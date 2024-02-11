from selenium.webdriver.common.by import By

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


def get_rows(driver) -> list:

    rows_data = []

    # tbody = driver.find_element(by=By.XPATH, value='//tbody[@id="anonimHatarozatGridContent"]')
    main_rows = driver.find_elements(by=By.XPATH, value='//tbody[@id="anonimHatarozatGridContent"]/tr[@class="add-border-top"]')
    detail_rows = driver.find_elements(by=By.XPATH, value='//tbody[@id="anonimHatarozatGridContent"]/tr[not(@class="add-border-top")]')  # not(contains(@title,'短期'))

    if len(main_rows) != len(detail_rows):  # for self
        raise NotImplementedError('Not same number of main and detail rows - bad implementation!')

    # 1a) Get metadata
    for row_n, (main_row, detail_row) in enumerate(zip(main_rows, detail_rows), start=1):

        row_data = {}

        # 1a.1) Get main values from row
        column_titles = main_row.find_elements(by=By.XPATH, value='.//td/span[@class="d-md-none d-inline-block tableTitle"]')
        column_values = main_row.find_elements(by=By.XPATH, value='.//td/span[@class="tableData"]')
        for column_title, column_value in zip(column_titles, column_values):
            column_title_text = column_title.get_attribute("textContent").strip()
            column_value_text = column_value.text.strip()
            row_data[main_columns[column_title_text]] = column_value_text

        # 1a.2) Get detail values from "Részletek" dropdown
        detail_row_divs = detail_row.find_elements(by=By.XPATH,
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
                    row_data[detail_column] = [(a.text.strip(), a.get_attribute('href')) for a in hatarozatok_a_tags]
            else:
                row_data[detail_column] = \
                    detail_row_div.find_element(by=By.XPATH,
                                                value='.//div[@class="tableData"]').get_attribute("textContent").strip()


        # # 2a) Download file
        # download_dropdown_button = row_element.find_element(by=By.TAG_NAME, value='button')
        # download_dropdown_button.click()
        #
        # download_button = row_element.find_element(by=By.XPATH, value='.//a[@id="letoltesPopupButton"]')
        # download_button.click()
        #
        # # 2b) Rename downloaded file and move to folder to use
        yield row_data
    #     rows_data.append(row_data)
    #
    # return rows_data
