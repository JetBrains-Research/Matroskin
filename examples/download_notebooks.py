import json
import ray
import os.path
from tqdm import tqdm
import random
import yaml

from notebook_analyzer import Notebook, create_db
from examples_utils import log_exceptions, set_nlp_model, timing


with open("config.yml", "r") as yml_config:
    cfg = yaml.safe_load(yml_config)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sql_config = cfg['sql']

if sql_config['engine'] == 'postgresql':
    db_name = f'{sql_config["engine"]}://@{sql_config["host"]}/{sql_config["name"]}'
else:  # Engine = sqlite
    abs_path_to_db = os.path.join(BASE_DIR, sql_config["name"])
    db_name = f'{sql_config["engine"]}:////{abs_path_to_db}'
    print(db_name)
config = cfg['metrics']


nlp_functions = {'cell_language', 'sentences_count', 'unique_words'}
nlp = set_nlp_model() if sum([config['markdown'][f] for f in nlp_functions]) else None
ray.init(num_cpus=cfg['ray_multiprocessing']['num_cpu'], log_to_driver=False)


@ray.remote
@log_exceptions
def add_notebook(name, idx):
    nb = Notebook(name, db_name)
    success = nb.add_nlp_model(nlp)
    log = nb.run_tasks(config)
    rows = nb.write_to_db()
    features = nb.aggregate_tasks(config)

    return rows


@timing
def main():
    ntb_list = []
    random.seed(cfg['data']['seed'])

    if cfg['data']['download_notebooks']:
        with open(cfg['data']['route_to_notebooks'], 'r') as file:
            full_ntb_list = json.load(file)
            ntb_list += random.sample(full_ntb_list, cfg['data']['sample_size'])

    if cfg['data']['download_scripts']:
        with open(cfg['data']['route_to_scripts'], 'r') as file:
            full_script_list = file.read().splitlines()
            ntb_list += random.sample(full_script_list, cfg['data']['sample_size'])

    create_db(db_name)
    res = []
    result_ids = [add_notebook.remote(name, idx) for idx, name in enumerate(ntb_list)]

    if len(result_ids) < 50_000:
        pbar = tqdm(result_ids)
        for result_id in pbar:
            res.append(ray.get(result_id))
            errors = len(res) - sum(res)
            errors_percentage = round(errors / len(result_ids) * 100, 1)
            pbar.set_postfix(errors=f'{errors} ({errors_percentage}%)')
    else:
        for result_id in result_ids:
            res.append(ray.get(result_id))

    # # Code for not use multiprocessing
    # pbar = tqdm(ntb_list)
    # for idx, name in enumerate(pbar):
    #     res.append(add_notebook(name, idx))
    #     errors = len(res) - sum(res)
    #     errors_percentage = round(errors / len(ntb_list) * 100, 1)
    #     pbar.set_postfix(errors=f'{errors} ({errors_percentage}%)')

    print('Finishing...')


if __name__ == '__main__':
    main()
