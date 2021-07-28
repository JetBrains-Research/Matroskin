import gast as ast
from radon.visitors import ComplexityVisitor


def get_ast(cell_source):
    try:
        code_ast = ast.parse(cell_source)
        return code_ast
    except SyntaxError as e:  # TODO: reconsider a way for handling magic functions
        code_string = cell_source.splitlines()
        del code_string[e.lineno - 1]
        code_string = '\n'.join(code_string)
        return get_ast(code_string)


def get_cyclomatic_complexity(cell_source):

    refactored_cell = 'def _():\n\tpass\n' \
                      + '\n'.join(['\t' + line
                                   for line in cell_source.split('\n')]) \
        if cell_source else ''
    if not refactored_cell:
        return 0

    try:
        v = ComplexityVisitor.from_code(refactored_cell)
    except SyntaxError as e:
        source = cell_source.splitlines()
        del source[e.lineno - 1 - 3]
        source = '\n'.join(source)
        return get_cyclomatic_complexity(source)

    v = ComplexityVisitor.from_code(refactored_cell)
    func_cell = v.functions[0]
    cell_complexity = func_cell.complexity

    for f in func_cell.closures:
        cell_complexity += f.complexity

    return cell_complexity
