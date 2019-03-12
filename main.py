import pandas as pd
import plotly as py
import plotly.graph_objs as go
# import timeit # timeit.default_timer()

# Constants for fine tuning
MODE = 'OFFLINE'            # 'OFFLINE' or 'ONLINE'
MULTIPLIER = 1            # Multiplier for MACD and SIGNAL plots, for visibility reasons. Set to 1 to ignore.

if MODE == 'ONLINE':
    FILENAME = "https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv"
    DATA_COLUMN = 'AAPL.Close'
    DATE_COLUMN = 'Date'
    INTERVAL = 'none'
    SEPARATOR = ','
else:
    FILENAME = "DAT_ASCII_USDPLN_M1_2018.csv"
    DATA_COLUMN = 'Bar CLOSE Bid Quote'
    DATE_COLUMN = 'DateTime Stamp'
    INTERVAL = '6H'  # set to 'none' to disable interval grouping and rounding of values
    SEPARATOR = ';'


# Function for calculating EMA_n
def calculate_ema(df, n, today, column):
    if n <= 2:
        return 0

    if not isinstance(df, pd.DataFrame):
        raise TypeError

    one_minus_alpha = 1 - (2 / (n - 1))
    """
    ema = (data[0] + data[i]*one_minus_alpha^i + ... + data[n]*one_minus_alpha^n)
    / (1 + one_minus_alpha^i + ... + one_minus_alpha^n)
    """
    apow = 1
    topdiv = df.iloc[today][column]
    botdiv = 1
    for i in range(1, n):
        # apow = pow(one_minus_alpha, i)
        apow = apow * one_minus_alpha  # Should be less calculation intensive than pow()
        topdiv = topdiv + df.iloc[today - i][column] * apow
        botdiv = botdiv + apow

    return topdiv / botdiv


# Preparing the file
sourceDF = pd.read_csv(FILENAME, sep=SEPARATOR)
sourceDF[DATE_COLUMN] = pd.to_datetime(sourceDF[DATE_COLUMN])
sourceDF.set_index(DATE_COLUMN, inplace=True)

# Reducing the time intervals to INTERVAL with averaging the values
if INTERVAL != 'none':
    sourceDF = sourceDF.groupby(sourceDF.index.floor(INTERVAL)).mean()

totalCount = sourceDF.count()[DATA_COLUMN]

# Calculating MACD, EMA_12, EMA_26
# MACD = EMA_12 - EMA_26
macd = [0] * 26
ema_12 = [0] * 26
ema_26 = [0] * 26

for day in range(26, totalCount):
    ema_12_ = calculate_ema(sourceDF, 12, day, DATA_COLUMN)
    ema_26_ = calculate_ema(sourceDF, 26, day, DATA_COLUMN)
    macd.append(ema_12_ - ema_26_)
    ema_12.append(ema_12_)
    ema_26.append(ema_26_)

for day in range(0, 26):
    ema = macd[26]
    macd[day] = ema
    ema_12[day] = ema
    ema_26[day] = ema

# Add EMA12, EMA26, MACD to sourceDF
sourceDF['EMA_12'] = pd.Series(ema_12, index=sourceDF.index)
sourceDF['EMA_26'] = pd.Series(ema_26, index=sourceDF.index)
sourceDF['MACD'] = pd.Series(macd, index=sourceDF.index)

# Calculating Signal
signal = []
for day in range(9, totalCount):
    ema = calculate_ema(sourceDF, 9, day, 'MACD')
    signal.append(ema)
for day in range(0, 9):
    ema = signal[26]
    signal.append(ema)

sourceDF['SIGNAL'] = pd.Series(signal, index=sourceDF.index)

# And this is where we enter the plotly part.
# Preparing and displaying the graph, MACD and SIGNAL * 100 for visibility against raw data
raw = go.Scatter(
    name='RAW VALUE',
    x=sourceDF.index,
    y=sourceDF[DATA_COLUMN]
)
macd = go.Scatter(
    name='MACD',
    x=sourceDF.index,
    y=sourceDF['MACD'] * MULTIPLIER
)
signal = go.Scatter(
    name='SIGNAL',
    x=sourceDF.index,
    y=sourceDF['SIGNAL'] * MULTIPLIER
)
data_raw = [raw]
data_macd = [macd, signal]
data_mixed = [macd, signal, raw]
py.offline.plot(data_raw, filename='raw.html')
py.offline.plot(data_macd, filename='macd.html')
# py.offline.plot(data_mixed, filename='mixed.html')

# 50% of the project points is all above this comment.

# TODO: Figure out how to get buy/sell triggers and display them on the graph

# TODO: Create a bot that will "trade" for the year using the triggers

# TODO: Ustalić próbkowanie np. 12 każdego dnia
# TODO: Dane z kilku lat żeby dostać 1000 próbek?

