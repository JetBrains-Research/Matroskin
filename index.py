import json
import time
import ray
from ray.util.multiprocessing import Pool
# from multiprocessing import Pool
# from tqdm import tqdm
import numpy as np
import progressbar
import os.path
import spacy
from spacy_langdetect import LanguageDetector
from spacy.language import Language

from Notebook import Notebook
from db_structures import create_db


@Language.factory('language_detector')
def language_detector(nlp, name):
    return LanguageDetector()


def set_nlp_model():
    nlp = spacy.load('en_core_web_sm')
    nlp.max_length = 2000000
    nlp.add_pipe('language_detector', last=True)
    return nlp


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_name = os.path.join(BASE_DIR, 'databases/testik.db.db')
config = {
    'code_instructions_count': True,
    'code_lines_count': True,
    'cell_language': True,
    'code_imports': True,
    'code_chars_count': True,
    'sentences_count': True,
    'unique_words': True,
    'content': True
}
nlp_functions = {'cell_language', 'sentences_count', 'unique_words'}
nlp = set_nlp_model() if sum([config[f] for f in nlp_functions]) else None
ray.init(num_cpus=4)


@ray.remote
def add_notebook(name):
    try:
        nb = Notebook(name, db_name)
        success = nb.add_nlp_model(nlp)
        log = nb.parse_features(config)
        rows = nb.write_to_db()
        return rows
    except Exception as e:
        with open("log.txt", "a") as f:
            f.write(f'{name}\t{type(e).__name__}\n')
        return 0


def get_notebook(notebook_id):
    nb = Notebook(notebook_id, db_name)
    success = nb.add_nlp_model(nlp)
    cells = nb.parse_features(config)
    print(f'{nb.metadata}\n{np.array(nb.cells)}')
    return nb


def main():
    get = False
    notebook_id = 12

    if get:
        nb = get_notebook(notebook_id)
        return

    with open('databases/ntbs_list.json', 'r') as fp:
        start, step = 0, 1000
        ntb_list = json.load(fp)[start:start+step]

    create_db(db_name)
    res = []

    result_ids = [add_notebook.remote(name) for name in ntb_list]
    for result_id in progressbar.progressbar(result_ids):
        res.append(ray.get(result_id))

    print('Finishing...')
    print('{} notebooks contain errors ({:.1f}%) '.format(
        len(res) - sum(res),
        (len(res) - sum(res)) / len(res) * 100
    ))


if __name__ == '__main__':
    start_time = time.time()
    main()
    print("--- {:.1f} seconds ---".format(time.time() - start_time))
