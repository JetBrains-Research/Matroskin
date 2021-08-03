import json
import time
import ray
from tqdm import tqdm
import os.path
import spacy
from spacy_langdetect import LanguageDetector
from spacy.language import Language

from notebook import Notebook
from connector import create_db


@Language.factory('language_detector')
def language_detector(nlp, name):
    return LanguageDetector()


def set_nlp_model():
    nlp = spacy.load('en_core_web_sm')
    nlp.max_length = 2000000
    nlp.add_pipe('language_detector', last=True)
    return nlp


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_name = os.path.join(BASE_DIR, '../databases/test.db')

config = {
    'markdown': {
        'cell_language': False,
        'sentences_count': False,
        'unique_words': False,
        'content': True,
    },
    'code': {
        'code_instructions_count': True,
        'code_imports': True,
        'code_chars_count': True,
        'metrics': True
    }
}
nlp_functions = {'cell_language', 'sentences_count', 'unique_words'}
nlp = set_nlp_model() if sum([config['markdown'][f] for f in nlp_functions]) else None
ray.init(num_cpus=6)


@ray.remote
def add_notebook(name):
    try:
        nb = Notebook(name, db_name)
        success = nb.add_nlp_model(nlp)
        log = nb.run_tasks(config)
        rows = nb.write_to_db()
        return rows
    except Exception as e:
        with open("../logs/log.txt", "a") as f:
            f.write(f'{name}\t{type(e).__name__}\n')
        return 0


def get_notebook(notebook_id):
    nb = Notebook(notebook_id, db_name)
    success = nb.add_nlp_model(nlp)
    cells = nb.run_tasks(config)
    print(f'{nb.metadata}\n{nb.cells}')
    return nb


def main():
    get = False
    notebook_id = 16

    if get:
        nb = get_notebook(notebook_id)
        # metrics = nb.metrics
        # print(metrics)
        return

    with open('../databases/ntbs_list.json', 'r') as fp:
        start, step = 1_100_000, 50
        ntb_list = json.load(fp)[start:start+step]

    create_db(db_name)
    res = []
    result_ids = [add_notebook.remote(name) for name in ntb_list]

    pbar = tqdm(result_ids)
    for result_id in pbar:
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
