import pytest
from test_utils import get_metrics


@pytest.mark.parametrize('metrics', get_metrics())
def test_complexity_metrics(metrics):
    """
    Testing all files from configured directories

    metrics: Tuple[
                Tuple[ FileName: String, MetricName: String, ExpectedValue: Any ],
                Dict[ MetricName1: Value1, ... ]
             ]
    """

    expected_result, aggregated_metrics = metrics
    filename, metric_name, expected_metric_value = expected_result

    print(f'{filename}\t{metric_name}')
    assert aggregated_metrics[metric_name] == expected_metric_value


