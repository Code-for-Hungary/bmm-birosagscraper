import logging
import configparser
from datetime import datetime
from itertools import product
from tempfile import TemporaryFile
from argparse import ArgumentParser

import huspacy
import requests
from docx import Document
from jinja2 import Environment, FileSystemLoader, select_autoescape

from bmm_backend import BmmBackend
from bmm_birosagdb import BmmBirosagDB
from bmm_tools import lemmatize, searchstringtofts
from birosag_api_configs import BIROSAG_API_FORMDATA_BASE, LETOLTES_URL_START, FORM_OPTIONS


def get_form_option_and_date_combinations(form_options: dict, year_start=1998):
    keys = list(form_options.keys())
    values = list(form_options.values())

    combinations = []
    for year in range(year_start, datetime.today().year+1):
        for combination_values in product(*values):
            combination = {'MeghozatalIdejeTol': str(year), 'MeghozatalIdejeIg': str(year)}
            for key, value in zip(keys, combination_values):
                combination[key] = value
            combinations.append(combination)

    return combinations


def response_list_gen(form_data_combination, api_url, result_start_index):

    # Set starting index
    form_data_combination['ResultStartIndex'] = str(result_start_index)

    # Make request
    response = requests.post(api_url, data=form_data_combination)
    if response.status_code == 200:
        response_data = response.json()
    else:
        raise requests.exceptions.RequestException(f'Could not get response for combination '
                                                   f'{form_data_combination} !')

    count = response_data['Count']
    if count == 10000:
        raise NotImplementedError(f'Too many responses for combination {form_data_combination} ! Cannot ensure'
                                  f'all results are fetched!')

    response_list = response_data['List']
    if len(response_list) > 0:
        for elem in response_list:
            yield elem
        # yield from iter(response_list)

    if len(response_list) == 100:
        yield from response_list_gen(form_data_combination, api_url, result_start_index + 100)


def clear_is_new(ids, db):
    for num in ids:
        db.clear_is_new(num)

    db.commit_connection()


def download_data(year_start, existing_azonosito_set, api_url, db, nlp):
    """
    Get results for all query combinations, and save non-existing results to database. All combinations have to be
    queried to ensure all new 'hatarozat' are returned, as results only have 'year' metadata, no months or days are
    shown.
    :param year_start: Year to start query combinations from
    :param existing_azonosito_set: Existing egyedi_azonosito values
    :param api_url: URL of anotnimizalt birosagi hatarozatok API
    :param db: BmmBirosagDB instance
    :param nlp: Huspacy instance
    :return: -
    """

    # Get combinations are API responses for each
    combinations = get_form_option_and_date_combinations(FORM_OPTIONS, year_start)

    for form_data_combination in combinations:

        form_data = BIROSAG_API_FORMDATA_BASE.copy()

        form_data.update(form_data_combination)

        results_start_index = 0  # ResultStartIndex

        for response_list_item in response_list_gen(form_data, api_url, results_start_index):
            egyedi_azonosito = response_list_item['EgyediAzonosito']
            if egyedi_azonosito not in existing_azonosito_set:

                # Get scrape date-time
                response_list_item['scrape_date'] = datetime.today().strftime("%Y-%m-%dT%H-%M")

                # Create url
                url = f'https://eakta.birosag.hu//anonimizalt-hatarozatok?azonosito={response_list_item["Azonosito"]}' \
                      f'&birosag={response_list_item["MeghozoBirosag"]}'
                response_list_item['url'] = url

                # Create download_url
                birosag = response_list_item['MeghozoBirosag']
                azonosito = response_list_item['Azonosito']
                index_id = response_list_item['IndexId']
                response_list_item['download_url'] = \
                    f'{LETOLTES_URL_START}/?birosagName={birosag}&ugyszam={azonosito}&azonosito={index_id}'

                # Download file TODO handle errors
                download_resp = requests.get(response_list_item['download_url'])
                if download_resp.status_code == 200:
                    downloaded_content = download_resp.content
                else:
                    raise FileNotFoundError(f'Could not download file for {response_list_item}')

                if download_resp.headers['Content-Type'] != \
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                    raise NotImplementedError(f'Receive Content-Type not handled: '
                                              f'{download_resp.headers["Content-Type"]}')

                # Create temporary file to save docx
                temp = TemporaryFile()
                temp.write(downloaded_content)
                temp.seek(0)

                # Exctract text from docx (as paragraphs for quicker nlp processing)
                doc = Document(temp)
                response_list_item['paragraphs'] = [par.text for par in doc.paragraphs]
                temp.close()

                # Lemmatize if needed
                lemmas = []
                if nlp is not None:
                    lemmas = lemmatize(nlp, response_list_item['paragraphs'])

                response_list_item['lemmacontent'] = " ".join(lemmas)
                response_list_item['content'] = '\n'.join(response_list_item.pop('paragraphs'))

                # Save to database
                db.save_hatarozat(response_list_item)
                existing_azonosito_set.add(egyedi_azonosito)

        db.commit_connection()  # Commit for every combination


def handle_events(backend, config, contenttpl, db):
    found_ids = []
    events = backend.get_events()
    for event in events['data']:
        result = None

        if event['type'] == 1:
            keresoszo = searchstringtofts(event['parameters'])
            if keresoszo:
                result = db.search_records(keresoszo)
                for res in result:
                    found_ids.append(res[0])
        else:
            result = db.get_all_new()
            for res in result:
                found_ids.append(res[0])

        if result:
            content = ''
            for res in result:
                content = content + contenttpl.render(contract=res)

            if config['DEFAULT']['donotnotify'] == '0':
                backend.notify_event(event['id'], content)
                logging.info(f"Notified: {event['id']} - {event['type']} - {event['parameters']}")
    return found_ids


def main(config_path, with_backend=False):
    config = configparser.ConfigParser()
    config.read(config_path)

    # Logging
    logging.basicConfig(
        filename=f'logs/{datetime.today().strftime("%Y-%m-%d_%H-%M")}_{config["DEFAULT"]["logfile_name"]}',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s | %(module)s.%(funcName)s line %(lineno)d: %(message)s')

    logging.info('BirosagAnonimizalHatarozatok scraper started')

    # Database
    db = BmmBirosagDB(config['DEFAULT']['database_name'])

    # Get start year
    year_start = config['Download']['year_start']
    if year_start == 'current':
        year_start = datetime.today().year
    else:
        year_start = int(year_start)

    # Load nlp
    if config['DEFAULT']['donotlemmatize'] == '0':
        nlp = huspacy.load()
    else:
        nlp = None

    # Download
    download_data(year_start, db.get_existing_azonosito_set(), config['Download']['url'], db, nlp)

    # Backend Events TODO ez a with_backend majd nem lesz
    if with_backend:
        # Jinja template
        env = Environment(
            loader=FileSystemLoader('templates'),
            autoescape=select_autoescape()
        )
        contenttpl = env.get_template('content.html')

        # Backend TODO
        backend = BmmBackend(config['DEFAULT']['monitor_url'], config['DEFAULT']['uuid'])

        # Events TODO
        found_ids = handle_events(backend, config, contenttpl, db)

        if config['DEFAULT']['staging'] == '0':
            clear_is_new(found_ids, db)

    db.close_connection()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('config_path', help='Path to config file!')
    args = parser.parse_args()
    main(args.config_path, with_backend=False)
