import time
from pathlib import Path

from slugify import slugify
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains

from selenium_base import DOWNLOAD_DIRECTORY, SAVE_DIRECTORY

save_directory_path = Path(SAVE_DIRECTORY)
download_directory_path = Path(DOWNLOAD_DIRECTORY)

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


def get_rows(driver):

    main_rows = driver.find_elements(by=By.XPATH, value='//tbody[@id="anonimHatarozatGridContent"]/tr[@class="add-border-top"]')
    detail_rows = driver.find_elements(by=By.XPATH, value='//tbody[@id="anonimHatarozatGridContent"]/tr[not(@class="add-border-top")]')  # not(contains(@title,'短期'))

    if len(main_rows) != len(detail_rows):  # for self
        raise NotImplementedError('Not same number of main and detail rows - bad implementation!')

    # Get metadata
    for row_n, (main_row, detail_row) in enumerate(zip(main_rows, detail_rows), start=0):

        # Move down
        if len(main_rows) != row_n+1:
            ActionChains(driver).move_to_element(main_rows[row_n+1]).perform()

        row_data = {}

        # 1) Get main values from row
        # ActionChains(driver).move_to_element(main_row).perform()
        column_titles = main_row.find_elements(by=By.XPATH, value='.//td/span[@class="d-md-none d-inline-block tableTitle"]')
        column_values = main_row.find_elements(by=By.XPATH, value='.//td/span[@class="tableData"]')
        for column_title, column_value in zip(column_titles, column_values):
            column_title_text = column_title.get_attribute("textContent").strip()
            column_value_text = column_value.text.strip()
            row_data[main_columns[column_title_text]] = column_value_text

        # 2) Get detail values from "Részletek" dropdown
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
                    # Complete urls with base "https://eakta.birosag.hu"  # TODO lehet nem itt kéne?
                    row_data[detail_column] = [a.text.strip() for a in hatarozatok_a_tags]
            else:
                row_data[detail_column] = \
                    detail_row_div.find_element(by=By.XPATH,
                                                value='.//div[@class="tableData"]').get_attribute("textContent").strip()

        # 3) Download file
        download_dropdown_button = main_row.find_element(by=By.TAG_NAME, value='button')
        download_dropdown_button.click()
        download_a_tag = main_row.find_element(by=By.XPATH, value='.//a[@id="letoltesPopupButton"]')
        download_a_tag.click()
        time.sleep(1)
        main_row.find_element(by=By.TAG_NAME, value='td').click()

        downloaded_filepaths = list(download_directory_path.glob('*'))
        if len(downloaded_filepaths) > 1:
            raise Warning('Temporary download directory has more than one file, they will all be deleted!')
        for downloaded_file in downloaded_filepaths:
            # create new filepath
            new_file_name = slugify(row_data['sorszam']) + downloaded_file.suffix
            new_file_path = save_directory_path / new_file_name
            new_file_path.write_bytes(downloaded_file.read_bytes())
            downloaded_file.unlink()
            row_data['filepath'] = new_file_name

        yield row_data
