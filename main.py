import pandas as pd
import plotly as py
import plotly.graph_objs as go
# import multiprocessing as mp
# import timeit  # timeit.default_timer()


# Function for calculating EMA_n
def calculate_ema(data_frame: pd.DataFrame, n: int, today: int, column: str):
    if n <= 2:
        return 0

    if not isinstance(data_frame, pd.DataFrame):
        raise TypeError

    one_minus_alpha = 1 - (2 / (n - 1))
    """
    ema = (data[0] + data[i]*one_minus_alpha^i + ... + data[n]*one_minus_alpha^n)
    / (1 + one_minus_alpha^i + ... + one_minus_alpha^n)
    """
    apow = 1
    topdiv = data_frame.iloc[today][column]
    botdiv = 1
    for j in range(1, n):
        # apow = pow(one_minus_alpha, i)
        apow = apow * one_minus_alpha  # Should be less calculation intensive than pow()
        topdiv = topdiv + data_frame.iloc[today - j][column] * apow
        botdiv = botdiv + apow

    return topdiv / botdiv


"""
There's a little problem - the FOREX data is missing from each FRIDAY 16:59 to SUNDAY 17:00 (yeah, don't ask me)
making it cause to miss a day if we were to pick a specific hour, like 12:00 - every SATURDAY would be missing.
Solutions:
- Picking 16:59 on some days and 17:00 on others
    -- DONE by employing a tolerance selection with duplicate index removal
- Give up trying to fetch per-day data and process the per-minute data - extreme amounts of values and processing time.
    -- This could be minimized by multiprocessing the calculations.
"""

# Constants for fine tuning
MULTIPLIER = 1            # Multiplier for MACD and SIGNAL plots, for visibility reasons. Set to 1 to ignore.
FILENAME = 'DAT_ASCII_USDPLN_M1_'
COLS = ['DateTime Stamp', 'Bar OPEN Bid Quote', 'Bar LOW Bid Quote',
        'Bar HIGH Bid Quote', 'Bar CLOSE Bid Quote', 'Volume']
DATA_COLUMN = 'Bar CLOSE Bid Quote'
DATE_COLUMN = 'DateTime Stamp'
SEPARATOR = ';'

# Preparing the pd.DataFrame
li = []
all_files = []
for i in range(2015, 2019):
    all_files.append(FILENAME + str(i) + '.csv')

for filename in all_files:
    df = pd.read_csv(filename, sep=SEPARATOR, names=COLS)
    li.append(df)

source_df: pd.DataFrame = pd.concat(li, ignore_index=True)
source_df[DATE_COLUMN] = pd.to_datetime(source_df[DATE_COLUMN])
source_df.set_index(DATE_COLUMN, inplace=True)
del li, all_files

# Extracting a single value from each working day
ts = source_df.index.min().replace(hour=17, minute=00)
final_ts = source_df.index.max().replace(hour=17, minute=00)
delta = pd.Timedelta('1d')
indexes = pd.date_range(ts, final_ts)
formatted_df = source_df.reindex(index=indexes, method='nearest').drop_duplicates()
formatted_df.index = formatted_df.index.date
total_count = formatted_df.index.size
del delta, ts, final_ts, indexes, source_df

# Calculating MACD, EMA_12, EMA_26 - this takes about 42% of the entire program's processing time
# MACD = EMA_12 - EMA_26
macd = [0] * 26

# TODO: Multithread
for day in range(26, total_count):
    ema_12 = calculate_ema(formatted_df, 12, day, DATA_COLUMN)
    ema_26 = calculate_ema(formatted_df, 26, day, DATA_COLUMN)
    macd.append(ema_12 - ema_26)

for day in range(0, 26):
    ema = macd[26]
    macd[day] = ema

# Add MACD to formatted_df
formatted_df['MACD'] = pd.Series(macd, index=formatted_df.index)

# Calculating Signal
signal = [0] * 9
# TODO: Multithread
for day in range(9, total_count):
    ema = calculate_ema(formatted_df, 9, day, 'MACD')
    signal.append(ema)
for day in range(0, 9):
    ema = signal[26]
    signal[day] = ema

# Add SIGNAL to formatted_df
formatted_df['SIGNAL'] = pd.Series(signal, index=formatted_df.index)

# And this is where we enter the plotly part.
# Preparing and displaying the graph, MACD and SIGNAL * 100 for visibility against raw data
# TODO: Figure out how to get buy/sell triggers and display them on the graph
raw = go.Scatter(
    name='Kurs',
    x=formatted_df.index,
    y=formatted_df[DATA_COLUMN],
    legendgroup='Kurs'
)
macd = go.Scatter(
    name='MACD',
    x=formatted_df.index,
    y=formatted_df['MACD'] * MULTIPLIER,
    legendgroup='MACD'
)
signal = go.Scatter(
    name='SIGNAL',
    x=formatted_df.index,
    y=formatted_df['SIGNAL'] * MULTIPLIER,
    legendgroup='SIGNAL'
)
layout = dict(
    title="Kurs dolara amerykańskiego do złotówki w latach 2015-2018",
    xaxis=dict(
        type="category",
        title="Dzień"
    )
)
data_raw = dict(data=[raw], layout=layout)
data_macd = dict(data=[macd, signal], layout=layout)
data_mixed = dict(data=[macd, signal, raw], layout=layout)
# py.offline.plot(data_raw, filename='raw.html')
# py.offline.plot(data_macd, filename='macd.html')
py.offline.plot(data_mixed, filename='mixed.html')

# 50% of the project points is above this comment.

# TODO: Create a bot that will "trade" for the year using the triggers
