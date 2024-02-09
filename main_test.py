import pickle
import time

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


def main():
    driver.get("https://eakta.birosag.hu/anonimizalt-hatarozatok")
    driver.implicitly_wait(1)

    # Keresés gomb
    kereses_button = driver.find_element(by=By.XPATH, value='//button[@class="filter-button custom-button float-left"]')

    # Tobb szűrő megjelenítése
    tobb_szuro_button = driver.find_element(by=By.XPATH, value='//button[@class="custom-button white collapse-button"]')
    tobb_szuro_button.click()

    form_options = extract_form_options(driver)

    form_combinations = get_form_option_and_date_combinations(form_options, year_start=2022)

    for year, (form_option, form_value) in form_combinations:

        # Select form option
        form_value_option_xpath = f'//ul[@class="select2-results__options"]/li[contains(text(), "{form_value}")]'
        dropdown = driver.find_element(by=By.XPATH, value=form_xpaths[form_option]['xpath'])
        dropdown_select_by_text(driver, dropdown, form_value_option_xpath)
        time.sleep(2)

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
        # Make sure results are not truncated.
        number_of_results = driver.find_element(by=By.XPATH,
                                                value='//div[@class="table-data main-content"]/div[@class="count-wrappe'
                                                      'r"]/span[@class="listCountHolder"]').text.strip()
        if number_of_results == '10000+':
            raise NotImplementedError('Too many results, cannot be certain of parsing all results!')

        # Extract rows data
        get_rows(driver)

        # Set pagination page size to 100
        driver.find_element(by=By.XPATH, value=oldalmeret_dropdown_xpath).click()
        driver.find_element(by=By.XPATH, value=oldalmeret_100_option_xpath).click()

        # Next page
        next_page_disabled_button = driver.find_elements(by=By.XPATH, value=next_page_disabled_button_xpath)
        # TODO
        if len(next_page_disabled_button) > 0:
            continue  # go to next form combination
        else:
            next_page_enabled_button = driver.find_elements(by=By.XPATH, value=next_page_enabled_button_xpath)
            next_page_enabled_button.click()


def dropdown_select_by_text(driver, dropdown, form_value_option_xpath):
    dropdown.click()
    time.sleep(0.5)
    scroll_form_dropdowns(driver)
    dropdown_option = driver.find_element(by=By.XPATH, value=form_value_option_xpath)  # select2-results__option
    dropdown_option.click()
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()  # Maybe don't need
    time.sleep(1)


if __name__ == '__main__':
    main()
