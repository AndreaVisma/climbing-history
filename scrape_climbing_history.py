import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import numpy as np
import dateparser
import re
from dateutil import parser

### first find all the links for the individual pages of each climb
# Base URL for the paginated pages
base_url = "https://climbing-history.org/climbs?page="

# Configure retries
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session = requests.Session()
session.mount('https://', HTTPAdapter(max_retries=retries))

# List to store all climb links
all_climb_links = []
all_grades = []

# Loop through pages 1 to 200 (after page 200 the climbs have zero ascents)
skipped_pages = []
skipped_urls = []
for page in tqdm(range(1, 230)):  # Adjust range as needed
    # Construct the URL for the current page
    url = base_url + str(page)

    try:
        response = session.get(url, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        skipped_urls.append(url)
        continue  # Skip to the next URL

    if response.status_code != 200:
        print(f"Failed to load page {page}")
        skipped_pages.append(page)
        continue  # Skip to the next page on error

    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the table
    table = soup.find('table')
    if not table:
        print(f"No table found on page {page}")
        skipped_pages.append(page)
        continue  # Skip if no table is found

    # Extract links from the first column
    rows = table.find_all('tr')
    for row in rows[1:]:  # Skip the header row
        first_cell = row.find('td')
        if first_cell and first_cell.find('a'): #check if there's a link
            row_text = row.get_text().lower()
            link = first_cell.find('a')['href']
            grade = row_text.split("\n")[3]
            all_climb_links.append(link)
            all_grades.append(grade)

# Print the total number of links found
print(f"Total links found: {len(all_climb_links)}")

# Save all links and grades files
with open('all_climb_links.txt', 'w', encoding='utf-8') as file:
    file.write("\n".join(all_climb_links))
with open('all_grades.txt', 'w', encoding='utf-8') as file:
    file.write("\n".join(all_grades))

## now scrape info from all of the individual pages
#base url for the website
base_url = "https://climbing-history.org"

with open('all_climb_links.txt', 'r', encoding='utf-8') as file:
    all_climb_links = file.read().splitlines()
with open('all_grades.txt', 'r', encoding='utf-8') as file:
    all_grades = file.read().splitlines()
dict_grades = dict(zip(all_climb_links, all_grades))

#now parse all the links to extract the data tables
skipped_urls = []
data = [] # place to concat all the data scraped

# Configure retries
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session = requests.Session()
session.mount('https://', HTTPAdapter(max_retries=retries))

for link in tqdm(all_climb_links):
    url = base_url + link #the climb page's url

    try:
        response = session.get(url, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        skipped_urls.append(url)
        continue  # Skip to the next URL

    # Parse the page with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the table containing climber data
    table = soup.find('table')  # Assuming data is in a <table> tag

    # Extract table rows
    try:
        rows = table.find_all('tr')
    except:
        print(f"No ascents logged for {url}")
        continue

    # Parse headers
    header = [th.text.strip() for th in rows[0].find_all('th')]

    # Parse data, excluding rows with "Reference"
    for row in rows[1:]:  # Skip the header row
        cells = [td.text.strip() for td in row.find_all('td')]
        if not any("Reference" in cell for cell in cells):  # Exclude rows with "Reference"
            cells.append(link)
            data.append(cells)

header = ['Climber', 'Style', 'Ascent Date', 'Suggested Grade', 'link']
# Create a DataFrame
df = pd.DataFrame(data, columns=header)
df = df.replace({None: np.nan})
df.dropna(inplace = True)

df['Route'] = df['link'].apply(lambda x: x.split("/")[-1])  # add climb name column by taking it from the link
df['Official grade'] = df.link.map(dict_grades)
df.Route = df.Route.apply(lambda x: " ".join(word.capitalize() for word in x.split("-")))

# Function to parse mixed date formats
def parse_date(entry):
    clean_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', entry)
    try:
        return parser.parse(clean_str, dayfirst=True)
    except Exception:
        return pd.NaT

# Apply the function to the 'dates' column
df['parsed_dates'] = df['Ascent Date'].apply(parse_date)

df.to_csv("c://data//climbing//climbing_history_all_02_05.csv", index = False)

# #################################
# df_old = pd.read_excel("c://data//climbing//dataset_with_routes_location.xlsx")[
#     ["Route", "longitude", "latitude", "inferred_country"]].drop_duplicates("Route")
# df_new = pd.read_csv("c://data//climbing//climbing_history_all_31_03.csv")
#
# df_new = df_new.merge(df_old, on = "Route", how = 'left')
# df_new.to_csv("c://data//climbing//climbing_history_all_31_03.csv", index = False)


