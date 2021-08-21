import ray
import os.path
from tqdm import tqdm
import pandas as pd
import yaml

from notebook_analyzer import Notebook
from examples_utils import log_exceptions, timing


with open("config.yml", "r") as yml_config:
    cfg = yaml.safe_load(yml_config)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sql_config = cfg['sql']

if sql_config['engine'] == 'postgresql':
    db_name = f'{sql_config["engine"]}://@{sql_config["host"]}/{sql_config["name"]}'
else:  # Engine = sqlite
    abs_path_to_db = os.path.join(BASE_DIR, sql_config["name"])
    db_name = f'{sql_config["engine"]}:///{abs_path_to_db}'

ray.init(num_cpus=cfg['ray_multiprocessing']['num_cpu'], log_to_driver=False)


@ray.remote
@log_exceptions
def get_notebook(notebook_id):
    nb = Notebook(notebook_id, db_name)
    return {'cells': nb.cells, 'metadata': nb.metadata, 'features': nb.features}


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

    notebooks_features = [notebook['features'] for notebook in notebooks if notebook]
    notebooks_cells = [notebook['cells'] for notebook in notebooks if notebook]
    notebook_metadata = [notebook['metadata'] for notebook in notebooks if notebook]

    print(pd.DataFrame(notebooks_features).sloc.head(15))


if __name__ == '__main__':
    main()
