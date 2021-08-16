import gast as ast
from typing import List, Dict, Tuple, Set
from itertools import combinations
from radon.metrics import h_visit_ast
from radon.complexity import cc_visit_ast, add_inner_blocks
import beniget

operation_complexity_weight = {
    'branching': 0.5,
    'binary_op': 2,
    'assign': 0.5,
    'call': 5
}


class GetInnerUsedFunctions(ast.NodeVisitor):
    def __init__(self):
        self.inner_functions = set()
        self.used_functions = []

    def visit(self, tree):
        ast.NodeVisitor.visit(self, tree)
        return {
            'used_functions': self.used_functions,
            'inner_functions': self.inner_functions
        }

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.inner_functions.add(node.func.id)
            self.used_functions.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.inner_functions.add(node.func.attr)
            self.used_functions.append(node.func.attr)


class FunctionDefsVisitor(ast.NodeVisitor):
    def __init__(self):
        self.defined_functions = set([])
        self.inner_functions = []
        self.used_functions = []

    def visit(self, tree):
        ast.NodeVisitor.visit(self, tree)
        return {'defined_functions': self.defined_functions,
                'inner_functions': self.inner_functions}

    def visit_FunctionDef(self, node):
        v = GetInnerUsedFunctions()

        self.defined_functions.add(node.name)
        functions = v.visit(node)
        self.inner_functions.append(functions['inner_functions'])
        self.used_functions = functions['used_functions']


class GetImports(ast.NodeVisitor):
    def __init__(self):
        self.imports = []
        self.aliases = []
        super().__init__()

    def visit(self, node):
        super().visit(node)

        return self.imports

    def visit_Import(self, node):
        self.imports += [alias.name for alias in node.names]
        self.aliases += [alias for alias in node.names]

    def visit_ImportFrom(self, node):
        self.imports += [f'{alias.name}'
                         for alias in node.names]
        self.aliases += [alias for alias in node.names]


class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.operation_complexity = 0
        self.imports = []
        self.functions = []
        self.variables = set([])
        self.defined_functions = []
        self.inner_functions = []
        self.used_functions = []
        self.import_aliases = []

    def visit(self, node):
        super().visit(node)

        functions_visitor = FunctionDefsVisitor()
        functions_visitor.visit(node)
        self.defined_functions = functions_visitor.defined_functions
        self.inner_functions = functions_visitor.inner_functions
        self.used_functions += functions_visitor.used_functions

        if isinstance(node, (ast.AsyncFor, ast.While, ast.If,
                             ast.With, ast.AsyncWith)):
            self.operation_complexity += operation_complexity_weight['branching']

        return self.operation_complexity

    def visit_BinOp(self, node):
        self.operation_complexity += operation_complexity_weight['binary_op']

    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Name):
            self.variables.add(node.targets[0].id)
        self.operation_complexity += operation_complexity_weight['assign']

    def visit_Call(self, node):
        for v in node.args:
            if isinstance(v, ast.Name):
                self.variables.add(v.id)

        if isinstance(node.func, (ast.Attribute, ast.Call)):
            self.operation_complexity += operation_complexity_weight['call']
        if isinstance(node, ast.Call):
            self.functions.append({'function': node, 'args': node.args})
        else:
            self.functions.append({'function': node, 'args': node.args.args})

    def visit_Import(self, node):
        self.imports += [alias.name for alias in node.names]
        self.import_aliases += [alias for alias in node.names]

    def visit_ImportFrom(self, node):
        self.imports += [f'{node.module}.{alias.name}'
                         for alias in node.names]
        self.import_aliases += [alias for alias in node.names]

    def get_imports(self):
        return self.imports

    def get_unused_imports(self, node):
        import_visitor = GetImports()
        imports = import_visitor.visit(node)
        aliases = import_visitor.aliases
        duc = beniget.DefUseChains()
        duc.visit(node)

        unused_imports = []
        for name in aliases:
            ud = duc.chains[name]
            if not ud.users():
                unused_imports.append(ud.name())

        return unused_imports

    @staticmethod
    def get_cyclomatic_complexity(cell_ast):
        blocks = cc_visit_ast(cell_ast)
        complexity = sum([block.complexity for block \
                          in add_inner_blocks(blocks)])
        return complexity

    @staticmethod
    def get_halstead_complexity(cell_ast):
        halstead_metrics = h_visit_ast(cell_ast)

        return halstead_metrics.total.vocabulary

    @property
    def npavg(self):
        """Get average Number of Parameters per function and functions count"""
        if not self.functions:
            return 0

        args = 0
        for f in self.functions:
            args += len(f['args'])
        return args / len(self.functions)


class MethodVisitor(ast.NodeVisitor):
    def __init__(self):
        self.attributes = set()
        self.inner_methods = set()

    def visit_Attribute(self, node):
        if isinstance(node.ctx, ast.Store) \
                and isinstance(node.value, ast.Name) \
                and node.value.id == 'self':
            self.attributes.add(node.attr)

    def visit_FunctionDef(self, node):
        self.inner_methods.add(node.name)

        for method in node.body:
            method_visitor = MethodVisitor()
            method_visitor.visit(method)
            self.attributes = set.union(self.attributes, method_visitor.attributes)


class ClassVisitor(ast.NodeVisitor):
    def __init__(self):
        self.methods = set()
        self.attributes = set()
        self.private_methods = set()
        self.protected_methods = set()

    def visit_FunctionDef(self, node):
        self.methods.add(node.name)
        if node.name.startswith('__'):
            self.private_methods.add(node.name)
        elif node.name.startswith('_') and not node.name.startswith('__'):
            self.protected_methods.add(node.name)

        for method in node.body:
            method_visitor = MethodVisitor()
            method_visitor.visit(method)
            self.attributes = self.attributes.union(method_visitor.attributes)
            self.methods = self.methods.union(method_visitor.inner_methods)

    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Name):
            self.attributes.add(node.targets[0].id)

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
            'size': visitor.size,
            'private_methods': visitor.private_methods,
            'protected_methods': visitor.protected_methods
        }

    @property
    def classes_size(self):
        size = 0
        for cls in self.classes:
            size += self.get_class_entities(cls)['size']
        return size

    @staticmethod
    def get_sets_coupling(pair: Tuple[Set, Set]) -> int:
        a, b = pair
        return len(a.intersection(b))

    def get_mean_methods_coupling(self):
        couplings = []
        for cls in self.classes:
            functions_visitor = FunctionDefsVisitor()
            functions_visitor.visit(cls)
            inner_functions = functions_visitor.inner_functions
            couplings.append(self.get_class_methods_coupling(inner_functions))

        return sum(couplings) / max(1, len(couplings))

    def get_class_methods_coupling(self, inner_functions_in_methods):
        coupling = 0
        for pair in combinations(inner_functions_in_methods, 2):
            coupling += self.get_sets_coupling(pair)

        return coupling

    def get_non_public_methods_count(self):
        private_count = 0
        protected_count = 0
        for cls in self.classes:
            private_count += len(self.get_class_entities(cls)['private_methods'])
            protected_count += len(self.get_class_entities(cls)['protected_methods'])

        count_dict = {
            'private_methods_count': private_count,
            'protected_methods_count': protected_count
        }
        return count_dict

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
