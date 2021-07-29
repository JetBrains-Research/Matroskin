import gast as ast
from radon.raw import analyze

from processors import CellProcessor
from processors import metrics_utils
from processors.node_visitor import ComplexityVisitor, OOPVisitor


class CodeProcessor(CellProcessor):
    task_mapping = {}
    visitors = [
        ComplexityVisitor,
        OOPVisitor
    ]

    def __init__(self, cell_data):
        super().__init__(cell_data)

        self.task_mapping = {
            'code_instructions_count': self.get_num_instructions,
            'code_imports': self.get_imports,
            'code_chars_count': self.get_chars_of_code,
            'metrics': self.get_general_metrics
        }

    def process_cell(self, tasks) -> dict:
        for function in {
            k: v
            for k, v in tasks.items()
            if (v and k in self.task_mapping.keys())
        }:
            self.cell[function] = self.task_mapping[function](self.cell)
        return self.cell

    def get_num_instructions(self, cell):
        cell_ast = metrics_utils.get_ast(cell['source'])
        return self.depth_ast(cell_ast)

    def depth_ast(self, cell_ast):
        return 1 + max(
            [self.depth_ast(child)
             for child in ast.iter_child_nodes(cell_ast)],
            default=0)

    @staticmethod
    def get_chars_of_code(cell):
        return len(cell['source'])

    def get_imports(self, cell):
        cell_ast = metrics_utils.get_ast(cell['source'])
        complexity_visitor = self.visitors[0]()
        complexity_visitor.visit(cell_ast)

        return " ".join(complexity_visitor.get_imports())

    def get_general_metrics(self, cell):
        source = cell['source']
        metrics = {}

        try:
            res = analyze(source)
            metrics['sloc'] = res.sloc
            metrics['comments_count'] = res.comments + res.multi
        except SyntaxError:
            metrics['sloc'] = -1
            metrics['comments_count'] = -1

        ast_cell = metrics_utils.get_ast(source)  # ast.parse(source)

        complexity_visitor = self.visitors[0]()
        oop_visitor = self.visitors[1]()
        complexity_visitor.visit(ast_cell)
        oop_visitor.visit(ast_cell)
        classes_parameters = oop_visitor.get_classes_parameters()

        new_methods_count = 0
        override_methods_count = 0
        for params in classes_parameters:
            new_methods_count += len(params['new_methods'])
            override_methods_count += len(params['override_methods'])

        metrics['ccn'] = metrics_utils.get_cyclomatic_complexity(source)
        metrics['operation_complexity'] = complexity_visitor.operation_complexity
        metrics['classes_size'] = oop_visitor.classes_size
        metrics['npavg'] = complexity_visitor.npavg
        metrics['functions_count'] = len(complexity_visitor.functions)
        metrics['override_methods_count'] = override_methods_count  # len(oop_visitor.override_methods)
        metrics['new_methods_count'] = new_methods_count  # len(oop_visitor.new_methods)

        return metrics
