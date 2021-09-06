import pytest
from test_utils import get_aggregated_metrics, preprocessed_test_metrics

#
# Aggregated metrics
#
# notebook_cells_number
# md_cells_count
# code_cells_count
# notebook_imports
# unused_imports_total
#
# ccn
# halstead
# npavg
#
# sloc
# comments_count
# blank_lines_count
# classes
# classes_comments
# mean_new_methods
# mean_override_methods
# mean_attributes_count
# comments_density
# comments_per_class
#
# coupling_between_cells
# coupling_between_functions
# coupling_between_methods
#
# API_functions_count
# defined_functions_count
# API_functions_uses
# defined_functions_uses
# other_functions_uses


f = 'test_scripts/test_script.py'
metrics = {'code_cells_count': 1,
           'md_cells_count': 0,
           'blank_lines_count': 20,
           'classes': 1,
           'classes_comments': 22,
           'mean_new_methods': 8,
           'mean_attributes_count': 4,
           'coupling_between_functions': 5,
           'coupling_between_methods': 1,
           'defined_functions_count': 10,
           'API_functions_count': 9,
           'API_functions_uses': 16,
           'defined_functions_uses': 20,
           'other_functions_uses': 2
}


functions_test = 'test_scripts/test_functions.py'
metrics_functions_test = {
    'code_cells_count': 1,
    'md_cells_count': 0,
    'sloc': 15,
    'comments_count': 3,
    'comments_density': 3 / 18,
    'API_functions_count': 6,
    'defined_functions_count': 3,
    'API_functions_uses': 8,
    'defined_functions_uses': 0,
    'coupling_between_functions': 2
}

expected_metrics = [
    (functions_test, metrics_functions_test),
    (f, metrics)
]
res = preprocessed_test_metrics(expected_metrics)


@pytest.mark.parametrize('filename, metric_name, expected_metric_value', res)
def test_complexity_metrics(filename, metric_name, expected_metric_value):
    aggregated_metrics = get_aggregated_metrics(filename)
    print(f'{filename}\t{metric_name}')
    assert aggregated_metrics[metric_name] == expected_metric_value



