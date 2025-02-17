
import pandas as pd
import geopandas
from geodatasets import get_path
import plotly.express as px
import plotly.io as pio
pio.renderers.default = 'browser'

df = pd.read_excel("c://data//climbing//dataset_with_routes_location.xlsx")
gdf = geopandas.GeoDataFrame(df, geometry=geopandas.points_from_xy(df.longitude, df.latitude),
                             crs = 'EPSG:4326')

px.set_mapbox_access_token(open("C:\\Data\\geo\\mapbox_token.txt").read())
fig = px.scatter_geo(gdf,
                    lat=gdf.geometry.y,
                    lon=gdf.geometry.x,
                    hover_name="Route")
fig.update_geos(showcountries=True, visible=False, countrycolor = 'black')
fig.show()