import time
from itertools import combinations, islice

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from sqlalchemy import insert, select

from selenium_base import create_driver
from results_extraction import get_rows
from form_options_extraction import extract_form_options, form_xpaths
from utils import get_form_option_and_date_combinations, simple_find_or_none

from sql_stuff.database import Session
from sql_stuff.models import Hatarozat, kapcsolodo_hatarozatok_table

scroll_into_view_js_code = "arguments[0].scrollIntoView();"

form_options_year = {
    'from': {'xpath': '//span[@id="select2-MeghozatalIdejeTol-container"]'},
    'to': {'xpath': '//span[@id="select2-MeghozatalIdejeIg-container"]'}
}

oldalmeret_dropdown_xpath = '//span[@id="select2-page-size-container"]'
oldalmeret_100_option_xpath = '//li[contains(text(), "100")]'

next_page_enabled_button_xpath = '//button[@class="grid-pager btn btn-default grid-pager-next"]'
next_page_disabled_button_xpath = '//button[@class="grid-pager btn btn-default grid-pager-next disabled"]'

hatarozat_cols = {'sorszam', 'birosag', 'kollegium', 'jogterulet', 'year', 'egyedi_azonosito', 'jogszabalyhelyek',
                  'elvi_tartalma', 'kapcsolodo_hatarozatok'}


def main(year_start=2022):

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

    form_options = extract_form_options(driver)
    form_combinations = get_form_option_and_date_combinations(form_options, year_start=year_start)

    # Saved hatarozatok
    with Session() as session:
        existing_hatarozat_sorszam = [s for s in session.execute(select(Hatarozat.sorszam))]
        existing_hatarozat_sorszam = set(existing_hatarozat_sorszam)

    # Kapcsolodo hatarozatok save
    kapcsolodo_hatarozatok_pairs = set()

    for combination in form_combinations:
        print(f'RUNNING SEARCH COMBINATION: {combination}')
        time.sleep(1)
        year = combination.pop('year')

        for form_option, form_value in combination.items():
            # Select form option
            form_value_option_xpath = f'//ul[@class="select2-results__options"]/li[contains(text(), "{form_value}")]'
            dropdown = driver.find_element(by=By.XPATH, value=form_xpaths[form_option]['xpath'])
            ActionChains(driver).move_to_element(dropdown).perform()

            # driver.execute_script(scroll_into_view_js_code, dropdown)  # scroll into view
            time.sleep(1)
            # dropdown = driver.find_element(by=By.XPATH, value=form_xpaths[form_option]['xpath'])
            dropdown_select_by_text(driver, dropdown, form_value_option_xpath)


        # Select year
        date_to_and_from_option_xpath = f'//ul[@class="select2-results__options"]/li[contains(text(), "{year}")]'

        # From year
        scroll_to_form(driver)
        from_dropdown = driver.find_element(by=By.XPATH, value=form_options_year['from']['xpath'])
        dropdown_select_by_text(driver, from_dropdown, date_to_and_from_option_xpath, scroll_for_date=True)

        # To year
        to_dropdown = driver.find_element(by=By.XPATH, value=form_options_year['to']['xpath'])
        dropdown_select_by_text(driver, to_dropdown, date_to_and_from_option_xpath, scroll_for_date=True)


        kereses_button.click()
        time.sleep(2)
        # Make sure results are not truncated.
        number_of_results = driver.find_element(by=By.XPATH,
                                                value='//div[@class="table-data main-content"]/div[@class="count-wrappe'
                                                      'r"]/span[@class="listCountHolder"]').text.strip()
        if number_of_results == '10000+':
            raise NotImplementedError('Too many results, cannot be certain of parsing all results!')
        elif number_of_results == '0':
            continue

        # Set pagination page size to 100
        driver.find_element(by=By.XPATH, value=oldalmeret_dropdown_xpath).click()
        driver.find_element(by=By.XPATH, value=oldalmeret_100_option_xpath).click()

        # Extract rows data
        insert_rows_hatarozat = []
        for res in collect_page_rows_and_go_to_next(driver):
            # Check if saved
            if res['sorszam'] not in existing_hatarozat_sorszam:
                existing_hatarozat_sorszam.add(res['sorszam'])  # dirty fix
                # Base values
                hatarozat_vals = {k: v for k, v in res.items() if k in hatarozat_cols}
                # URL
                hatarozat_vals['url'] = "https://eakta.birosag.hu/anonimizalt-hatarozatok?azonosito="+hatarozat_vals['sorszam']
                # Year
                hatarozat_vals['year'] = year

                # Kapcsolodo hatarozatok
                kapcsolodo_hatarozatok = res.pop('kapcsolodo_hatarozatok', [])  # TODO can this be none?
                if len(kapcsolodo_hatarozatok) > 0:
                    kapcsolodo_hatarozatok.append(res['sorszam'])
                    for pair in combinations(kapcsolodo_hatarozatok, 2):
                        kapcsolodo_hatarozatok_pairs.add(tuple(sorted(pair)))

                insert_rows_hatarozat.append(hatarozat_vals)
            else:
                print(f'Sorszám duplicate: ', res['sorszam'])

        if len(insert_rows_hatarozat) > 0:
            print(f'INSERTING {len(insert_rows_hatarozat)} HATAROZAT')
            with Session() as session:
                session.execute(
                    insert(Hatarozat),
                    insert_rows_hatarozat
                )
                session.commit()

    kapcs_hat_it = iter(kapcsolodo_hatarozatok_pairs)
    with Session() as session:
        while True:
            chunk = [{'id-1': sl[0], 'id-2': sl[1]} for sl in islice(kapcs_hat_it, 100)]
            if not chunk:
                break
            session.execute(
                insert(kapcsolodo_hatarozatok_table),
                chunk
            )


