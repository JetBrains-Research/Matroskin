import pandas as pd
from sqlalchemy.orm.session import sessionmaker
from itertools import combinations
from typing import Tuple, Set
import builtins
import types

from ..processors import MdProcessor
from ..processors import CodeProcessor
from ..connector import Connector
from .write_to_db import write_notebook_to_db, write_features_to_db


def flatten(dictionary):
    output = dict()
    for key, value in dictionary.items():
        if isinstance(value, dict):
            output.update(flatten(value))
        else:
            output[key] = value

    return output


class Aggregator:
    def __init__(self):
        self.task_mapping = {
            'general_metrics': self.get_general_notebook_metrics,
            'complexity_metrics': self.get_mean_complexity_metrics,
            'coupling_between_cells': self.get_coupling_between_cells,
            'coupling_between_functions': self.get_coupling_between_functions,
            'coupling_between_methods': self.get_mean_coupling_between_methods,
            'functions_statistics': self.get_functions_statistics
        }
        self.cells_df = None

    @staticmethod
    def get_sets_coupling(pair: Tuple[Set, Set]) -> int:
        a, b = pair
        return len(a.intersection(b))

    def get_general_notebook_metrics(self):
        df = self.cells_df

        notebook_metrics = {
            'notebook_cells_number': df.shape[0],
            'code_cells_count': sum(df.type == 'code'),
            'md_cells_count': sum(df.type == 'markdown'),
            'notebook_imports': " ".join(df.code_imports.replace('', float('NaN')).dropna()),
            'unused_imports_total': int(df.unused_imports_count.dropna().sum()),
            'sloc': int(df.sloc.sum()),
            'comments_count': max(int(df.comments_count.sum()), 0),
            'blank_lines_count': max(int(df.blank_lines_count.sum()), 0),
            'classes': int(
                df[df.classes_size > 0]. \
                classes_size. \
                dropna().astype(bool).sum()
            ),

            'classes_comments': int(
                df[df.classes_size > 0]. \
                comments_count. \
                dropna().sum()
            ),

            'mean_attributes_count': (df.classes_size
                                      - df.new_methods_count
                                      - df.override_methods_count).mean(),

            'mean_new_methods': df.new_methods_count.mean(),
            'mean_override_methods': df.override_methods_count.mean(),
            'comments_density': 0,
            'comments_per_class': 0,
        }

        count_markdown = True
        if count_markdown:
            default_length = 1
            notebook_metrics['comments_count'] += int(
                df[df.type == 'markdown']. \
                source. \
                apply(lambda lines: lines.count('\n') + default_length).sum()
            )

        notebook_metrics['comments_density'] = notebook_metrics['comments_count'] \
                                               / max((notebook_metrics['sloc'] + notebook_metrics['comments_count']), 1)

        notebook_metrics['comments_per_class'] = notebook_metrics['classes_comments'] \
                                                 / max(notebook_metrics['classes'], 1)

        return notebook_metrics

    def get_coupling_between_cells(self):
        pair_combination = 2
        cells_variables = self.cells_df.variables. \
            replace("", float("NaN")).dropna().apply(
            lambda variables_string: set(variables_string.split(' '))
        )

        coupling = 0
        for pair in combinations(cells_variables, pair_combination):
            coupling += self.get_sets_coupling(pair)

        return coupling

    def get_coupling_between_functions(self):
        """
        cells_df.inner_functions: Series[ List[ Set, ... , Set ] ]
        """

        pair_combination = 2
        inner_functions_sets = self.cells_df.inner_functions.explode().dropna()

        coupling = 0
        for pair in combinations(inner_functions_sets, pair_combination):
            coupling += self.get_sets_coupling(pair)

        return coupling

    def get_mean_coupling_between_methods(self):
        """
        Mean Coupling in cells which have methods in it
        """
        coupling_series = self.cells_df[self.cells_df.mean_classes_coupling > 0]. \
            mean_classes_coupling.dropna()

        mean_coupling = coupling_series.mean() if len(coupling_series) else 0
        return mean_coupling

    def get_functions_statistics(self):
        """
        cells_df.defined_functions: Series[ String['fun_1 fun_2 ... fun_n'] ]
        cells_df.used_functions: Series[ List[ String, ... , String ] ]
        cells_df.inner_functions: Series[ List[ Set, ... , Set ] ]

        Not great not terrible...
        """

        builtin_functions = [name for name, obj in vars(builtins).items()
                             if isinstance(obj, types.BuiltinFunctionType)]
        collection_functions_names = dir(list) + dir(dict) + dir(tuple)

        build_in_functions_set = set(builtin_functions + collection_functions_names)

        used_functions_series = self.cells_df.used_functions. \
            explode().replace('', float('Nan')).dropna()

        defined_functions_series = self.cells_df.defined_functions. \
            replace("", float('Nan')).dropna().apply(lambda line: line.split(' ')).explode()
        defined_functions_set = set(defined_functions_series)

        imported_entities = self.cells_df.imported_entities.explode().to_numpy()

        defined_functions_used = [function for function in used_functions_series
                                  if function in defined_functions_set]

        build_in_functions_used = [function for function in used_functions_series
                                   if function in build_in_functions_set]

        api_functions_used = [
            function['function']
            for function in self.cells_df.functions.explode().dropna()
            if (function['module'] in imported_entities or
                function['function'] in imported_entities)
        ]
        api_functions_set = set(api_functions_used)

        other_functions_used = [function for function in used_functions_series
                                if (function not in defined_functions_set
                                    and function not in api_functions_set
                                    and function not in build_in_functions_set)]

        # if len(api_functions_used) == 2:
        #     print(api_functions_used)
        #     print(self.cells_df.source.to_numpy()[0])

        stats = {
            'API_functions_count': len(api_functions_set),
            'defined_functions_count': len(defined_functions_set),
            'API_functions_uses': len(api_functions_used),
            'defined_functions_uses': len(defined_functions_used),
            'build_in_functions_count': len(set(build_in_functions_used)),
            'build_in_functions_uses': len(build_in_functions_used),
            'other_functions_uses': len(other_functions_used)
        }

        return stats

    def get_mean_complexity_metrics(self):
        cells_metrics = ['ccn', 'npavg', 'halstead']
        notebook_metrics = {}

        for metric in cells_metrics:
            notebook_metrics[metric] = self.cells_df[metric].mean()

        return notebook_metrics

    def run_tasks(self, cells, config):
        self.cells_df = pd.DataFrame(cells).set_index('num').sort_index()

        functions = [
            function for function, executing in config.items()
            if (function in self.task_mapping.keys() and executing is True)
        ]

        features = {}
        for function in functions:
            features[function] = self.task_mapping[function]()

        return features


