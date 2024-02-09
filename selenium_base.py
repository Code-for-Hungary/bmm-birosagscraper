from selenium import webdriver

options = webdriver.ChromeOptions()
prefs = {"download.default_directory": "/tmp/birosag"}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(options=options)
