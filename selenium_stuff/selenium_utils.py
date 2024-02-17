import logging
import time

from selenium.common import ElementClickInterceptedException, StaleElementReferenceException, \
    ElementNotInteractableException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By

from form_options_extraction import form_xpaths
from scraper_crawler_thing import set_up_page, download_hatarozat
from selenium_stuff.slenium_details import form_options_year, oldalmeret_dropdown_xpath, oldalmeret_100_option_xpath, \
    hatarozat_cols
from utils import simple_find_or_none

main_columns = {'Határozat sorszáma': 'sorszam',
                'Bíróság': 'birosag',
                'Kollégium': 'kollegium',
                'Jogterület': 'jogterulet',
                'Év': 'year'}
detail_columns = ['egyedi_azonosito', 'kapcsolodo_hatarozatok', 'jogszabalyhelyek', 'elvi_tartalma']
detail_column_values = {'Egyedi azonositó': 'egyedi_azonosito',
                        'Kapcsolódó határozatok': 'kapcsolodo_hatarozatok',
                        'Jogszabályhelyek': 'jogszabalyhelyek',
                        'A határozat elvi tartalma': 'elvi_tartalma'}
LETOLTES_URL_START = 'https://eakta.birosag.hu/hatarozat-letoltes'


def row_packages_gen(all_rows):

    all_rows_it = iter(all_rows)
    row_package = [next(all_rows_it)]

    for row in all_rows_it:
        if row.get_attribute('class') == 'add-border-top':
            yield row_package
            row_package = [row]
        else:
            row_package.append(row)

    yield row_package


def get_rows(driver, existing_azonosito_set, year):
    time.sleep(2)

    all_rows = driver.find_elements(by=By.XPATH, value='//tbody[@id="anonimHatarozatGridContent"]/tr')

    new_rows_data = []
    for row_package in row_packages_gen(all_rows):
        row_data = get_row_package_data(row_package, year)
        if row_data['egyedi_azonosito'] not in existing_azonosito_set:
            new_rows_data.append(row_data)

    return new_rows_data


def get_row_package_data(row_package, year):
    # Get row metadata
    row_data = {}
    # 1) Get run_crawler values from main_row
    main_row = row_package[0]
    column_titles = main_row.find_elements(by=By.XPATH, value='.//td/span[@class="d-md-none d-inline-block tableTitle"]')
    column_values = main_row.find_elements(by=By.XPATH, value='.//td/span[@class="tableData"]')
    for column_title, column_value in zip(column_titles, column_values):
        column_title_text = column_title.get_attribute("textContent").strip()
        column_value_text = column_value.text.strip()
        row_data[main_columns[column_title_text]] = column_value_text

    # 2) Get detail values - either one extra <tr> tag or two (main_row is first)
    if len(row_package) == 2:
        get_values_from_detail_row(row_package[1], row_data)
    elif len(row_package) == 3:
        # Get detail values from "Részletek" dropdown - "A hatarozat elvi tartalma"
        elvi_tart_row = row_package[1]
        elvi_tart_label = elvi_tart_row.find_element(by=By.TAG_NAME, value='label').get_attribute("textContent").strip()
        elvi_tart_div_text = elvi_tart_row.find_element(by=By.TAG_NAME, value='div').get_attribute("textContent").strip()
        elvi_tart_key = detail_column_values.get(elvi_tart_label)
        if elvi_tart_key is not None:
            row_data[elvi_tart_key] = elvi_tart_div_text
        else:
            raise ValueError('ELVI TARTALOM could not be extracted! Wrong label tag content!')

        get_values_from_detail_row(row_package[2], row_data)

    # Get download link
    download_a_tag = main_row.find_element(by=By.XPATH,
                                           value='.//td[@class="d-md-table-cell d-none"]/'
                                                 'div[@class="popover open-akta-popover"]/a')
    data_azonosito = download_a_tag.get_attribute('data-azonosito').strip()
    data_birosag = download_a_tag.get_attribute('data-birosag').strip()
    data_ugyszam = download_a_tag.get_attribute('data-ugyszam').strip()
    download_url = f'{LETOLTES_URL_START}/?birosagName={data_birosag}&ugyszam={data_ugyszam}&azonosito={data_azonosito}'
    row_data['download_url'] = download_url

    row_data['year'] = year

    return row_data


