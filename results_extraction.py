from selenium.webdriver.common.by import By

from utils import simple_find_or_none


column_main_values = {'Határozat sorszáma': 'sorszam',
                      'Bíróság': 'birosag',
                      'Kollégium': 'kollegium',
                      'Jogterület': 'jogterulet',
                      'Év': 'year'}


def get_rows(driver):
    tbody = driver.find_element(by=By.XPATH, value='//tbody[@id="anonimHatarozatGridContent"]')
    main_rows = tbody.find_elements(by=By.XPATH, value='/tr[@class="add-border-top"]')
    detail_rows = tbody.find_elements(by=By.XPATH, value='/tr[not(@class="add-border-top")]')  # not(contains(@title,'短期'))

    print(len(main_rows), len(detail_rows))

    # 1a) Get metadata
    for row_element in main_rows:
        row_data = {}
        # 1a.1) Get main values from row
        # columns = row_element.find_elements(by=By.XPATH, value='//td')
        # for column in columns:
        #     column_title = column.find_element(
        #         by=By.XPATH, value='//span[@class="d-md-none d-inline-block tableTitle"]').text.strip()
        #     column_value = column.find_element(by=By.XPATH, value='//span[@class="tableData"]').text.strip()
        #     row_data[column_main_values[column_title]] = column_value
        #
        # # 1a.2) Get detail values from "Részletek" dropdown
        # reszletek_button = row_element.find_element(by=By.XPATH, value='//a[@class="green-text underlined collapsed"]')
        # reszletek_button.click()
        #
        # # 1b) Save metadata in SQL (with filename)
        #
        # # 2a) Download file
        # download_dropdown_button = row_element.find_element(by=By.TAG_NAME, value='button')
        # download_dropdown_button.click()
        #
        # download_button = row_element.find_element(by=By.XPATH, value='.//a[@id="letoltesPopupButton"]')
        # download_button.click()
        #
        # # 2b) Rename downloaded file and move to folder to use

        exit(10)
