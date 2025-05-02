
import pandas as pd

df = pd.read_csv("c://data//climbing//climbing_history_all_02_05.csv", parse_dates=['parsed_dates'])

df_with_loc = pd.read_excel("c://data//climbing//dataset_with_routes_location.xlsx")

cols_to_add = list(set(df_with_loc.columns) - set(df.columns))

df_with_loc = df_with_loc[~df_with_loc.Route.duplicated()][cols_to_add + ["Route"]]

df = df.merge(df_with_loc, on = "Route", how = 'left')

df.to_csv("c://data//climbing//climbing_history_all_02_05.csv", index = False)