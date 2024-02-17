from selenium import webdriver

from scraper_crawler_thing import SAVE_DIRECTORY


def create_driver(headless=False):
    options = webdriver.ChromeOptions()
    # prefs = {"download.default_directory": SAVE_DIRECTORY}
    # options.add_experimental_option("prefs", prefs)
    if headless:
        options.add_argument('--headless=new')
    options.add_argument("--window-size=1280,700")
    driver = webdriver.Chrome(options=options)

    return driver
