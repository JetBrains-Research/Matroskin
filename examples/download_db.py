import ray
import os.path

from examples_utils import log_exceptions, set_nlp_model, timing
from notebook import Notebook


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


@log_exceptions
def get_notebook(notebook_id):
    nb = Notebook(notebook_id, db_name)
    success = nb.add_nlp_model(nlp)
    cells = nb.run_tasks(config)

    return nb


@timing
def main():
    notebook_ids = [1, 2]
    notebooks = []

    for idx in notebook_ids:
        notebooks.append(get_notebook(idx))

    for notebook in notebooks:
        print(notebook.metadata, notebook.cells)


if __name__ == '__main__':
    main()
