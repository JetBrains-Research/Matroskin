import urllib.request
import nbformat
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
import ast
import spacy
from spacy_langdetect import LanguageDetector
from spacy.language import Language

import db_structures


@Language.factory('language_detector')
def language_detector(nlp, name):
    return LanguageDetector()


def get_cell_language(cell):
    if cell['type'] == 'markdown':
        nlp = spacy.load('en_core_web_sm')
        nlp.max_length = 2000000
        nlp.add_pipe('language_detector', last=True)
        doc = nlp(cell['source'])
        return doc._.language['language']
    else:
        return None


class Notebook(object):
    metadata = {}
    cells = []

    def __init__(self, name):
        self.mapping = {
            'code_instructions_count': self.get_num_instructions,
            'code_lines_count': self.get_lines_of_code,
            'cell_language': get_cell_language,
            'code_imports': self.get_imports
        }

        self.metadata['name'] = name
        notebook_string = self.download_notebook()
        notebook = nbformat.reads(notebook_string, 4)
        self.metadata['language'], self.metadata['version'] = self.get_kernel(notebook)
        self.cells = self.get_cells(notebook)

    def write_to_db(self):
        engine = create_engine("sqlite:///test.db")
        engine.dispose()
        session = sessionmaker(bind=engine)()

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
            return -1

    def write_cells_to_db(self, conn):
        success = []
        for cell in self.cells:
            cell['id'] = self.write_cell_to_db(conn)
            if cell['type'] == 'code':
                result = self.write_code_cell_to_db(cell, conn)
            else:
                result = self.write_md_cell_to_db(cell, conn)
            success.append(result)
        return min(success, default=1)

    def write_cell_to_db(self, conn):
        cell = db_structures.CellDb(notebook_id=self.metadata['id'])
        conn.add(cell)
        conn.commit()
        return cell.cell_id

    def write_code_cell_to_db(self, cell, conn):
        cd_cell = db_structures.CodeCellDb(
                cell_id=cell['id'],
                cell_num=cell['num'],
                source=cell['source']
        )
        for key in cell.keys():
            if key in dir(cd_cell) and key in self.mapping:
                # print(f'{key} -> {cell[key]}')
                setattr(cd_cell, key, cell[key])

        conn.add(cd_cell)
        conn.commit()
        return 1

    def write_md_cell_to_db(self, cell, conn):
        # sentences_count = get_sentences_count(cell)
        # language = get_language(cell)
        # words = get_words(cell)
        # cell_contents = get_md_contents(cell)
        # unique_words = Counter(words)
        # unique_string = " ".join(f"{key}-{value}" for key, value in unique_words.items())
        md_cell = db_structures.MdCellDb(
            cell_id=cell['id'],
            cell_num=cell['num'],
            source=cell['source']
        )
        # conn.add(db_structures.MdCellDb(
        #     cell_id=cell['id'],
        #     cell_num=cell['num'],
        #     sentences_count=0,  # sentences_count,
        #     words_count=0,  # len(words),
        #     unique_words='0',  # unique_string,
        #     cell_language='en',  # language,
        #     latex=False,  # cell_contents['latex'],
        #     html=False,  # cell_contents['html'],
        #     code=False,  # cell_contents['code'],
        #     source=cell['source']
        # ))
        for key in cell.keys():
            if key in dir(md_cell) and key in self.mapping:
                # print(f'{key} -> {cell[key]}')
                setattr(md_cell, key, cell[key])

        conn.add(md_cell)
        conn.commit()
        return 1

    def download_notebook(self):
        host = 'http://github-notebooks-update1.s3-eu-west-1.amazonaws.com/'
        link = host + self.metadata['name']
        with urllib.request.urlopen(link) as url:
            notebook_string = url.read().decode()
        return notebook_string

    def get_cells(self, notebook: nbformat.NotebookNode) -> list:
        notebook_cells = [{'type': cell.get('cell_type'),
                           'source': cell.get('source'),
                           'num': num}
                          for num, cell in enumerate(notebook.get('cells'))]
        return notebook_cells

    def get_kernel(self, notebook: nbformat.NotebookNode):
        kernel = notebook.get('metadata').get('language_info')
        if not kernel:
            return "None", "None"
        return kernel.get("name"), kernel.get("version")

    def parse_features(self, config):
        for cell in self.cells:
            for function in {k: v for k, v in config.items() if v}:
                cell[function] = self.mapping[function](cell)
        return self.cells

    def get_ast(self, cell):
        try:
            code_ast = ast.parse(cell)
            return code_ast
        except SyntaxError as e:  # TODO: reconsider a way for handling magic functions
            code_string = cell.splitlines()
            del code_string[e.lineno - 1]
            code_string = '\n'.join(code_string)
            return self.get_ast(code_string)

    def get_num_instructions(self, cell):
        if cell['type'] == 'code':
            cell_ast = self.get_ast(cell['source'])
            return self.depth_ast(cell_ast)

    def depth_ast(self, cell_ast):
        return 1 + max(
            [self.depth_ast(child)
             for child in ast.iter_child_nodes(cell_ast)],
            default=0)

    def get_lines_of_code(self, cell):
        if cell['type'] == 'code':
            cell_ast = self.get_ast(cell['source'])
            return max([node.lineno
                        for node in ast.walk(cell_ast)
                        if hasattr(node, 'lineno')],
                       default=0)
        else:
            return None

    def get_imports(self, cell):
        cell_imports = []
        if cell['type'] == 'code':
            cell_ast = self.get_ast(cell['source'])
            ast_nodes = list(ast.walk(cell_ast))
            for node in ast_nodes:
                if type(node) == ast.Import:
                    cell_imports += [alias.name for alias in node.names]
                if type(node) == ast.ImportFrom:
                    cell_imports += [f'{node.module}.{alias.name}' for alias in
                                     node.names]
            return " ".join(cell_imports)
        else:
            return None
