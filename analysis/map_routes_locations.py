
import pandas as pd
import numpy as np
import geopandas
from geodatasets import get_path
import plotly.express as px
import plotly.io as pio
pio.renderers.default = 'browser'

####################
# print some info
#####################
df = pd.read_excel("c://data//climbing//dataset_with_routes_location.xlsx")
print(f"We have {len(df.Route.unique())} routes in our dataset ...")
print(f"For {len(df[~df.latitude.isna()].Route.unique())} we know the exact location ...")
print(f"For {len(df[~df.inferred_country.isna()].Route.unique())} we know the country (including those for which we have the coordinates) ...")
print(f"For {len(df.Route.unique())- len(df[~df.inferred_country.isna()].Route.unique())} we don't have final info on position (but maybe a link to a website)")

df = df[~df.Route.duplicated()]
df.loc[df.inferred_country ==  'United Kingdom of Great Britain and Northern Ireland', 'inferred_country'] = "United Kingdom"
country_count = (df[['inferred_country', 'Route']].groupby('inferred_country').count().
                 reset_index().rename(columns = {'Route' : 'count'})).sort_values('count', ascending=False)
country_count['count_log'] = country_count['count'].map(np.log)

fig = px.bar(country_count,
    x="inferred_country",y="count",
    text="count", title="Number of routes per country",
    labels={"inferred_country": "Country", "count": "Count"},
    color="count", color_continuous_scale="Viridis_r")
fig.show()
fig.to_html("C:\\git-projects\\climbing-history\\plots\\routes_locations\\bar_chart_all_routes.html")

fig = px.choropleth(country_count,locations="inferred_country",
    locationmode="country names",color="count_log",
    color_continuous_scale="Viridis_r", title="Number of routes per country (log)")
fig.show()
fig.to_html("C:\\git-projects\\climbing-history\\plots\\routes_locations\\map_log_route_count.html")

#### maps for bouldering and lead
df[['style', 'work']] = df['Style'].str.split('|', expand=True)
df['style'] = df['style'].apply(lambda x: x.replace(" ", ""))

for style in ['Boulder', 'Lead']:
    df_style = df[df['style'] == style]
    style_count = (df_style[['inferred_country', 'Route']].groupby('inferred_country').count().
                     reset_index().rename(columns={'Route': 'count'})).sort_values('count', ascending=False)
    style_count['count_log'] = country_count['count'].map(np.log)

    fig = px.bar(style_count,
                 x="inferred_country", y="count",
                 text="count", title=f"Number of routes per country, {style}",
                 labels={"inferred_country": "Country", "count": "Count"},
                 color="count", color_continuous_scale="Viridis_r")
    fig.show()
    fig.to_html(f"C:\\git-projects\\climbing-history\\plots\\routes_locations\\bar_chart_{style}_routes.html")

    fig = px.choropleth(style_count, locations="inferred_country",
                        locationmode="country names", color="count_log",
                        color_continuous_scale="Viridis_r", title=f"Number of routes per country, {style} (log)")
    fig.show()
    fig.to_html(f"C:\\git-projects\\climbing-history\\plots\\routes_locations\\map_log_route_count_{style}.html")

######
# plot map
#####

gdf = geopandas.GeoDataFrame(df, geometry=geopandas.points_from_xy(df.longitude, df.latitude),
                             crs = 'EPSG:4326')

px.set_mapbox_access_token(open("C:\\Data\\geo\\mapbox_token.txt").read())
fig = px.scatter_geo(gdf,
                    lat=gdf.geometry.y,
                    lon=gdf.geometry.x,
                    hover_name="Route")
fig.update_geos(showcountries=True, visible=False, countrycolor = 'black')
fig.show()