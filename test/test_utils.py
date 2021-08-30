from notebook_analyzer import Notebook
import yaml

with open("config.yml", "r") as yml_config:
    cfg = yaml.safe_load(yml_config)
    config = cfg['metrics']


def flatten(dictionary):
    output = dict()
    for key, value in dictionary.items():
        if isinstance(value, dict):
            output.update(flatten(value))
        else:
            output[key] = value

    return output


def get_aggregated_metrics(filename):
    nb = Notebook(filename)
    log = nb.run_tasks(config)
    features = nb.aggregate_tasks(config)
    return flatten(features)


def get_cells(filename):
    nb = Notebook(filename)
    log = nb.run_tasks(config)
    return nb.cells

