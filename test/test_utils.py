import os
import yaml
from matroskin import Notebook


def read_expected_results(directory=None):
    files = os.listdir(directory)
    expected_metrics = []
    for file in files:
        filename, file_extension = os.path.splitext(file)

        if file_extension == '.yml':
            with open(f'{directory}{file}', "r") as yml_config:
                cfg = yaml.safe_load(yml_config)
                metrics_config = cfg['metrics']
                python_file_type = '.py' if cfg['python_file_type'] == 'script' else '.ipynb'

            filename = filename if not directory else directory + filename
            expected_metrics.append((filename + python_file_type, metrics_config))

    return expected_metrics


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


def get_expected_metrics(directory):
    raw_metrics = read_expected_results(directory)
    preprocessed_metrics = preprocessed_test_metrics(raw_metrics)
    return preprocessed_metrics


def flatten(dictionary):
    output = dict()
    for key, value in dictionary.items():
        if isinstance(value, dict):
            output.update(flatten(value))
        else:
            output[key] = value

    return output


def get_aggregated_metrics(filename, config):
    nb = Notebook(filename)
    log = nb.run_tasks(config)
    features = nb.aggregate_tasks(config)
    return flatten(features)


def get_cells(filename, config):
    nb = Notebook(filename)
    log = nb.run_tasks(config)
    return nb.cells


def get_metrics():
    """
    A function that collects predicted and calculated
    metrics into a single array
    """

    with open('testing_config.yml', "r") as yml_testing_config:
        testing_cfg = yaml.safe_load(yml_testing_config)
        directories = testing_cfg['directories']

    with open('metrics_config.yml', "r") as yml_config:
        metrics_cfg = yaml.safe_load(yml_config)
        config = metrics_cfg['metrics']

    expected_metrics_list = []
    for directory in directories:
        expected_metrics_list += get_expected_metrics(directory)

    metrics = []
    unique_filenames = set([filename for filename, _, _ in expected_metrics_list])

    for filename in unique_filenames:
        aggregated_metrics = get_aggregated_metrics(filename, config)
        for expected_metrics in expected_metrics_list:
            if expected_metrics[0] == filename:
                metrics.append((expected_metrics, aggregated_metrics))

    return metrics


