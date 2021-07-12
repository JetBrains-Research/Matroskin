import nbformat
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
import ast
import re

import db_structures
import get_data


def markdown_cell(func):
    def function_wrapper(*args, **kwargs):
        cell = args[0] if len(args) == 1 else args[1]
        if cell['type'] == 'markdown':
            return func(*args, **kwargs)
        else:
            return None
    return function_wrapper


def code_cell(func):
    def function_wrapper(*args, **kwargs):
        cell = args[0] if len(args) == 1 else args[1]
        if cell['type'] == 'code':
            return func(*args, **kwargs)
        else:
            return None
    return function_wrapper


class Notebook(object):
    metadata = {}
    cells = []
    nlp = None

    def __init__(self, name, db_name=''):
        self.mapping = {
            'code_instructions_count': self.get_num_instructions,
            'code_lines_count': self.get_lines_of_code,
            'cell_language': self.get_cell_language,
            'code_imports': self.get_imports,
            'code_chars_count': self.get_chars_of_code,
            'sentences_count': self.get_sentences_count,
            'unique_words': self.get_unique_words,
            'content': self.get_md_content
        }

        self.engine = create_engine(f"sqlite:///{db_name}")
        self.engine.dispose()

        if isinstance(name, int):
            try:
                data = get_data.NotebookReaderDb(name, db_name)
            except Exception as e:
                with open("log.txt", "a") as f:
                    f.write(f'{name}\t{type(e).__name__}\n')
        elif isinstance(name, str):
            data = get_data.NotebookReaderAmazon(name)
        else:
            raise Exception("Incorrect input name format")

        self.metadata = data.get_notebook
        self.cells = data.get_cells

    def add_nlp_model(self, nlp):
        self.nlp = nlp
        return 1

    def write_to_db(self):
        session = sessionmaker(bind=self.engine)()

        with session as conn:
            self.metadata['id'] = self.write_notebook_to_db(conn)
            success = self.write_cells_to_db(conn)
        return success

    def write_notebook_to_db(self, conn):
        ntb = db_structures.NotebookDb(
            notebook_name=self.metadata['name'],
            notebook_language=self.metadata['language'],
            notebook_version=self.metadata['version'],
        )
        conn.add(ntb)
        exists = conn.commit()
        if not exists:
            conn.commit()
            return ntb.notebook_id
        else:
            return 0

    def write_cells_to_db(self, conn):
        success = []
        for cell in self.cells:
            cell['id'] = self.write_cell_to_db(conn)
            result = self.write_processed_cell_to_db(cell, conn)
            success.append(result)
        return min(success, default=1)

    def write_cell_to_db(self, conn):
        cell = db_structures.CellDb(notebook_id=self.metadata['id'])
        conn.add(cell)
        conn.commit()
        return cell.cell_id

    def write_processed_cell_to_db(self, cell, conn):
        if cell['type'] == 'markdown':
            cell_db = db_structures.MdCellDb(
                cell_id=cell['id'],
                cell_num=cell['num'],
                source=cell['source']
            )
        else:
            cell_db = db_structures.CodeCellDb(
                cell_id=cell['id'],
                cell_num=cell['num'],
                source=cell['source']
            )

        for key in cell.keys():
            if key in dir(cell_db) and key in self.mapping:
                if key == 'content':  # TODO reconsider handling content
                    content = cell[key]
                    for k, value in content.items():
                        setattr(cell_db, k, value)
                    continue
                # print(f'{key} -> {cell[key]}')
                setattr(cell_db, key, cell[key])

        conn.add(cell_db)
        conn.commit()
        return 1

    def parse_features(self, config):
        for cell in self.cells:
            for function in {k: v for k, v in config.items() if v}:
                cell[function] = self.mapping[function](cell)
        return self.cells

    @markdown_cell
    def get_cell_language(self, cell):
        doc = self.nlp(cell['source'])
        return doc._.language['language']

    @markdown_cell
    def get_sentences_count(self, cell):
        doc = self.nlp(cell['source'])
        sentence_tokens = [[token.text for token in sent]
                           for sent in doc.sents]
        return len(sentence_tokens)

    @markdown_cell
    def get_unique_words(self, cell) -> str:
        doc = self.nlp(cell['source'])

        words = [token.text.lower()
                 for token in doc
                 if not token.is_stop and not token.is_punct]
        unique_words = set(words)
        return ' '.join(unique_words)

    @staticmethod
    @markdown_cell
    def get_md_content(cell) -> dict:
        latex_regex_1 = r'\$(.*)\$'
        latex_regex_2 = r'\\begin(.*)\\end'

        html_regex = r'<(.*)>'
        code_regex = r'`(.*)`'
        result = {
            'latex': False,
            'html': False,
            'code': False
        }

        cell_text = cell['source'].replace('\n', '')
        if re.findall(latex_regex_1, cell_text, re.MULTILINE) \
                or re.findall(latex_regex_2, cell_text, re.MULTILINE):
            result['latex'] = True
        if re.findall(html_regex, cell_text, re.MULTILINE):
            result['html'] = True
        if re.findall(code_regex, cell_text, re.MULTILINE):
            result['code'] = True
        return result

    def get_ast(self, cell):
        try:
            code_ast = ast.parse(cell)
            return code_ast
        except SyntaxError as e:  # TODO: reconsider a way for handling magic functions
            code_string = cell.splitlines()
            del code_string[e.lineno - 1]
            code_string = '\n'.join(code_string)
            return self.get_ast(code_string)

    @code_cell
    def get_num_instructions(self, cell):
        cell_ast = self.get_ast(cell['source'])
        return self.depth_ast(cell_ast)

    def depth_ast(self, cell_ast):
        return 1 + max(
            [self.depth_ast(child)
             for child in ast.iter_child_nodes(cell_ast)],
            default=0)

    @code_cell
    def get_lines_of_code(self, cell):
        cell_ast = self.get_ast(cell['source'])
        return max([node.lineno
                    for node in ast.walk(cell_ast)
                    if hasattr(node, 'lineno')],
                   default=0)

    @staticmethod
    @code_cell
    def get_chars_of_code(cell):
        return len(cell['source'])

    @code_cell
    def get_imports(self, cell):
        cell_imports = []
        cell_ast = self.get_ast(cell['source'])
        ast_nodes = list(ast.walk(cell_ast))
        for node in ast_nodes:
            if type(node) == ast.Import:
                cell_imports += [alias.name for alias in node.names]
            if type(node) == ast.ImportFrom:
                cell_imports += [f'{node.module}.{alias.name}' for alias in
                                 node.names]
        return " ".join(cell_imports)
