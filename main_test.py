import pickle
import time

import jsonlines
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium_base import driver
from utils import get_form_option_and_date_combinations, simple_find_or_none
from form_options_extraction import extract_form_options, form_xpaths, scroll_form_dropdowns
from results_extraction import get_rows

form_options_year = {
    'from': {'xpath': '//span[@id="select2-MeghozatalIdejeTol-container"]'},
    'to': {'xpath': '//span[@id="select2-MeghozatalIdejeIg-container"]'}
}

oldalmeret_dropdown_xpath = '//span[@id="select2-page-size-container"]'
# oldalmeret_100_option_xpath = '//li[@id="select2-page-size-result-viss-100"]'
oldalmeret_100_option_xpath = '//li[contains(text(), "100")]'

next_page_enabled_button_xpath = '//button[@class="grid-pager btn btn-default grid-pager-next"]'
next_page_disabled_button_xpath = '//button[@class="grid-pager btn btn-default grid-pager-next disabled"]'


def main(out_filename, select_year=None):
    driver.get("https://eakta.birosag.hu/anonimizalt-hatarozatok")
    driver.implicitly_wait(1)

    # Keresés gomb
    kereses_button = driver.find_element(by=By.XPATH, value='//button[@class="filter-button custom-button float-left"]')

    # Tobb szűrő megjelenítése
    tobb_szuro_button = driver.find_element(by=By.XPATH, value='//button[@class="custom-button white collapse-button"]')
    tobb_szuro_button.click()

    if select_year is not None:  # TODO
        # Select year
        from_dropdown = driver.find_element(by=By.XPATH, value=form_options_year['from']['xpath'])
        to_dropdown = driver.find_element(by=By.XPATH, value=form_options_year['to']['xpath'])
        # for from_to_dropdown in (from_dropdown, to_dropdown):  # Remove year if previously set
        #     selection_x = simple_find_or_none(from_to_dropdown, '//span[@class="select2-selection__clear"]')
        #     if selection_x is not None:
        #         selection_x.click()
        #         ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        date_to_and_from_option_xpath = f'//ul[@class="select2-results__options"]/li[contains(text(), "{year}")]'
        dropdown_select_by_text(driver, from_dropdown, date_to_and_from_option_xpath)
        dropdown_select_by_text(driver, to_dropdown, date_to_and_from_option_xpath)

        kereses_button.click()
        time.sleep(2)
    time.sleep(0.5)
    # Set pagination page size to 100
    driver.find_element(by=By.XPATH, value=oldalmeret_dropdown_xpath).click()
    driver.find_element(by=By.XPATH, value=oldalmeret_100_option_xpath).click()

    with jsonlines.open(out_filename, 'w') as fh:
        for res in collect_page_rows_and_go_to_next(driver):
            fh.write(res)


def collect_page_rows_and_go_to_next(driver):
    # Extract rows data
    yield from get_rows(driver)

    # Next page
    next_page_button = simple_find_or_none(driver, '//button[@class="grid-pager btn btn-default grid-pager-next"]')
    disabled_attr = next_page_button.get_attribute('disabled')
    if disabled_attr is None:
        next_page_button.click()
        time.sleep(1)
        yield from collect_page_rows_and_go_to_next(driver)
    return


def dropdown_select_by_text(driver, dropdown, form_value_option_xpath):
    dropdown.click()
    time.sleep(0.5)
    scroll_form_dropdowns(driver)
    dropdown_option = driver.find_element(by=By.XPATH, value=form_value_option_xpath)  # select2-results__option
    dropdown_option.click()
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()  # Maybe don't need
    time.sleep(1)


if __name__ == '__main__':
    main('data/all_results.jsonl')
