import pytest
import yaml
from test_utils import  get_expected_metrics, get_aggregated_metrics

with open('testing_config.yml', "r") as yml_testing_config:
    testing_cfg = yaml.safe_load(yml_testing_config)
    directories = testing_cfg['directories']

expected_metrics = []
for directory in directories:
    expected_metrics += get_expected_metrics(directory)


@pytest.mark.parametrize('expected_result', expected_metrics)
def test_complexity_metrics(expected_result):
    with open('metrics_config.yml', "r") as yml_config:
        metrics_cfg = yaml.safe_load(yml_config)
        config = metrics_cfg['metrics']

    filename, metric_name, expected_metric_value = expected_result
    aggregated_metrics = get_aggregated_metrics(filename, config)
    
    print(f'{filename}\t{metric_name}')
    assert aggregated_metrics[metric_name] == expected_metric_value


