import gast as ast
from radon.raw import analyze

from .cell_processor import CellProcessor
from .node_visitor import ComplexityVisitor, OOPVisitor


def get_ast(cell_source):
    try:
        code_ast = ast.parse(cell_source)
        return code_ast
    except SyntaxError as e:  # TODO: reconsider a way for handling magic functions
        code_string = cell_source.splitlines()
        del code_string[e.lineno - 1]
        code_string = '\n'.join(code_string)
        return get_ast(code_string)


class CodeProcessor(CellProcessor):
    visitors = [
        ComplexityVisitor,
        OOPVisitor
    ]

    def __init__(self, cell_data):
        self.cell = cell_data

        self.task_mapping = {
            'code_instructions_count': self.get_num_instructions,
            'code_imports': self.get_imports,
            'code_chars_count': self.get_chars_of_code,
            'metrics': self.get_general_metrics
        }

        self.cell['ast'] = get_ast(self.cell['source'])
        self.refactored_cell_ast = get_ast(self.__get_refactored_cell())

        self.complexity_visitor = ComplexityVisitor()
        self.oop_visitor = OOPVisitor()
        self.complexity_visitor.visit(self.cell['ast'])
        self.oop_visitor.visit(self.cell['ast'])

    def get_num_instructions(self, cell):
        return self.depth_ast(cell['ast'])

    def depth_ast(self, cell_ast):
        default_depth = 1
        all_depths = [self.depth_ast(child)
                      for child in ast.iter_child_nodes(cell_ast)]
        depth = default_depth + max(all_depths, default=0)
        return depth

    def __get_refactored_cell(self):
        refactored_cell = 'def a():\n\tpass\n' \
                          + '\n'.join(['\t' + line
                                       for line in self.cell['source'].split('\n') if ('import' not in line)])
        return refactored_cell

    @staticmethod
    def get_chars_of_code(cell):
        return len(cell['source'])

    def get_imports(self, cell):
        complexity_visitor = self.visitors[0]()
        complexity_visitor.visit(cell['ast'])

        return " ".join(complexity_visitor.get_imports())

    def get_oop_metrics(self):
        non_public_methods_count = self.oop_visitor.get_non_public_methods_count()
        classes_parameters = self.oop_visitor.get_classes_parameters()

        new_methods_count = 0
        override_methods_count = 0
        for params in classes_parameters:
            new_methods_count += len(params['new_methods'])
            override_methods_count += len(params['override_methods'])

        oop_metrics = {
            'new_methods_count': new_methods_count,
            'override_methods_count': override_methods_count,
            'private_methods_count': non_public_methods_count['private_methods_count'],
            'protected_methods_count': non_public_methods_count['protected_methods_count'],
            'classes_size': self.oop_visitor.classes_size,
            'mean_classes_coupling': self.oop_visitor.get_mean_methods_coupling()
        }
        return oop_metrics

    def get_complexity_metrics(self):
        complexity_metrics = {
            'ccn': self.complexity_visitor.get_cyclomatic_complexity(self.refactored_cell_ast),
            'halstead': self.complexity_visitor.get_halstead_complexity(self.refactored_cell_ast),
            'operation_complexity': self.complexity_visitor.operation_complexity,
            'npavg': self.complexity_visitor.npavg,
            'functions_count': len(self.complexity_visitor.functions),
            'variables': " ".join(list(self.complexity_visitor.variables)),
            'defined_functions': " ".join(list(self.complexity_visitor.defined_functions)),
            'inner_functions': self.complexity_visitor.inner_functions,
            'used_functions': self.complexity_visitor.used_functions,
            'imported_entities': self.complexity_visitor.imported_entities,
            'functions': self.complexity_visitor.functions_and_args,
            'unused_imports_count': 0  # len(self.complexity_visitor.get_unused_imports(self.cell['ast']))
        }
        return complexity_metrics

    def get_radon_metrics(self, cell_source):
        radon_metrics = {'sloc': -1, 'comments_count': -1}
        try:
            res = analyze(cell_source)
            radon_metrics['sloc'] = res.sloc
            radon_metrics['comments_count'] = res.comments + res.multi
            radon_metrics['blank_lines_count'] = res.blank
            return radon_metrics
        except SyntaxError:
            return radon_metrics

    def get_general_metrics(self, cell):
        cell_source = cell['source']

        radon_metrics = self.get_radon_metrics(cell_source)
        complexity_metrics = self.get_complexity_metrics()
        oop_metrics = self.get_oop_metrics()

        metrics = {**radon_metrics, **complexity_metrics, **oop_metrics}

        return metrics
