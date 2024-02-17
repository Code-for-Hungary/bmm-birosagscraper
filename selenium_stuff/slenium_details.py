scroll_into_view_js_code = "arguments[0].scrollIntoView();"
form_options_year = {
    'from': {'xpath': '//span[@id="select2-MeghozatalIdejeTol-container"]'},
    'to': {'xpath': '//span[@id="select2-MeghozatalIdejeIg-container"]'}
}
oldalmeret_dropdown_xpath = '//span[@id="select2-page-size-container"]'
oldalmeret_100_option_xpath = '//li[contains(text(), "100")]'
next_page_enabled_button_xpath = '//button[@class="grid-pager btn btn-default grid-pager-next"]'
next_page_disabled_button_xpath = '//button[@class="grid-pager btn btn-default grid-pager-next disabled"]'
hatarozat_cols = {'sorszam', 'birosag', 'kollegium', 'jogterulet', 'year', 'egyedi_azonosito', 'jogszabalyhelyek',
                  'elvi_tartalma', 'kapcsolodo_hatarozatok', 'download_url'}
