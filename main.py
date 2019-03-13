from typing import List

import pandas as pd
import plotly as py
import plotly.graph_objs as go
# import multiprocessing as mp
# import timeit  # timeit.default_timer()

"""
There's a little problem - the FOREX data is missing from each FRIDAY 16:59 to SUNDAY 17:00 (yeah, don't ask me)
making it cause to miss a day if we were to pick a specific hour, like 12:00 - every SATURDAY would be missing.
Solutions:
- Picking 16:59 on some days and 17:00 on others
    -- DONE by using nearest value selection with duplicate index removal
- Give up trying to fetch per-day data and process the per-minute data - extreme amounts of values and processing time.
    -- This could be minimized by multiprocessing the calculations.
"""

# Constants for fine tuning
FILENAME = 'DAT_ASCII_USDPLN_M1_'
COLS = ['DateTime Stamp', 'Bar OPEN Bid Quote', 'Bar LOW Bid Quote',
        'Bar HIGH Bid Quote', 'Bar CLOSE Bid Quote', 'Volume']
DATA_COLUMN = 'Bar CLOSE Bid Quote'
DATE_COLUMN = 'DateTime Stamp'
SEPARATOR = ';'


# Function for calculating EMA_n
def calculate_ema(data_frame: pd.DataFrame, n: int, today: int, column: str) -> float:
    if n <= 2:
        return 0

    if not isinstance(data_frame, pd.DataFrame):
        raise TypeError

    """
    ema = (data[0] + data[i]*one_minus_alpha^i + ... + data[n]*one_minus_alpha^n)
    / (1 + one_minus_alpha^i + ... + one_minus_alpha^n)
    """
    one_minus_alpha = 1 - (2 / (n - 1))
    apow = 1.0
    topdiv = data_frame.iloc[today][column]
    botdiv = 1.0
    for j in range(1, n):
        # apow = pow(one_minus_alpha, i)
        apow = apow * one_minus_alpha  # Should be less calculation intensive than pow()
        topdiv += data_frame.iloc[today - j][column] * apow
        botdiv += apow

    return topdiv / botdiv


def main():
    # Preparing the pd.DataFrame
    li = []
    all_files = []

    for i in range(2015, 2019):
        all_files.append(FILENAME + str(i) + '.csv')
    for file in all_files:
        df = pd.read_csv(file, sep=SEPARATOR, names=COLS)
        li.append(df)

    source_df: pd.DataFrame = pd.concat(li, ignore_index=True)
    source_df[DATE_COLUMN] = pd.to_datetime(source_df[DATE_COLUMN])
    source_df.set_index(DATE_COLUMN, inplace=True)
    del li, all_files

    # Extracting a single value from each working day
    ts = source_df.index.min().replace(hour=17, minute=00)
    final_ts = source_df.index.max().replace(hour=17, minute=00)
    indexes = pd.date_range(ts, final_ts, freq='D')
    formatted_df: pd.DataFrame = source_df.reindex(index=indexes, method='nearest').drop_duplicates()
    formatted_df.index = formatted_df.index.date
    total_count = formatted_df.index.size
    del ts, final_ts, indexes, source_df

    # Calculating MACD, EMA_12, EMA_26 - this takes about 42% of the entire program's processing time
    # MACD = EMA_12 - EMA_26
    macd: List[float] = [None] * total_count

    # TODO: Multithread
    for day in range(26, total_count):
        ema_12 = calculate_ema(formatted_df, 12, day, DATA_COLUMN)
        ema_26 = calculate_ema(formatted_df, 26, day, DATA_COLUMN)
        macd[day] = ema_12 - ema_26

    for day in range(0, 26):
        ema = macd[26]
        macd[day] = ema

    # Add MACD to formatted_df
    formatted_df['MACD'] = pd.Series(macd, index=formatted_df.index)

    # Calculating Signal
    signal: List[float] = [None] * total_count
    # TODO: Multithread
    for day in range(9, total_count):
        ema = calculate_ema(formatted_df, 9, day, 'MACD')
        signal[day] = ema
    for day in range(0, 9):
        ema = signal[26]
        signal[day] = ema

    # Add SIGNAL to formatted_df
    formatted_df['SIGNAL'] = pd.Series(signal, index=formatted_df.index)

    # TODO: Get x/y values for buy/sell markers
    previous = False
    markers_buy = []
    markers_sell = []
    for row in formatted_df.iterrows():
        if row[1]['MACD'] > row[1]['SIGNAL'] and previous is False:
            markers_buy.append(row[1][DATA_COLUMN])
            markers_sell.append(None)
            previous = True
        elif row[1]['MACD'] < row[1]['SIGNAL'] and previous is True:
            markers_sell.append(row[1][DATA_COLUMN])
            markers_buy.append(None)
            previous = False
        else:
            markers_buy.append(None)
            markers_sell.append(None)

    # And this is where we enter the plotly part.
    # Preparing and displaying the graph, MACD and SIGNAL * 100 for visibility against raw data
    raw = go.Scatter(
        name='Kurs',
        x=formatted_df.index,
        y=formatted_df[DATA_COLUMN],
        legendgroup='Kurs'
    )
    # Used to align the MACD and SIGNAL charts to the DATA chart for clarity
    avg = ((formatted_df.max() + formatted_df.min()) / 2)[DATA_COLUMN]
    macd = go.Scatter(
        name='MACD',
        x=formatted_df.index,
        y=formatted_df['MACD'] + avg,
        legendgroup='MACD'
    )
    signal = go.Scatter(
        name='SIGNAL',
        x=formatted_df.index,
        y=formatted_df['SIGNAL'] + avg,
        legendgroup='SIGNAL')
    buy = go.Scatter(
        name='BUY',
        x=formatted_df.index,
        y=markers_buy,
        mode='markers',
        marker=dict(
            size=20,
            color='rgb(0,255,0)'))
    sell = go.Scatter(
        name='SELL',
        x=formatted_df.index,
        y=markers_sell,
        mode='markers',
        marker=dict(
            size=20,
            color='rgb(255,0,0)'))
    layout = dict(
        title="Kurs dolara amerykańskiego do złotówki w latach 2015-2018",
        xaxis=dict(
            type="category",
            title="Dzień"))
    # data = dict(data=[macd, signal, raw], layout=layout)
    data = dict(data=[macd, signal, raw, buy, sell], layout=layout)
    py.offline.plot(data, filename='graph.html')

    # 50% of the project points is above this comment.

    # TODO: Create a bot that will "trade" for the year using the triggers


main()
