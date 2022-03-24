import ray
import os.path
from tqdm import tqdm
import pandas as pd

from matroskin import Notebook
from examples_utils import log_exceptions, get_config, get_db_name, timing


cfg = get_config("config.yml")
sql_config = cfg['sql']
metrics_config = cfg['metrics']

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_name = get_db_name(sql_config)

ray.init(num_cpus=cfg['ray_multiprocessing']['num_cpu'], log_to_driver=False)


@ray.remote
def get_notebook(notebook_id):
    res = {
        'metadata': None,
        'cells': None,
        'features': None
    }

    try:
        nb = Notebook(notebook_id, db_name)
        res['metadata'] = nb.metadata
        res['cells'] = nb.cells
        res['features'] = nb.features
        return res

    except Exception as e:
        return None


@timing
def main():
    notebook_ids = [i for i in range(1, cfg['data']['sample_size'] + 1)]
    multiprocessing = True
    notebooks = []

    if multiprocessing:
        result_ids = [get_notebook.remote(idx) for idx in notebook_ids]

        pbar = tqdm(result_ids)
        for result_id in pbar:
            notebooks.append(ray.get(result_id))

    else:
        pbar = tqdm(notebook_ids)
        for idx in pbar:
            notebooks.append(get_notebook(idx))

    notebooks_features = [ntb['features'] for ntb in notebooks if ntb]
    notebooks_cells = [ntb['cells'] for ntb in notebooks if ntb]
    notebook_metadata = [ntb['metadata'] for ntb in notebooks if ntb]

    print(pd.DataFrame(notebooks_features).sloc.head())


if __name__ == '__main__':
    main()