def get_values_from_detail_row(detial_row, row_data):
    # Get detail values from "Részletek" dropdown
    detail_row_divs = detial_row.find_elements(by=By.XPATH,
                                               value='.//div[@class="col-12" and not(@class="col-12 d-md-none")]')
    for detail_row_div in detail_row_divs:
        label = detail_row_div.find_element(by=By.TAG_NAME, value='label').get_attribute("textContent").strip()
        detail_column = detail_column_values.get(label)
        if detail_column is None:
            raise ValueError(f'Wrong implementation of detail column sequence! Value {label} not in '
                             f'detail_column_values lookup!')

        if detail_column == 'kapcsolodo_hatarozatok':
            hatarozatok_a_tags = detail_row_div.find_elements(by=By.TAG_NAME, value='a')
            if len(hatarozatok_a_tags) > 0:
                # Complete urls with base "https://eakta.birosag.hu"  # TODO lehet nem itt kéne?
                row_data[detail_column] = ';'.join([a.text.strip() for a in hatarozatok_a_tags])
        else:
            row_data[detail_column] = \
                detail_row_div.find_element(by=By.XPATH,
                                            value='.//div[@class="tableData"]').get_attribute("textContent").strip()


def scroll_to_form(driver):
    # Form div
    form_container = driver.find_element(by=By.XPATH, value='//div[@class="run_crawler-content content searchParams"]')
    # Move
    driver.execute_script("arguments[0].scrollIntoView(true);", form_container)


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


def collect_page_rows_and_go_to_next(driver, existing_azonosito_list, year):

    # Extract rows data
    yield get_rows(driver, existing_azonosito_list, year)

    # Next page
    next_page_button = simple_find_or_none(driver, '//button[@class="grid-pager btn btn-default grid-pager-next"]')
    # disabled_attr = next_page_button.get_attribute('disabled')
    if next_page_button is not None:
        # if disabled_attr is None:
        ActionChains(driver).move_to_element(next_page_button).perform()
        next_page_button.click()
        time.sleep(1)
        yield from collect_page_rows_and_go_to_next(driver, existing_azonosito_list, year)
    return


def process_combinations_gen(form_combinations, driver, kereses_button, existing_azonosito_list):
    for combination_i, combination in enumerate(form_combinations):
        try:
            # scrape combination
            insert_rows_hatarozat = scrape_combination(combination, driver, kereses_button, existing_azonosito_list)
            if len(insert_rows_hatarozat) > 0:
                yield insert_rows_hatarozat
            else:
                continue
        except (ElementClickInterceptedException, StaleElementReferenceException, ElementNotInteractableException) as e:
            # if scrape fails, start again from same combination
            print(f'FAILED TO SCRAPE COMBINATION {combination} - {e}')
            logging.error(f'FAILED TO SCRAPE COMBINATION {combination} - {e}')
            driver.close()
            driver, kereses_button = set_up_page()
            yield from process_combinations_gen(form_combinations[combination_i:], driver, kereses_button,
                                                existing_azonosito_list)


def scrape_combination(combination, driver, kereses_button, existing_azonosito_set):
    scroll_to_form(driver)
    print(f'RUNNING SEARCH COMBINATION: {combination}')
    logging.info(f'RUNNING SEARCH COMBINATION: {combination}')
    time.sleep(1)

    # Select everything but year
    for form_option, form_value in combination.items():
        if form_option != 'year':
            # Select form option
            form_value_option_xpath = f'//ul[@class="select2-results__options"]/li[contains(text(), "{form_value}")]'
            dropdown = driver.find_element(by=By.XPATH, value=form_xpaths[form_option]['xpath'])
            ActionChains(driver).move_to_element(dropdown).perform()
            time.sleep(1)
            dropdown_select_by_text(driver, dropdown, form_value_option_xpath)

    # Select year
    year = combination.get('year')
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
                                            value='//div[@class="table-data run_crawler-content"]/div[@class="count-wrappe'
                                                  'r"]/span[@class="listCountHolder"]').text.strip()
    if number_of_results == '10000+':
        raise NotImplementedError(f'Too many results, cannot be certain of parsing all results for combination '
                                  f'{combination}!')
    elif number_of_results == '0':
        return ()

    # Set pagination page size to 100
    driver.find_element(by=By.XPATH, value=oldalmeret_dropdown_xpath).click()
    driver.find_element(by=By.XPATH, value=oldalmeret_100_option_xpath).click()

    rows_gen = collect_page_rows_and_go_to_next(driver, existing_azonosito_set, year)

    return rows_gen
