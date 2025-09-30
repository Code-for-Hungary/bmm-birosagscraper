import time
import logging
import configparser
from pathlib import Path
from datetime import datetime
from itertools import product, repeat
from tempfile import TemporaryFile
from argparse import ArgumentParser

import huspacy
import re
from docx import Document
from jinja2 import Environment, FileSystemLoader, select_autoescape
from requests import RequestException, get as requests_get, post as requests_post

from bmm_backend import BmmBackend
from bmm_birosagdb import BmmBirosagDB
from bmm_tools import lemmatize, searchstringtofts
from birosag_api_configs import BIROSAG_API_FORMDATA_BASE, LETOLTES_URL_START, FORM_OPTIONS


def make_request(url, request_func, request_args={}, retry=10):
    for i in range(1, retry + 1):
        try:
            response = request_func(url, **request_args, timeout=10)
            if response.status_code != 200:
                logging.warning(f'Could not get response for {url} -- {request_args} on try {i}. '
                                f'Retrying.!')
            else:
                return response
        except RequestException as e:
            logging.warning(f'Network error happened (retry, {i}, ): {e}')
            time.sleep(i*5)
    else:
        raise RequestException(f'Could not get response for: {url} -- {request_args}')


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
    response = make_request(api_url, requests_post, {'data': form_data_combination})
    response_data = response.json()

    count = response_data['Count']
    if count == 10000:
        raise NotImplementedError(f'Too many responses for combination {form_data_combination} ! Cannot ensure'
                                  f'all results are fetched!')

    response_list = response_data['List']
    if len(response_list) > 0:
        for elem in response_list:
            yield elem

    if len(response_list) == 100:
        yield from response_list_gen(form_data_combination, api_url, result_start_index + 100)


def clear_is_new(ids, db):
    for num in ids:
        db.clear_is_new(num)

    db.commit_connection()


def search(entry, keyword, do_lemmatize=False):
    text = entry["content"] if not do_lemmatize else entry["lemmacontent"]
    keyword = keyword.replace('*', '').replace('"', '')
    results = []
    matches = [m.start() for m in re.finditer(re.escape(keyword), text, re.IGNORECASE)]

    surrounding_context = 64

    for match_index in matches:
        before_context = text[max(0, match_index-surrounding_context):match_index]
        after_context = text[match_index+len(keyword):match_index+len(keyword)+surrounding_context]
        common_part = text[match_index:match_index+len(keyword)]

        lemma_warn = ''
        if do_lemmatize:
            lemma_warn = "szótövezett találat: "

        results.append(
            {
                "before": lemma_warn+before_context,
                "after": after_context,
                "common": common_part,
            }
        )
    return results

def find_matching_multiple(keywords, entry, config):
    all_results = []
    print("Searching for keywords:", keywords)
    for keyword in keywords:
        keyword_results = search(entry, keyword)
        if not keyword_results and config['DEFAULT']['donotlemmatize'] == '0':
            keyword_results = search(entry, keyword, do_lemmatize=True)
        all_results += keyword_results
    return all_results


