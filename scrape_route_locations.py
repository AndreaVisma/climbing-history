import requests
import numpy as np
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from urllib.request import Request, urlopen
import numpy as np
import dateparser
import re
import geopandas
from geodatasets import get_path
import plotly.express as px
import plotly.io as pio
pio.renderers.default = 'browser'
from geopy.geocoders import Nominatim

#base url for the website
base_url = "https://climbing-history.org"

with open('all_climb_links.txt', 'r', encoding='utf-8') as file:
    all_climb_links = file.read().splitlines()
with open('all_grades.txt', 'r', encoding='utf-8') as file:
    all_grades = file.read().splitlines()
dict_grades = dict(zip(all_climb_links, all_grades))

#now parse all the links to extract the data tables
skipped_urls = []
skipped_crag_links = []
data_x = []
data_y = []
succesful_links = []

# Configure retries
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session = requests.Session()
session.mount('https://', HTTPAdapter(max_retries=retries))

for link in tqdm(all_climb_links):
    target_name = link.split('/')[-1].split('-')[0].capitalize()
    pattern = re.sub(r"([a-zA-Z])(['’]?)", r"\1['’]?", target_name)
    url = base_url + link #the climb page's url

    try:
        response = session.get(url, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        skipped_urls.append(url)
        continue  # Skip to the next URL

    # Parse the page with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Try to get the link to the crag
    try:
        span = [span for span in soup.find_all("span") if re.match(f"^{pattern}", span.get_text(strip=True), re.IGNORECASE)][0]
    except:
        print(f"Error getting title for {link}")
        skipped_urls.append(url)
        continue  # Skip to the next URL
    text = span.get_text(strip=True)
    crag_link = span.find("a")
    if crag_link:
        crag_link = "https://climbing-history.org" + crag_link["href"]
        try:
            response_crag = session.get(crag_link, timeout=10)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {crag_link}: {e}")
            skipped_crag_links.append(crag_link)
            continue  # Skip to the next URL
        soup = BeautifulSoup(response_crag.text, 'html.parser')
        try:
            map_script = [script.string for script in soup.find_all("script") if script.string and "L.map" in script.string][0]
            marker_pattern = re.search(r"L\.marker\(\[(\-?\d+\.\d+),\s*(\-?\d+\.\d+)\]\)", map_script)
            marker_coords = (float(marker_pattern.group(1)), float(marker_pattern.group(2))) if marker_pattern else None
            marker_x, marker_y = marker_coords[0], marker_coords[1]
            data_x.append(marker_x)
            data_y.append(marker_y)
            succesful_links.append(link)
        except:
            print(f"couldn't find map for {crag_link}")
            skipped_crag_links.append(crag_link)
            continue

# Create a DataFrame
df = pd.DataFrame(
    {'link' : succesful_links, 'longitude' : data_y, 'latitude': data_x}
)
df['Route'] = df['link'].apply(lambda x: x.split("/")[-1])
df.Route = df.Route.apply(lambda x: " ".join(word.capitalize() for word in x.split("-")))

df_routes = pd.read_excel("c://data//climbing//climbing_history_all_cleanish.xlsx")
df_comp = df_routes.merge(df, on = ['link', 'Route'], how = 'left')
df_comp.to_excel("c://data//climbing//dataset_with_routes_location.xlsx", index = False)

print(df_comp[~df_comp.Route.duplicated()].isna().sum())
missing_links = df_comp[(~df_comp.Route.duplicated()) & (df_comp.latitude.isna())]['link_x'].tolist()
with open('links_for_which_i_couldnt_scrape_location.txt', 'w', encoding='utf-8') as file:
    file.write("\n".join(missing_links))

###########
# try to find the missing locations
###########

# iteration 1
succesful_links = []
crag_names = []
further_links = []
location = []
no_info_links = []

for link in tqdm(missing_links):
    target_name = link.split('/')[-1].split('-')[0].capitalize()
    pattern = re.sub(r"([a-zA-Z])(['’]?)", r"\1['’]?", target_name)
    url = base_url + link

    try:
        response = session.get(url, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        skipped_urls.append(url)
        continue  # Skip to the next URL

    # Parse the page with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Try to get the link to the crag
    try:
        span = [span for span in soup.find_all("span") if re.match(f"^{pattern}", span.get_text(strip=True), re.IGNORECASE)][0]
    except:
        print(f"Error getting title for {link}")
        skipped_urls.append(url)
        continue  # Skip to the next URL
    text = span.get_text(strip=True)
    crag_link = span.find("a")
    if not crag_link: ## there's no link in the page title
        try: # try to go to 8a.nu
            nu_link = soup.find("a", {'class': 'text-break text-muted small'}).get('href')
            further_links.append(nu_link)
            succesful_links.append(link)
            crag_names.append("")
            location.append("")
            continue
        except:
            print(f"couldn't find link for {url}, nor its says location")
            no_info_links.append(link)
            continue
    else:
        crag_link = "https://climbing-history.org" + crag_link["href"]
        try:
            response_crag = session.get(crag_link, timeout=10)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {crag_link}: {e}")
            skipped_crag_links.append(crag_link)
            continue  # Skip to the next URL
        soup = BeautifulSoup(response_crag.text, 'html.parser')
        crag_name = soup.find("title").get_text(strip=True)
        try:
            map_script = [script.string for script in soup.find_all("script") if script.string and "L.map" in script.string][0]
            marker_pattern = re.search(r"L\.marker\(\[(\-?\d+\.\d+),\s*(\-?\d+\.\d+)\]\)", map_script)
            marker_coords = (float(marker_pattern.group(1)), float(marker_pattern.group(2))) if marker_pattern else None
            further_links.append("")
            succesful_links.append(link)
            crag_names.append(crag_name)
            location.append(marker_coords)
        except:
            print(f"couldn't find map for {crag_link}")
            try:  # try to go to climbinguk
                cluk_link = soup.find("a", {'class': 'text-break text-muted small'}).get('href') + "/#maps"
                try:
                    response_crag = session.get(cluk_link, timeout=10)
                    soup = BeautifulSoup(response_crag.text, 'html.parser')
                    latitude = soup.find("meta", {'property' : 'place:location:latitude'}).get('content')
                    longitude = soup.find("meta", {'property': 'place:location:longitude'}).get('content')
                    coords = [latitude, longitude]
                    further_links.append(cluk_link)
                    succesful_links.append(link)
                    crag_names.append(crag_name)
                    location.append(coords)
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching {crag_link}: {e}")
                    further_links.append(cluk_link)
                    succesful_links.append(link)
                    crag_names.append(crag_name)
                    location.append("")
                    continue  # Skip to the next URL
            except:
                continue

df_missing = pd.DataFrame({'link' : succesful_links,
    'crag_name' : crag_names,
    'further_link' : further_links,
    'location' : location})
df_missing.loc[df_missing.location != '','latitude'] = df_missing.loc[df_missing.location != '','location'].apply(lambda x: float(x[0]))
df_missing.loc[df_missing.location != '','longitude'] = df_missing.loc[df_missing.location != '','location'].apply(lambda x: float(x[1]))

df_missing[df_missing.latitude.isna()].to_excel("c://data//climbing//links_for_missing_routes.xlsx", index = False)

## add the places for which we could get a location
df = pd.read_excel("c://data//climbing//dataset_with_routes_location.xlsx")

df_comp = df.merge(df_missing[['link', 'latitude', 'longitude']], on = 'link', how = 'left')
df_comp.loc[df_comp.latitude_x.isna(), 'latitude_x'] = df_comp.loc[df_comp.latitude_x.isna(), 'latitude_y']
df_comp.loc[df_comp.latitude_x.isna(), 'longitude_x'] = df_comp.loc[df_comp.latitude_x.isna(), 'longitude_y']
df_comp.rename(columns = {'latitude_x' : 'latitude', 'longitude_x' : 'longitude'}, inplace = True)
df_comp.drop(columns = {'latitude_y', 'longitude_y'}, inplace = True)
df_comp.to_excel("c://data//climbing//dataset_with_routes_location.xlsx", index = False)


### try scrping the rest of the nu8 links

nu_links = [x for x in df_missing.further_link.tolist() if '8a.nu' in x]
no_success = []
titles = []

for link in tqdm(nu_links):
    try:
        req = Request(
            url=link,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        soup = BeautifulSoup(urlopen(req).read(), 'html.parser')
        title = soup.find("title").get_text()
        titles.append(title)
    except:
        titles.append("")
        no_success.append(link)

df_nu = pd.DataFrame({'further_link' : nu_links, 'title' : titles})
df_missing = df_missing.merge(df_nu, on = 'further_link', how = 'left')
df_missing.loc[df_missing.title != "", 'inferred_country'] = (
    df_missing.loc[(~df_missing.title.isna()) & (df_missing.title != ""), 'title']
    .apply(lambda x: x.split(',')[1].split('-')[0].strip()))

df = df.merge(df_missing[['link', 'further_link', 'inferred_country', 'title']], on = 'link', how = 'left')

import geopandas
gdf = geopandas.GeoDataFrame(df, geometry=geopandas.points_from_xy(df.longitude, df.latitude),
                             crs = 'EPSG:4326')
gdf = gdf[(~gdf.latitude.isna()) & (~gdf.Route.duplicated())]
world = geopandas.read_file("C:\\Data\\geo\\admin_0\\ne_110m_admin_0_countries.shp")

gdf = gdf.sjoin(world[['ADMIN', 'geometry']], how = 'left')
gdf = gdf[gdf['ADMIN'] != ""]
dict_routes_countries = dict(zip(gdf.Route.tolist(), gdf.ADMIN.tolist()))

df.loc[df.Route.isin(dict_routes_countries.keys()), 'inferred_country'] = (
    df.loc[df.Route.isin(dict_routes_countries.keys()), 'Route'].map(dict_routes_countries))

df.to_excel("c://data//climbing//dataset_with_routes_location.xlsx", index = False)
