import json
import time
from multiprocessing import Pool
from tqdm import tqdm
import numpy as np
from Notebook import Notebook
from db_structures import create_db

db_name = 'test.db'

def add_notebook(name):
    #config = {'get_lines_of_code': True, 'get_cell_language': False}
    config = {
        'code_instructions_count': True,
        'code_lines_count': True,
        'cell_language': False,
        'code_imports': True}

    try:
        nb = Notebook(name)
        log = nb.parse_features(config)
        rows = nb.write_to_db(db_name)
        return rows
    except Exception as e:
        with open("log.txt", "a") as f:
            f.write(f'{name}:\t{repr(e)}\n')
        return 0


def main():
    get = True

    if get:
        notebook_id = 33
        nb = Notebook(notebook_id, db_name)
        print(nb.metadata)
        print(np.array(nb.cells))
        return

    with open('ntbs_list.json', 'r') as fp:
        start, step = 0, 15
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
    print(res)
    print('{} notebooks contain errors ({:.1f}%) '.format(
        len(res) - sum(res),
        (len(res) - sum(res)) / len(res) * 100
    ))


if __name__ == '__main__':
    start_time = time.time()
    main()
    print("--- {:.1f} seconds ---".format(time.time() - start_time))
