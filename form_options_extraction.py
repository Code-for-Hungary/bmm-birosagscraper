import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains

form_xpaths = {
        # 'ugycsoport': {'xpath': '//span[@id="select2-Ugycsoport-container"]', 'scroll': True},
        # 'jogterulet': {'xpath': '//span[@id="select2-Jogterulet-container"]'},
        'hatarozat_fajtaja': {'xpath': '//span[@id="select2-HatarozatFajta-container"]'},
        'kollegium': {'xpath': '//span[@id="select2-Kollegium-container"]'},
    }


def extract_form_options(driver):

    form_options = {}

    for field, details in form_xpaths.items():
        dropdown = driver.find_element(by=By.XPATH, value=details['xpath'])

        dropdown.click()

        if details.get('scroll') is True:
            scroll_form_dropdowns(driver)

        dropdown_options = driver.find_elements(by=By.XPATH, value='//li[@class="select2-results__option"]')
        form_options[field] = _get_dropdown_options(dropdown_options)
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(2)

    return form_options


def _get_dropdown_options(dropdown_options):
    return [option.text for option in dropdown_options]


def scroll_form_dropdowns(driver):

    last_elm = driver.find_elements(by=By.XPATH, value='//li[@class="select2-results__option"]')[-1]
    driver.execute_script("arguments[0].scrollIntoView(true);", last_elm)
    time.sleep(1)
    next_last_elm = driver.find_elements(by=By.XPATH, value='//li[@class="select2-results__option"]')[-1]

    while last_elm.text != next_last_elm.text:
        driver.execute_script("arguments[0].scrollIntoView(true);", next_last_elm)
        last_elm = next_last_elm
        next_last_elm = driver.find_elements(by=By.XPATH, value='//li[@class="select2-results__option"]')[-1]
        time.sleep(0.5)


if __name__ == '__main__':
    extract_form_options()