import json
import ray
import os.path
from tqdm import tqdm
import random

from matroskin import Notebook, create_db
from examples_utils import log_exceptions, get_config, get_db_name, timing


cfg = get_config("config.yml")
sql_config = cfg['sql']
metrics_config = cfg['metrics']

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_name = get_db_name(sql_config)
ray.init(num_cpus=cfg['ray_multiprocessing']['num_cpu'], log_to_driver=False)


@ray.remote
@log_exceptions
def add_notebook(name, idx):
    nb = Notebook(name, db_name)
    success = nb.add_nlp_model(None)
    log = nb.run_tasks(metrics_config)
    rows = nb.write_to_db()
    features = nb.aggregate_tasks(metrics_config)

    return rows


def main():
    ntb_list = []
    random.seed(cfg['data']['seed'])

    if cfg['data']['download_notebooks']:
        with open(cfg['data']['route_to_notebooks'], 'r') as file:
            full_ntb_list = json.load(file)
            full_ntb_list = [os.path.join(BASE_DIR, notebook_name)
                             for notebook_name in full_ntb_list]
            ntb_list += random.sample(full_ntb_list, cfg['data']['sample_size'])

    if cfg['data']['download_scripts']:
        with open(cfg['data']['route_to_scripts'], 'r') as file:
            full_script_list = json.load(file)
            full_script_list = [os.path.join(BASE_DIR, script_name)
                                for script_name in full_script_list]
            ntb_list += random.sample(full_script_list, cfg['data']['sample_size'])

    if cfg['db']['create_database']:
        create_db(db_name)

    res = []
    result_ids = [add_notebook.remote(name, idx) for idx, name in enumerate(ntb_list)]

    if len(result_ids) < cfg['data']['progress_bar_limit']:
        pbar = tqdm(result_ids)
        for result_id in pbar:
            res.append(ray.get(result_id))
            errors = len(res) - sum(res)
            errors_percentage = round(errors / len(result_ids) * 100, 1)
            pbar.set_postfix(errors=f'{errors} ({errors_percentage}%)')
    else:
        for result_id in result_ids:
            res.append(ray.get(result_id))

    # # Code to not use multiprocessing
    # pbar = tqdm(ntb_list)
    # for name in pbar:
    #     res.append(add_notebook(name))
    #     errors = len(res) - sum(res)
    #     errors_percentage = round(errors / len(ntb_list) * 100, 1)
    #     pbar.set_postfix(errors=f'{errors} ({errors_percentage}%)')
    #
    # print('Finishing...')


if __name__ == '__main__':
    main()
