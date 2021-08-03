import gast as ast
from typing import List, Dict
from radon.visitors import ComplexityVisitor as CyclomaticComplexityVisitor

operation_complexity_weight = {
    'branching': 0.5,
    'binary_op': 2,
    'assign': 0.5,
    'call': 5
}


class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.operation_complexity = 0
        self.imports = []
        self.functions = []

    def visit(self, node):
        super().visit(node)

        if isinstance(node, (ast.AsyncFor, ast.While, ast.If,
                             ast.With, ast.AsyncWith)):
            self.operation_complexity += operation_complexity_weight['branching']

        return self.operation_complexity

    def visit_BinOp(self, node):
        self.operation_complexity += operation_complexity_weight['binary_op']

    def visit_Assign(self, node):
        self.operation_complexity += operation_complexity_weight['assign']

    def visit_Call(self, node):
        if isinstance(node.func, (ast.Attribute, ast.Call)):
            self.operation_complexity += operation_complexity_weight['call']
        if isinstance(node, ast.Call):
            self.functions.append({'function': node, 'args': node.args})
        else:
            self.functions.append({'function': node, 'args': node.args.args})

    def visit_Import(self, node):
        self.imports += [alias.name for alias in node.names]

    def visit_ImportFrom(self, node):
        self.imports += [f'{node.module}.{alias.name}'
                         for alias in node.names]

    def get_imports(self):
        return self.imports

    def get_cyclomatic_complexity(self, cell_source):
        refactored_cell = 'def _():\n\tpass\n' \
                          + '\n'.join(['\t' + line
                                       for line in cell_source.split('\n')]) \
            if cell_source else ''
        if not refactored_cell:
            return 0

        try:
            cyclomatic_visitor = CyclomaticComplexityVisitor.from_code(refactored_cell)
        except SyntaxError as e:
            source = cell_source.splitlines()
            del source[e.lineno - 1 - 3]
            source = '\n'.join(source)
            return self.get_cyclomatic_complexity(source)

        func_cell = cyclomatic_visitor.functions[0]
        cell_complexity = func_cell.complexity

        for func in func_cell.closures:
            cell_complexity += func.complexity

        return cell_complexity

    @property
    def npavg(self):
        """Get average Number of Parameters per function and functions count"""
        if not self.functions:
            return 0

        args = 0
        for f in self.functions:
            args += len(f['args'])
        return args / len(self.functions)


class ClassVisitor(ast.NodeVisitor):
    def __init__(self):
        self.methods = set()
        self.attributes = set()

    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Name):
            self.attributes.add(node.targets[0].id)

    def visit_Attribute(self, node):
        if isinstance(node.ctx, ast.Store) \
                and isinstance(node.value, ast.Name) \
                and node.value.id == 'self':
            self.attributes.add(node.attr)

    def visit_FunctionDef(self, node):
        self.methods.add(node.name)

    @property
    def size(self):
        return len(self.methods) + len(self.attributes)


class OOPVisitor(ast.NodeVisitor):
    def __init__(self):
        self.classes = []
        self.override_methods = []
        self.new_methods = []
        self.attributes_count = 0

    def visit_ClassDef(self, node):
        self.classes.append(node)

    @staticmethod
    def get_class_entities(cls):
        visitor = ClassVisitor()
        visitor.visit(cls)

        return {
            'methods': visitor.methods,
            'attributes': visitor.attributes,
            'size': visitor.size
        }

    @property
    def classes_size(self):
        size = 0
        for cls in self.classes:
            size += len(self.get_class_entities(cls)['methods'])
        return size

    def get_classes_parameters(self) -> List[Dict]:
        res = []

        for cls in self.classes:

            child_methods = self.get_class_entities(cls)['methods']

            if len(cls.bases) and isinstance(cls.bases[0], ast.Attribute) \
                    and isinstance(cls.bases[0].value, ast.Name):
                parent_name = cls.bases[0].value.id

            elif len(cls.bases) and isinstance(cls.bases[0], ast.Name):
                parent_name = cls.bases[0].id
            else:
                parent_name = None

            parent = [cls for cls in self.classes
                      if cls.name == parent_name] if parent_name else None
            parent = parent if parent else None

            if not parent:
                res.append({
                    'override_methods': {},
                    'new_methods': child_methods
                })
                continue

            parent_methods = self.get_class_entities(parent[0])['methods']

            get_from_parent = child_methods.intersection(parent_methods)
            done_by_child = child_methods.difference(parent_methods)
            self.override_methods += get_from_parent
            self.new_methods += done_by_child

            res.append({
                'override_methods': get_from_parent,
                'new_methods': done_by_child
            })

        return res