class Notebook(object):
    processors = [CodeProcessor, MdProcessor]
    aggregator = Aggregator()
    cells = []
    metadata = {}
    features = {}
    nlp = None

    def __init__(self, name, db_name=""):
        connector = Connector(name, db_name)

        self.engine = connector.engine
        self.metadata = connector.data.metadata
        self.cells = connector.data.cells
        self.features = connector.data.features

    def add_nlp_model(self, nlp):
        self.nlp = nlp

        return 1

    def write_to_db(self):
        session = sessionmaker(bind=self.engine)()

        with session as conn:
            self.metadata['id'] = write_notebook_to_db(conn, self.metadata, self.cells)

        return 1

    def write_aggregated_to_db(self):
        session = sessionmaker(bind=self.engine)()
        with session as conn:
            flatten_features = write_features_to_db(conn, self.metadata, self.features)

        return flatten_features

    def run_tasks(self, config):
        for i, cell in enumerate(self.cells):
            self.cells[i] = self.processors[0](cell).process_cell(config['code']) \
                if cell['type'] == 'code' \
                else self.processors[1](cell, self.nlp).process_cell(config['markdown'])

        return self.cells

    def aggregate_tasks(self, config):
        flatten_cells = [flatten(cell) for cell in self.cells]
        self.features = self.aggregator.run_tasks(flatten_cells, config['notebook'])

        # if self.engine:
        #     session = sessionmaker(bind=self.engine)()
        #     with session as conn:
        #         flatten_features = write_features_to_db(conn, self.metadata, self.features)
        #         return flatten_features

        return self.features