def collect_page_rows_and_go_to_next(driver):
    time.sleep(1)
    # Extract rows data
    yield from get_rows(driver)

    # Next page
    next_page_button = simple_find_or_none(driver, '//button[@class="grid-pager btn btn-default grid-pager-next"]')
    # disabled_attr = next_page_button.get_attribute('disabled')
    if next_page_button is not None:
        # if disabled_attr is None:
        ActionChains(driver).move_to_element(next_page_button).perform()
        next_page_button.click()
        time.sleep(1)
        yield from collect_page_rows_and_go_to_next(driver)
    return


def dropdown_select_by_text(driver, dropdown, form_value_option_xpath, scroll_for_date=False):
    dropdown.click()
    if scroll_for_date:
        scroll_form_dropdowns(driver)
    time.sleep(0.5)
    dropdown_option = driver.find_element(by=By.XPATH, value=form_value_option_xpath)  # select2-results__option
    dropdown_option.click()


def scroll_form_dropdowns(driver):
    last_elm = driver.find_elements(by=By.XPATH, value='.//li[@class="select2-results__option"]')[-1]
    driver.execute_script("arguments[0].scrollIntoView(true);", last_elm)
    time.sleep(1)
    next_last_elm = driver.find_elements(by=By.XPATH, value='.//li[@class="select2-results__option"]')[-1]
    scroll_to_form(driver)

    while last_elm.text != next_last_elm.text:
        driver.execute_script("arguments[0].scrollIntoView(true);", next_last_elm)
        scroll_to_form(driver)
        last_elm = next_last_elm
        next_last_elm = driver.find_elements(by=By.XPATH, value='.//li[@class="select2-results__option"]')[-1]
        scroll_to_form(driver)
        time.sleep(0.5)


def scroll_to_form(driver):
    # Form div
    form_container = driver.find_element(by=By.XPATH, value='//div[@class="main-content content searchParams"]')
    # Move
    driver.execute_script("arguments[0].scrollIntoView(true);", form_container)


if __name__ == '__main__':
    main(year_start=2020)
