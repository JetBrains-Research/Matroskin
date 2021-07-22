import ast
from typing import List, Tuple
from radon.raw import analyze
from radon.visitors import ComplexityVisitor
import collections
import functools
import operator


def get_ast(cell_source):
    try:
        code_ast = ast.parse(cell_source)
        return code_ast
    except SyntaxError as e:  # TODO: reconsider a way for handling magic functions
        code_string = cell_source.splitlines()
        del code_string[e.lineno - 1]
        code_string = '\n'.join(code_string)
        return get_ast(code_string)


def get_cell_functions(ast_cell):
    functions = [
        node for node in ast.walk(ast_cell)
        if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            or isinstance(node, ast.Call)
            and isinstance(node.func, (ast.Attribute, ast.Call, ast.Name)))
    ]
    return functions
    # for function in functions: #  TODO Maybe store args?
    #     print(f"Args: {', '.join([arg.arg for arg in function.args.args])}")


def get_function_args(ast_func):
    if isinstance(ast_func, ast.Call):
        return ast_func.args
    return ast_func.args.args


def get_cell_classes(ast_cell):
    classes = [
        node
        for node in ast.walk(ast_cell)
        if isinstance(node, ast.ClassDef)
    ]
    return classes


def get_class_methods(ast_class):
    methods = [
        node
        for node in ast.walk(ast_class)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    return methods


def get_class_attributes(ast_class):
    attributes = [node.targets[0].id
                  for node in ast_class.body
                  if (isinstance(node, ast.Assign)
                      and isinstance(node.targets[0], ast.Name))]

    for node in ast.walk(ast_class):
        if isinstance(node, ast.Attribute) \
                and isinstance(node.ctx, ast.Store) \
                and isinstance(node.value, ast.Name) \
                and node.value.id == 'self':
            attributes.append(node.attr)

    return attributes


def get_override_metrics(ast_cell) -> List[Tuple[int, int]]:  # TODO Rename function
    res = []
    for cls in filter(lambda x: isinstance(x, ast.ClassDef), ast_cell.body):
        child_methods = get_class_methods(cls)

        if len(cls.bases) and isinstance(cls.bases[0], ast.Attribute):
            parent_name = cls.bases[0].value.id
        elif len(cls.bases) and isinstance(cls.bases[0], ast.Name):
            parent_name = cls.bases[0].id
        else:
            parent_name = None

        parent = [cls for cls in ast_cell.body
                  if isinstance(cls, ast.ClassDef)
                  and cls.name == parent_name] if parent_name else None
        parent = parent if parent else None
        if not parent:
            res.append((0, len(child_methods)))
            continue

        parent_methods = get_class_methods(parent[0]) if parent else None
        child_methods = get_class_methods(cls)

        parent_set = set([p.name for p in parent_methods])
        child_set = set([c.name for c in child_methods])
        get_from_parent = child_set.intersection(parent_set)
        done_by_child = child_set.difference(parent_set)

        res.append(
            (len(get_from_parent), len(done_by_child))
        )
    return res


def get_npavg(ast_cell) -> Tuple[float, int]:
    """Get average Number of Parameters per function and functions count"""
    functions = get_cell_functions(ast_cell)
    if not functions:
        return 0, 0

    res = 0
    for f in functions:
        res += len(get_function_args(f))
    return res / len(functions), len(functions)


def get_classes_size(ast_cell):
    classes = get_cell_classes(ast_cell)

    return sum([
        len(get_class_attributes(cls))
        + len(get_class_methods(cls))
        for cls in classes
    ])


def get_cyclomatic_complexity(cell_source):

    refactored_cell = 'def _():\n\tpass\n' \
                      + '\n'.join(['\t' + line
                                   for line in cell_source.split('\n')]) \
        if cell_source else ''
    if not refactored_cell:
        return 0

    v = ComplexityVisitor.from_code(refactored_cell)
    func_cell = v.functions[0]
    cell_complexity = func_cell.complexity

    for f in func_cell.closures:
        cell_complexity += f.complexity

    return cell_complexity


def get_operation_complexity(ast_cell):
    operation_complexity = 0
    for node in ast.walk(ast_cell):
        if isinstance(node, ast.BinOp):
            operation_complexity += 2
        if isinstance(node, ast.Assign):
            operation_complexity += 0.5
        if isinstance(node, ast.Call) \
                and isinstance(node.func, (ast.Attribute, ast.Call)):
            operation_complexity += 5
        if isinstance(node, (ast.AsyncFor, ast.While, ast.If,
                             ast.With, ast.AsyncWith)):
            operation_complexity += 0.5

    return operation_complexity
