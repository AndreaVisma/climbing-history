
import time
from tqdm import tqdm
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

with open('C:\\Data\\climbing\\bouldering_wc_links_201519.txt', 'r', encoding='utf-8') as file:
    all_comp_links = file.read().splitlines()

# Set up Firefox options
options = Options()
options.add_argument("--headless")  # Comment this line if you want to see the browser

# Set up the Firefox driver
service = Service(GeckoDriverManager().install())
driver = webdriver.Firefox(service=service, options=options)

def get_content_page(url):
    # Load the page
    driver.get(url)

    # Explicit wait: wait until a dynamic element appears (adjust selector accordingly)
    wait = WebDriverWait(driver, 30)  # Wait up to 30 seconds
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "r-name")))

    # Extract the updated page source after JS execution
    content = driver.page_source
    return content

def parse_ifsc_results(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Extract event, discipline, and round
    event_name = soup.find('div', class_='event-name').text.strip()
    discipline = soup.find_all('div', class_='dcat-row')[1].text.strip()
    round_name = soup.find('div', class_='round-name').text.strip()

    table = soup.find('table')
    rows = table.find_all('tr')

    data = []
    current_athlete = {}

    for row in rows:
        if 'r-row' in row.get('class', []):
            # Extract athlete information
            current_athlete = {}
            current_athlete['athlete'] = row.find('a', class_='r-name').get_text(strip=True)
            country = row.find('div', class_ = "r-name-sub").get_text().split(' • ')[-1]
            current_athlete['country'] = country
            current_athlete['event'] = event_name
            current_athlete['round'] = round_name
            current_athlete['discipline'] = discipline

        elif 'boulder-asc-detail' in row.get('class', []):
            # Extract boulder details
            boulders = row.find_all('div', class_='asc-cell-container')
            for boulder in boulders:
                boulder_data = current_athlete.copy()

                # Get boulder identifier
                boulder_num = boulder.find('div', class_='asc-route-name').get_text(strip=True)
                boulder_data['boulder'] = f"{event_name}-{round_name}-{boulder_num}"

                # Get attempts
                cell = boulder.find('div', class_='asc-cell')
                top = cell.find('div', class_='top')
                zone = cell.find('div', class_='zone')

                boulder_data['top'] = top.find('span').get_text(strip=True) if 'topped' in top.get('class',
                                                                                                   []) else None
                boulder_data['zone'] = zone.find('span').get_text(strip=True) if 'zoned' in zone.get('class',
                                                                                                     []) else None

                data.append(boulder_data)

    # Create DataFrame with specified column order
    df = pd.DataFrame(data)
    if not df.empty:
        # Convert numeric columns
        df['top'] = pd.to_numeric(df['top'], errors='coerce')
        df['zone'] = pd.to_numeric(df['zone'], errors='coerce')
        # Reorder columns
        df = df[['athlete', 'country', 'boulder', 'zone', 'top', 'event', 'round', 'discipline']]

    # Create DataFrame
    df = pd.DataFrame(data)
    return df

df_all_results = pd.DataFrame([])
failed_links = []
for link in tqdm(all_comp_links):
    try:
        df = parse_ifsc_results(get_content_page(link))
        df_all_results = pd.concat([df_all_results, df])
    except:
        print(f"Something failed for link: {link}")
        failed_links.append(link)

df_all_results.to_csv('C:\\Data\\climbing\\bouldering_Worldcups_2021_to_2024.csv', index = False)

driver.quit()