def download_data(year_start, existing_azonosito_set, api_url, db, nlp, just_download=False):
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

    entries = []

    # Get combinations are API responses for each
    combinations = get_form_option_and_date_combinations(FORM_OPTIONS, year_start)

    for form_data_combination in combinations:
        print(form_data_combination)
        form_data = BIROSAG_API_FORMDATA_BASE.copy()

        form_data.update(form_data_combination)

        results_start_index = 0  # ResultStartIndex

        committed_counter = 0
        for response_list_item in response_list_gen(form_data, api_url, results_start_index):
            egyedi_azonosito = response_list_item['EgyediAzonosito']
            if egyedi_azonosito not in existing_azonosito_set:
                if just_download:
                    db.save_hatarozat(response_list_item)
                    db.clear_is_new(egyedi_azonosito)
                    entries.append((egyedi_azonosito, response_list_item.copy()))
                    existing_azonosito_set.add(egyedi_azonosito)
                    committed_counter += 1
                    continue

                # Get scrape date-time
                response_list_item['scrape_date'] = datetime.today().strftime("%Y-%m-%dT%H-%M")

                # Create url
                url = f'https://eakta.birosag.hu/anonimizalt-hatarozatok?azonosito={response_list_item["Azonosito"]}' \
                      f'&birosag={response_list_item["MeghozoBirosag"]}'
                response_list_item['url'] = url

                # Create download_url
                birosag = response_list_item['MeghozoBirosag']
                azonosito = response_list_item['Azonosito']
                index_id = response_list_item['IndexId']
                response_list_item['download_url'] = \
                    f'{LETOLTES_URL_START}/?birosagName={birosag}&ugyszam={azonosito}&azonosito={index_id}'

                # Download file
                response = make_request(response_list_item['download_url'], requests_get)
                if response.headers['Content-Type'] != \
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                    raise NotImplementedError(f'Receive Content-Type not handled: '
                                              f'{response.headers["Content-Type"]}')
                downloaded_content = response.content

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
                entries.append((egyedi_azonosito, response_list_item.copy()))
                existing_azonosito_set.add(egyedi_azonosito)
                committed_counter += 1
                logging.info(f'Downloaded hatarozat with egyedi_azonosito: {egyedi_azonosito}')

        if committed_counter > 0:
            logging.info(f'Committed {committed_counter} new rows to db for form_data_combination {form_data_combination}')
            db.commit_connection()  # Commit for every combination

    return entries


def handle_events(backend, config, contenttpl, contenttpl_keyword, db, api_key, new_entries):
    found_ids = []
    events = backend.get_events(api_key)
    for event in events['data']:
        result = ()
        snippets = repeat([])
        content = ''

        if event['type'] == 1:  # Event is of specific keyword
            for entry in new_entries:
                search_results = find_matching_multiple(event['parameters'].split(","), entry, config)
                result_entry = entry.copy()
                result_entry["result_count"] = len(search_results)
                result_entry["results"] = search_results[:5]
                if result_entry["results"]:
                    content += contenttpl_keyword.render(hatarozat = result_entry)
                found_ids.append(entry["egyedi_azonosito"])

        else:  # Event is of whole database update
            for entry in new_entries:
                content = content + contenttpl.render(hatarozat = entry)
                found_ids.append(entry["egyedi_azonosito"])

        if config['DEFAULT']['donotnotify'] == '0' and content:
            backend.notify_event(event['id'], content, api_key)
            logging.info(f"Notified: {event['id']} - {event['type']} - {event['parameters']}")
        else:
            logging.info(f"Did not notify: {event['id']} - {event['type']} - {event['parameters']}")

    return found_ids


def main():
    config = configparser.ConfigParser()
    config.read_file(open('config.ini'))
    api_key = config['DEFAULT']['eventgenerator_api_key']

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
    just_download = config['DEFAULT'].getint('just_download', fallback=0) == 1
    download_data(year_start, db.get_existing_azonosito_set(), config['Download']['url'], db, nlp, just_download)
    new_entries = db.get_all_new()

    # Jinja template
    env = Environment(
        loader=FileSystemLoader('templates'),
        autoescape=select_autoescape()
    )
    contenttpl = env.get_template('content.html')
    contenttpl_keyword = env.get_template('content_keyword.html')

    # Backend
    backend = BmmBackend(config['DEFAULT']['monitor_url'], config['DEFAULT']['uuid'])

    # Events
    found_ids = handle_events(backend, config, contenttpl, contenttpl_keyword, db, api_key, new_entries)

    if config['DEFAULT']['staging'] == '0':
        print("CLEARING", found_ids)
        clear_is_new(found_ids, db)

    db.close_connection()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('config_path', help='Path to config file!')

    # Create logs dir
    logs_dir = Path('./logs')
    if logs_dir.is_dir() is False:
        logs_dir.mkdir(exist_ok=True, parents=True)

    main()
