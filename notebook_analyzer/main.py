import json
import ray
import os.path
from tqdm import tqdm

from notebook import Notebook
from connector import create_db
from examples import log_exceptions, set_nlp_model, timing

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_name = os.path.join(BASE_DIR, 'databases/testik_new.db')

config = {
    'markdown': {
        'cell_language': True,
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
@log_exceptions
def add_notebook(name):
    nb = Notebook(name, db_name)
    success = nb.add_nlp_model(nlp)
    log = nb.run_tasks(config)
    rows = nb.write_to_db()
    return rows


@timing
def main():

    with open('databases/ntbs_list.json', 'r') as fp:
        start, step = 1_800_000, 50
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
    main()
