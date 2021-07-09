import json
import time
from multiprocessing import Pool
from tqdm import tqdm
import numpy as np
import os.path

from Notebook import Notebook
from db_structures import create_db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_name = os.path.join(BASE_DIR, 'test.db')
config = {
    'code_instructions_count': False,
    'code_lines_count': False,
    'cell_language': True,
    'code_imports': False,
    'code_chars_count': True,
    'sentences_count': False,
    'unique_words': False,
    'content': False
}


def add_notebook(name):
    try:
        nb = Notebook(name, db_name)
        log = nb.parse_features(config)
        rows = nb.write_to_db()
        return rows
    except Exception as e:
        with open("log.txt", "a") as f:
            f.write(f'{name}\t{type(e).__name__}\n')
            # f.write(f'{name}\t{str(e)}\n')
        return 0


def get_notebook(notebook_id):
    nb = Notebook(notebook_id, db_name)
    cells = nb.parse_features(config)
    print(f'{nb.metadata}\n{np.array(nb.cells)}')
    return nb


def main():
    get = False
    notebook_id = 2

    if get:
        nb = get_notebook(notebook_id)
        return

    with open('ntbs_list.json', 'r') as fp:
        start, step = 1000, 5
        ntb_list = json.load(fp)[start:start+step]

    create_db(db_name)
    res = []
    with tqdm(total=len(ntb_list)) as pbar:
        with Pool(processes=5) as pool:
            for result in pool.imap_unordered(add_notebook, ntb_list,
                                              chunksize=1):
                res.append(result)
                pbar.update(1)

    print('Finishing...')
    print('{} notebooks contain errors ({:.1f}%) '.format(
        len(res) - sum(res),
        (len(res) - sum(res)) / len(res) * 100
    ))


if __name__ == '__main__':
    start_time = time.time()
    main()
    print("--- {:.1f} seconds ---".format(time.time() - start_time))
