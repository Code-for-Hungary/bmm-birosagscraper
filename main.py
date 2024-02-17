import json
import requests

# URL of the REST API endpoint
url = 'https://eakta.birosag.hu/AnonimizaltHatarozat/Search'

# Form data
data = {
    'ResultCount': '100',
    'ResultStartIndex': '0',
    'ResultSortExpression': 'Id asc',
    'KeresoSzo': '',
    'KeresoSzoTeljesKifejezes': 'false',
    'Rezume': '',
    'RezumeTeljesKifejezes': 'false',
    'JogTerulet': '',
    'MeghozoBirosag': '',
    'ErintettKozigazgatsaiSzerv': '',
    'Azonosito': '',
    'HatarozatFajta': 'Végzés',
    'MeghozatalIdejeTol': '2024',
    'MeghozatalIdejeIg': '2024',
    'Ugycsoport': '',
    'Ugytargy': '',
    'BefejezesMod': '',
    'ItelkezesiGyakorlat': '',
    'EUJoganyag': '',
    'EJEBJoganyag': '',
    'Kollegium': 'polgári',
    'HatarozatTipus': '',
    'EgyediAzonosito': '',
    'Rendezes': 'BirosagiSzint',
    'JogszabalyHely[GyakoriJogszabalyId]': '',
    'JogszabalyHely[JogszabalyHivatkozas]': '',
    'JogszabalyHely[JogszabalyIdejeTol]': '',
    'JogszabalyHely[JogszabalyIdejeIg]': ''
}

# Request headers
headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,hu;q=0.7',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Cookie': 'SessionID=r4utjm40ctavw4nwfoyj1xzh; language=en-US; path=/; fileDownload=true; UserTimeZoneOffset=60',
    'Host': 'eakta.birosag.hu',
    'Origin': 'https://eakta.birosag.hu',
    'Referer': 'https://eakta.birosag.hu/AnonimizaltHatarozat/',
    'sec-ch-ua': '"Google Chrome";v="105", "Not)A;Brand";v="8", "Chromium";v="105"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest'
}

# Make the POST request
response = requests.post(url, headers=headers, data=data)

# Print the response content
list_res = json.loads(response.content.decode())['List']
print(list_res[0])



# import requests
# import json
# headers = {
# 'Accept': '*/*',
# 'Accept-Encoding': 'gzip, deflate, br',
# 'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,hu;q=0.7',
# 'Connection': 'keep-alive',
# 'Content-Length': '610',
# 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
# 'Cookie': 'SessionID=r4utjm40ctavw4nwfoyj1xzh; language=en-US; path=/; fileDownload=true; UserTimeZoneOffset=60',
# 'Host': 'eakta.birosag.hu',
# 'Origin': 'https://eakta.birosag.hu',
# 'Referer': 'https://eakta.birosag.hu/AnonimizaltHatarozat/',
# 'sec-ch-ua': '"Google Chrome";v="105", "Not)A;Brand";v="8", "Chromium";v="105"',
# 'sec-ch-ua-mobile': '?0',
# 'sec-ch-ua-platform': 'Linux',
# 'Sec-Fetch-Dest': 'empty',
# 'Sec-Fetch-Mode': 'cors',
# 'Sec-Fetch-Site': 'cross-site', # 'cross-site' 'same-origin'
# 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
# 'X-Requested-With': 'XMLHttpRequest',
#
# }
#
# form_data = {'ResultCount': '100',
#              'ResultStartIndex': '0',
#              'ResultSortExpression': 'Id asc',
#              'KeresoSzoTeljesKifejezes': 'false',
#              'RezumeTeljesKifejezes': 'false',
#              'MeghozatalIdejeTol': '2024',
#              'MeghozatalIdejeIg': '2024',
#              'Rendezes': 'BirosagiSzint',
#              'HatarozatFajta': 'Végzés',
#              'Kollegium': 'polgári'}
#
# url = 'https://eakta.birosag.hu/AnonimizaltHatarozat/Search'
#
# server = requests.post(url, params={'Area': None}, data=form_data, headers=headers)
# output = server.text
#
# print(output)
#
#
#
#
# """'KeresoSzo':
# 'Rezume':
# 'JogTerulet':
# 'MeghozoBirosag':
# 'ErintettKozigazgatsaiSzerv':
# 'Azonosito':
# 'Ugycsoport':
# 'Ugytargy':
# 'BefejezesMod':
# 'ItelkezesiGyakorlat':
# 'EUJoganyag':
# 'EJEBJoganyag':
# 'HatarozatTipus':
# 'EgyediAzonosito':
# 'JogszabalyHely[GyakoriJogszabalyId]':
# 'JogszabalyHely[JogszabalyHivatkozas]':
# 'JogszabalyHely[JogszabalyIdejeTol]':"""
#
# """
# https://eakta.birosag.hu/AnonimizaltHatarozat/Search?ResultCount=100&ResultStartIndex=0&ResultSortExpression=Id+asc&KeresoSzoTeljesKifejezes=false&RezumeTeljesKifejezes=false&MeghozatalIdejeTol=2024&MeghozatalIdejeIg=2024&Rendezes=BirosagiSzint&KeresoSzo&Rezume&JogTerulet&MeghozoBirosag&ErintettKozigazgatsaiSzerv&Azonosito&HatarozatFajta=V%C3%A9gz%C3%A9s&Ugycsoport&Ugytargy&BefejezesMod&ItelkezesiGyakorlat&EUJoganyag&EJEBJoganyag&Kollegium=polg%C3%A1ri&HatarozatTipus&EgyediAzonosito&JogszabalyHely[GyakoriJogszabalyId]&JogszabalyHely[JogszabalyHivatkozas]&JogszabalyHely[JogszabalyIdejeTol]"""