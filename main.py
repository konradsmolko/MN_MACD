import pandas as pd
import jupyter as jp

# Constants for fine tuning
FILENAME = "USDPLN_DAT.csv"
INTERVAL = '6H'

# Preparing the file
sourceDF = pd.read_csv(FILENAME, sep=';')
del sourceDF["Volume"]
del sourceDF["OPEN"]
del sourceDF["HIGH"]
del sourceDF["LOW"]
sourceDF["DateTime"] = pd.to_datetime(sourceDF["DateTime"])
sourceDF.set_index('DateTime', inplace=True)

# Reducing the time intervals to 6H with averaging the values in each hour, for a total of 1092 entries
sourceDF = sourceDF.groupby(sourceDF.index.floor(INTERVAL)).mean()
totalCount = sourceDF.count()['CLOSE']

# TODO: Calculate EMA
# MACD = EMA_12 - EMA_26
ema = []
for day in range(0, 26):
    # ema.append()
    pass
for day in range(26, totalCount):
    print(day)

# TODO: Calculate MACD

# TODO: Calculate Signal

# TODO: Add EMA, MACD, Signal to sourceDF and display Signal and MACD on the same graph
sourceDF['EMA12'] = 0
sourceDF['EMA26'] = 0
sourceDF['MACD'] = 0
sourceDF['SIGNAL'] = 0

# TODO: Figure out how to get buy/sell triggers and display them on the graph

# TODO: Create a bot that will "trade" for the year using the triggers


def calculate_ema(data, n):
    if n <= 1:
        return 0

    one_minus_alpha = 1 - (2 / (n - 1))
    # ema = (data[0] + data[i]*one_minus_alpha^i + ... + data[n]*one_minus_alpha^n)
    # / (1 + one_minus_alpha^1 + ... + one_minus_alpha^n)
    topdiv = 0
    botdiv = 0
    for i in range(n):
        apow = pow(one_minus_alpha, i)
        topdiv = topdiv + data[i]*apow
        botdiv = botdiv + apow

    return topdiv / botdiv
