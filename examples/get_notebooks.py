import ray
import os.path
from tqdm import tqdm

from notebook_analyzer import Notebook
from examples_utils import log_exceptions, set_nlp_model, timing

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_name = os.path.join(BASE_DIR, '../databases/aggregated.db')

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
ray.init(num_cpus=1, log_to_driver=False)


@ray.remote
@log_exceptions
def get_notebook(notebook_id):
    nb = Notebook(notebook_id, db_name)
    features = nb.aggregate_tasks(config)
    return {'cells': nb.cells, 'metadata': nb.metadata, 'features': features}


@timing
def main():
    notebook_ids = [i for i in range(1, 10)]
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

    notebooks = [notebook for notebook in notebooks if notebook]
    for notebook in notebooks:
        print(notebook['features'])


if __name__ == '__main__':
    main()
