from datetime import datetime
from itertools import product

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


def simple_find_or_none(tag, xpath):
    try:
        result = tag.find_element(by=By.XPATH, value=xpath)
    except NoSuchElementException:
        result = None
    return result


def get_form_option_and_date_combinations(form_options: dict, year_start=1998):

    key_value_pairs = [list(range(year_start, datetime.today().year+1))]
    for key, values in form_options.items():
        key_value_pairs_for_key = []
        for value in values:
            key_value_pairs_for_key.append((key, value))
        key_value_pairs.append(key_value_pairs_for_key)

    return product(*key_value_pairs)


def get_form_combinations(form_options: dict):

    key_value_pairs = []
    for key, values in form_options.items():
        key_value_pairs_for_key = []
        for value in values:
            key_value_pairs_for_key.append((key, value))
        key_value_pairs.append(key_value_pairs_for_key)

    return product(*key_value_pairs)
