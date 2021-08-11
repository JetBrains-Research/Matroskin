import numpy as np
from sqlalchemy.orm.session import sessionmaker

from ..processors import MdProcessor
from ..processors import CodeProcessor
from ..connector import Connector
from .write_to_db import write_notebook_to_db


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
        self.cells = []

    def get_general_notebook_metrics(self):  # TODO hard function because of one pass
        cell_metrics = {
            'blank_lines_count': 0,
            'sloc': 0,
            'comments_count': 0,
            'classes': 0,
            'classes_size:': 0,
            'classes_comments': 0,
            'attributes_count': [],
            'new_methods_count': [],
            'override_methods_count': [],
        }

        count_markdown = True
        for i, cell in enumerate(self.cells):
            cell = flatten(cell)

            if cell['type'] == 'markdown' and count_markdown:
                cell_metrics['comments_count'] += len(cell['source'].split('\n')) + 1
                continue

            cell_metrics['blank_lines_count'] += cell['blank_lines_count']
            cell_metrics['sloc'] += cell['sloc']
            cell_metrics['comments_count'] += cell['comments_count']

            attributes_count = cell['classes_size'] - cell['new_methods_count'] - cell['override_methods_count']
            cell_metrics['attributes_count'].append(attributes_count)
            cell_metrics['new_methods_count'].append(cell['new_methods_count'])
            cell_metrics['override_methods_count'].append(cell['override_methods_count'])

            if cell['classes_size'] > 0:
                cell_metrics['classes'] += 1
                cell_metrics['classes'] += cell['classes_size']
                cell_metrics['classes_comments'] = cell['comments_count']

                if i != 0 and self.cells[i - 1]['type'] == 'markdown':
                    cell_metrics['classes_comments'] += len(self.cells[i - 1]['source'].split('\n')) + 1

        density = cell_metrics['comments_count'] / (cell_metrics['sloc'] + cell_metrics['comments_count'])
        comments_per_class = cell_metrics['classes_comments'] / max(cell_metrics['classes'], 1)
        notebook_metrics = {
            'blank_lines_count': cell_metrics['blank_lines_count'],
            'sloc': cell_metrics['sloc'],
            'comments_density': density,
            'comments_per_class': comments_per_class,
            'mean_attributes_count': np.mean(cell_metrics['attributes_count']),
            'mean_new_methods': np.mean(cell_metrics['new_methods_count']),
            'mean_override_methods': np.mean(cell_metrics['override_methods_count'])
        }

        return notebook_metrics

    def get_coupling_between_cells(self):
        cells_variables = [
            set(flatten(cell)['variables'].split(' '))
            for cell in self.cells
            if cell['type'] == 'code']

        coupling = 0
        for i, variables_i in enumerate(cells_variables):
            for j, variables_j in enumerate(cells_variables[i:]):
                tmp = variables_i.intersection(variables_j)
                coupling += len(tmp)
        return coupling

    def get_coupling_between_functions(self):
        cells_functions_and_inners = [
            flatten(cell)['functions_and_inners']
            for cell in self.cells
            if cell['type'] == 'code']

        functions = []
        for ss in cells_functions_and_inners:
            functions += [set(j[1].split(' '))
                          for j in [i.split(': ')
                                    for i in ss.split('\n') if ss]
                          if j[1] != '']

        coupling = 0
        for i, functions_i in enumerate(functions):
            for j, functions_j in enumerate(functions[i:]):
                tmp = functions_i.intersection(functions_j)
                coupling += len(tmp)
        return coupling

    def get_mean_coupling_between_methods(self):
        couplings = np.array([
            cell['mean_classes_coupling']
            for cell in self.cells
            if cell['type'] == 'code' and cell['mean_classes_coupling'] != 0
        ])
        default_coupling = 0
        return np.mean(couplings) if couplings.any() else default_coupling

    def get_functions_statistics(self):
        cells_functions_and_inners = [
            flatten(cell)['functions_and_inners']
            for cell in self.cells
            if cell['type'] == 'code']

        functions_uses = []
        for cfi in cells_functions_and_inners:
            lines = cfi.split('\n')
            for line in lines:
                function_name, inner_functions = line.split(': ') if line else '', ''
                inner_functions = inner_functions.split(' ') if inner_functions else []
                functions_uses += inner_functions

        defined_functions_uses = []
        for cell in filter(lambda cell: cell['type'] == 'code', self.cells):
            defined_functions_uses += cell['defined_functions'].split(' ')

        functions = set(functions_uses + defined_functions_uses)
        defined_functions = set(defined_functions_uses)

        stats = {
            'API_functions_count': len(functions) - len(defined_functions),
            'defined_functions_count': len(defined_functions),
            'API_functions_uses': len([f for f in functions_uses
                                       if f not in defined_functions]),
            'defined_functions_uses': len(defined_functions_uses)
        }
        return stats

    def get_mean_complexity_metrics(self):
        cells_metrics = {
            'ccn': [],
            'npavg': [],
            'halstead': []
        }
        for cell in filter(lambda cl: cl['type'] == 'code', self.cells):
            for metric in cells_metrics.keys():
                cells_metrics[metric].append(cell[metric])

        notebook_metrics = {}
        for metric in cells_metrics.keys():
            notebook_metrics[metric] = np.mean(cells_metrics[metric])

        return notebook_metrics

    def run_tasks(self, cells, config):
        self.cells = cells
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
    nlp = None

    def __init__(self, name, db_name=""):
        connector = Connector(name, db_name)

        self.engine = connector.engine
        self.metadata = connector.data.metadata
        self.cells = connector.data.cells

    def add_nlp_model(self, nlp):
        self.nlp = nlp

        return 1

    def write_to_db(self):
        session = sessionmaker(bind=self.engine)()

        with session as conn:
            self.metadata['id'] = write_notebook_to_db(conn, self.metadata, self.cells)

        return 1

    def run_tasks(self, config):
        for i, cell in enumerate(self.cells):
            self.cells[i] = self.processors[0](cell).process_cell(config['code']) \
                if cell['type'] == 'code' \
                else self.processors[1](cell, self.nlp).process_cell(config['markdown'])

        return self.cells

    def aggregate_tasks(self, config):
        features = self.aggregator.run_tasks(self.cells, config['notebook'])
        # ...
        # Write in DB
        # ...
        return features
