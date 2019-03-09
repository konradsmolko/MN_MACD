import pandas as pd
import jupyter as jp

# Preparing the file
file = open("USDPLN_DAT.csv", "r")
df = pd.read_csv(file, sep=';')
del df["Volume"]
del df["OPEN"]
del df["HIGH"]
del df["LOW"]

# Reducing the time intervals to 1H
df["DateTime"] = pd.to_datetime(df["DateTime"])
# df.set_index('DateTime', inplace=True)
newIndex = df.index.floor('1H')
newDf = df.groupby(['DateTime']).mean()
finalDf = newDf.groupby('DateTime').mean()  # TODO

print(df)
