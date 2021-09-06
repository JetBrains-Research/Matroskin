from notebook_analyzer import Notebook
import yaml

with open("config.yml", "r") as yml_config:
    cfg = yaml.safe_load(yml_config)
    config = cfg['metrics']


def preprocessed_test_metrics(expected_metrics):
    """function that creates a single file with metrics
    that need to be tested in different files

    In:
    expected_metrics:
        List[ Tuple[FileName, Dict[Metric1: Value1, Metric2: Value2, ...], ...] ]

    Out:
    res:
        List[ Tuple[FileName, Metric1, Value1], ... ]

    """

    res = []
    for a, b in expected_metrics:
        for c, d in b.items():
            res.append((a, c, d))
    return res


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

