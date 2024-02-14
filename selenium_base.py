from selenium import webdriver

DOWNLOAD_DIRECTORY = '/tmp/birosag'
SAVE_DIRECTORY = './data/texts'


def create_driver():
    options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": DOWNLOAD_DIRECTORY}
    options.add_experimental_option("prefs", prefs)
    # options.add_argument('--headless=new')
    # options.add_argument("--window-size=1280,700")
    driver = webdriver.Chrome(options=options)

    return driver
