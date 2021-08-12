import json
import ray
import os.path
from tqdm import tqdm

from notebook_analyzer import Notebook, create_db
from examples_utils import log_exceptions, set_nlp_model, timing

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_name = os.path.join(BASE_DIR, '../databases/aggregated_1k_scripts.db')
config = {
    'markdown': {
        'cell_language': False,
        'sentences_count': False,
        'unique_words': False,
        'content': False,
    },
    'code': {
        'code_instructions_count': True,
        'code_imports': True,
        'code_chars_count': True,
        'metrics': True
    },
    'notebook': {
            'general_metrics': True,
            'complexity_metrics': True,
            'coupling_between_cells': True,
            'coupling_between_functions': True,
            'coupling_between_methods': True,
            'functions_statistics': True
        }
}


nlp_functions = {'cell_language', 'sentences_count', 'unique_words'}
nlp = set_nlp_model() if sum([config['markdown'][f] for f in nlp_functions]) else None
ray.init(num_cpus=6, log_to_driver=False)


@ray.remote
def add_notebook(name):
    nb = Notebook(name, db_name)
    success = nb.add_nlp_model(nlp)
    log = nb.run_tasks(config)
    rows = nb.write_to_db()
    features = nb.aggregate_tasks(config)

    return rows


@timing
def main():
    scripts_input = False
    start, step = 5_900_000, 20  # 5_400_000, 1000

    if not scripts_input:
        with open('../databases/ntbs_list.json', 'r') as file:
            ntb_list = json.load(file)[start:start+step]
    else:
        with open('../databases/20kk_scripts.txt', 'r') as file:
            ntb_list = file.read().split('\n')[start:start+step]

    create_db(db_name)
    res = []
    result_ids = [add_notebook.remote(name) for name in ntb_list]

    pbar = tqdm(result_ids)
    for result_id in pbar:
        res.append(ray.get(result_id))
        errors = len(res) - sum(res)
        errors_percentage = round(errors / len(result_ids) * 100, 1)
        pbar.set_postfix(errors=f'{errors} ({errors_percentage}%)')

    print('Finishing...')
    print(f'{errors} notebooks contain errors ({errors_percentage}%) ')


if __name__ == '__main__':
    main()
