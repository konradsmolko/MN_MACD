import pandas as pd
import jupyter as jp

file = open("USDPLN_DAT.csv", "r")
df = pd.read_csv(file, sep=';')
del df["Volume"]
del df["OPEN"]
del df["HIGH"]
del df["LOW"]
df["DateTime"] = pd.to_datetime(df["DateTime"])
df.set_index('DateTime', inplace=True)
df.index.floor('1H')

df.groupby(['DateTime']).mean()  # TODO

print(df)
