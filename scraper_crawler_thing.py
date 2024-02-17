import time
import logging
from pathlib import Path
from datetime import datetime

import requests

from sqlalchemy import insert, select
from selenium.webdriver.common.by import By

from sql_stuff.models import Hatarozat
from sql_stuff.database import Session

from slugify import slugify

from selenium_stuff.selenium_utils import process_combinations_gen
from selenium_stuff.selenium_base import create_driver
from form_options_extraction import extract_form_options
from utils import get_form_option_and_date_combinations

SAVE_DIRECTORY = './data/texts'
SAVE_DIRECTORY_PATH = Path(SAVE_DIRECTORY)

# logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
# logger.setLevel(logging.WARNING)  # or any variant from ERROR, CRITICAL or NOTSET
logging.basicConfig(filename=f'logs/{datetime.today().isoformat()}.log', level=logging.DEBUG)


# TODO problem : RUNNING SEARCH COMBINATION: {'year': 2020, 'hatarozat_fajtaja': 'Végzés', 'kollegium': 'közigazgatási'}


def run_crawler(year_start, existing_azonosito_set):

    driver, kereses_button = set_up_page()

    form_options = extract_form_options(driver)
    form_combinations = get_form_option_and_date_combinations(form_options, year_start=year_start)

    hatarozat_data = process_combinations_gen(form_combinations, driver, kereses_button, existing_azonosito_set)

    return hatarozat_data


def main(year_start):

    # Saved Hatarozat sorszam from SQL
    with Session() as session:
        existing_azonosito_list = [s[0] for s in session.execute(select(Hatarozat.egyedi_azonosito))]
        existing_azonosito_set = set(existing_azonosito_list)

    hatarozat_data = run_crawler(year_start, existing_azonosito_set)

    # Extract rows data
    insert_rows_hatarozat = []
    for rows in hatarozat_data:
        if len(rows) > 0:
            for row in rows:
                # Base values
                hatarozat_vals = {k: v for k, v in row.items() if k in hatarozat_cols}
                # URL
                hatarozat_vals['url'] = 'https://eakta.birosag.hu/anonimizalt-hatarozatok?azonosito=' \
                                        + hatarozat_vals['sorszam']
                # # Year
                # hatarozat_vals['year'] = year

                filename = download_hatarozat(hatarozat_vals)
                hatarozat_vals['filename'] = filename

                insert_rows_hatarozat.append(hatarozat_vals)
                existing_azonosito_set.add(row['egyedi_azonosito'])

    return insert_rows_hatarozat


    # form_combinations = [{'year': 2024, 'hatarozat_fajtaja': 'Végzés', 'kollegium': 'polgári'}]
    for insert_rows_hatarozat in hatarozat_data:
        if len(insert_rows_hatarozat) > 0:
            print(f'INSERTING {len(insert_rows_hatarozat)} HATAROZAT')
            logging.info(f'INSERTING {len(insert_rows_hatarozat)} HATAROZAT')
            with Session() as session:
                session.execute(
                    insert(Hatarozat),
                    insert_rows_hatarozat
                )
                session.commit()

    logging.info('FINISHED CRAWL :)')


def set_up_page():
    driver = create_driver()
    driver.get("https://eakta.birosag.hu/anonimizalt-hatarozatok")
    driver.implicitly_wait(2)
    # driver.execute_script("document.body.style.zoom = '50%'")
    driver.maximize_window()
    time.sleep(2)

    # Keresés gomb
    kereses_button = driver.find_element(by=By.XPATH, value='//button[@class="filter-button custom-button float-left"]')

    # Tobb szűrő megjelenítése
    tobb_szuro_button = driver.find_element(by=By.XPATH, value='//button[@class="custom-button white collapse-button"]')
    tobb_szuro_button.click()

    return driver, kereses_button


def download_hatarozat(hatarozat_vals):
    download_url = hatarozat_vals.pop('download_url', None)
    if download_url is None:
        raise ValueError(f'No download_url retrieved for {hatarozat_vals}')

    dl_resp = None
    for i in range(3):
        try:
            dl_resp = requests.get(download_url, None)
        except requests.exceptions.ConnectTimeout:
            time.sleep(5)
            continue
    if dl_resp is None or dl_resp.status_code != 200:
        raise ValueError(f'Could not download file {hatarozat_vals["download_url"]}')
    else:
        extension = dl_resp.headers['Content-Disposition'].rstrip('"').split('.')[-1]
        filename = f'{slugify(hatarozat_vals["egyedi_azonosito"])}.{extension}'
        with open(SAVE_DIRECTORY_PATH / filename, 'wb') as fh:
            fh.write(dl_resp.content)
    return filename


if __name__ == '__main__':
    run_crawler(2024)
