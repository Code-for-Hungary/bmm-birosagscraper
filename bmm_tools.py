import re


def searchstringtofts(searchstring):

    keresoszo = ''
    if isinstance(searchstring, str):
        keresoszo = searchstring.strip()
        keresoszo = re.sub(r'\s+', ' ', keresoszo)
        keresoszo = re.sub(r'([()\-])', '', keresoszo)
        if '"' in keresoszo:
            keresoszo = keresoszo.replace('"', '""')
        if keresoszo:
            if not re.search(r'(["+*])', keresoszo):
                # Add " to both ends of string to make it literal
                keresoszo = '"' + re.sub(r'([\s])', ' + ', keresoszo) + '"' + '*'

    return keresoszo


def lemmatize(nlp, texts):
    lemmas = []
    docs = list(nlp.pipe(texts))
    for doc in docs:
        for token in doc:
            if token.pos_ in ['NOUN', 'ADJ', 'PROPN', 'ADP', 'ADV', 'VERB'] and token.lemma_.isalpha():
                lemmas.append(token.lemma_.lower())
    return lemmas


def gather_snippets(original_keyword, results, snippets):
    for res in results:
        result_snippets = []
        content = res[-4]

        for match, _i in zip(re.finditer(original_keyword, content, re.IGNORECASE), range(5)):
            match_start = match.start()
            match_end = match.end()

            before = content[max(match_start - 80, 0): match_start]
            left_i = before.find(' ')

            after = content[match_end:match_end + 80]
            right_i = after.rfind(' ')

            result_snippets.append((f'...{before[left_i:]}', match.group(), f'{after[:right_i]}...'))
        snippets.append(result_snippets)
    return snippets