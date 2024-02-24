import os
import sqlite3


class BmmBirosagDB:

    def __init__(self, databasename) -> None:
        self.databasename = databasename
        if not os.path.exists(self.databasename):
            self.connection = sqlite3.connect(self.databasename)
            c = self.connection.cursor()
            # JSON keys to Columns:
            # - Azonosito: egyedi_azonosito
            # - MeghozoBirosag: birosag
            # - Kollegium: kollegium
            # - JogTerulet: jogterulet
            # - KapcsolodoHatarozatok: -
            # - Jogszabalyhelyek: -
            # - HatarozatEve: year
            # - Szoveg: - content
            # - Rezume (elvi tartalom): rezume
            c.execute('''CREATE TABLE IF NOT EXISTS hatarozatok (
                            egyedi_azonosito TEXT,
                            azonosito TEXT,
                            birosag TEXT,
                            kollegium TEXT,
                            jogterulet TEXT,
                            year TEXT,
                            jogszabalyhelyek TEXT,
                            rezume TEXT,
                            index_id TEXT,
                            url TEXT,
                            download_url TEXT,
                            content TEXT,
                            lemmacontent TEXT,
                            scrape_date TEXT,
                            isnew INTEGER)''')

            c.execute('''CREATE VIRTUAL TABLE IF NOT EXISTS hatarozatok_fts 
                            USING FTS5 (egyedi_azonosito UNINDEXED, content, lemmacontent, rezume,
                             tokenize="unicode61 remove_diacritics 2")''')

            c.execute('''CREATE TRIGGER hatarozatok_ai AFTER INSERT ON hatarozatok BEGIN
                            INSERT INTO hatarozatok_fts(egyedi_azonosito, content, lemmacontent, rezume) 
                            VALUES (new.egyedi_azonosito, new.content, new.lemmacontent, new.rezume);
                        END;''')

            c.execute('''CREATE TRIGGER hatarozatok_ad AFTER DELETE ON hatarozatok BEGIN
                            INSERT INTO hatarozatok_fts(hatarozatok_fts, egyedi_azonosito, content, lemmacontent, rezume) 
                                VALUES('delete', old.egyedi_azonosito, old.content, old.lemmacontent, old.rezume);
                        END;''')

            self.commit_connection()
            c.close()
        else:
            self.connection = sqlite3.connect(self.databasename)

    def close_connection(self):
        self.connection.close()

    def commit_connection(self):
        self.connection.commit()

    def get_hatarozat(self, egyedi_azonosito):
        c = self.connection.cursor()

        c.execute('SELECT * FROM contracts WHERE egyedi_azonosito=?', (egyedi_azonosito,))
        res = c.fetchone()

        c.close()
        return res

    def save_hatarozat(self, entry):
        c = self.connection.cursor()

        c.execute(
            'INSERT INTO hatarozatok (egyedi_azonosito, azonosito, birosag, kollegium, jogterulet, year, '
            'jogszabalyhelyek, rezume, index_id, url, download_url, content, lemmacontent, scrape_date, isnew) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)',
            (entry['EgyediAzonosito'], entry['Azonosito'], entry['MeghozoBirosag'], entry['Kollegium'], entry['JogTerulet'],
             entry['HatarozatEve'], entry['Jogszabalyhelyek'], entry['Rezume'], entry['IndexId'], entry['url'],
             entry['download_url'], entry['content'], entry['lemmacontent'], entry['scrape_date']))

        c.close()

    def clear_is_new(self, egyedi_azonosito):
        c = self.connection.cursor()

        c.execute('UPDATE hatarozatok SET isnew=0 WHERE number=?', (egyedi_azonosito,))

        c.close()

    def search_records(self, keyword):
        c = self.connection.cursor()

        c.execute('SELECT * FROM hatarozatok WHERE isnew=1 AND egyedi_azonosito IN '
                  '(SELECT egyedi_azonosito FROM hatarozatok_fts WHERE hatarozatok_fts MATCH ?)',
                  (keyword,))

        results = c.fetchall()
        c.close()
        return results

    def get_all_new(self):
        """
        :return: tuple of results. (egyedi_azonosito, azonosito, birosag, kollegium, jogterulet, year,
                                    jogszabalyhelyek, rezume, index_id, url, download_url, content, lemmacontent,
                                    scrape_date, isnew)
        """
        c = self.connection.cursor()

        c.execute('SELECT * FROM hatarozatok WHERE isnew=1')

        results = c.fetchall()
        c.close()
        return results

    def get_existing_azonosito_set(self):
        c = self.connection.cursor()

        c.execute('SELECT egyedi_azonosito FROM hatarozatok')

        results = c.fetchall()
        c.close()
        return set(results)
