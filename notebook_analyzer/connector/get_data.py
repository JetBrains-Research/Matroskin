import urllib.request
import nbformat
import os
from sqlalchemy.orm.session import sessionmaker
from abc import ABC

from .db_structures import NotebookDb, CellDb, CodeCellDb, MdCellDb, NotebookFeaturesDb


class NotebookReader(ABC):
    _metadata = {}
    _cells = []
    _features = {}

    @property
    def metadata(self) -> dict:
        return self._metadata

    @property
    def cells(self) -> list:
        return self._cells

    @property
    def features(self):
        return self._features


class NotebookReaderAmazon(NotebookReader):
    _metadata = {}
    _cells = []

    def __init__(self, name):
        self._metadata['name'] = name
        notebook_string = self.download_notebook_amazon()
        notebook = nbformat.reads(notebook_string, 4)

        self._metadata['language'], self._metadata['version'] = self.get_kernel(notebook)
        self._cells = self.get_cells_from_notebook(notebook)

    @property
    def metadata(self):
        return self._metadata

    @property
    def cells(self):
        return self._cells

    def download_notebook_amazon(self):
        host = 'http://github-notebooks-update1.s3-eu-west-1.amazonaws.com/'
        link = host + self._metadata['name']
        with urllib.request.urlopen(link) as url:
            notebook_string = url.read().decode()
        return notebook_string

    @staticmethod
    def get_kernel(notebook: nbformat.NotebookNode):
        kernel = notebook.get('metadata').get('language_info')
        if not kernel:
            return "None", "None"
        return kernel.get("name"), kernel.get("version")

    @staticmethod
    def get_cells_from_notebook(notebook: nbformat.NotebookNode) -> list:
        notebook_cells = [{'type': cell.get('cell_type'),
                           'source': cell.get('source'),
                           'num': num}
                          for num, cell in enumerate(notebook.get('cells'))]
        return notebook_cells


class NotebookReaderDb(NotebookReader):
    _metadata = {}
    _cells = []
    _features = {}

    def __init__(self, notebook_id, engine):
        self.notebook_id = notebook_id
        self.engine = engine
        session = sessionmaker(bind=self.engine)()

        with session as conn:
            self._metadata = self.get_notebook_from_db(conn)
            self._cells = self.get_cells_from_db(conn)
            self._features = self.get_notebook_features_from_db(conn)

    @property
    def metadata(self):
        return self._metadata

    @property
    def cells(self):
        return self._cells

    @property
    def features(self):
        return self._features

    def get_notebook_from_db(self, conn):
        ntb_row = conn.query(NotebookDb). \
            where(NotebookDb.notebook_id == self.notebook_id).first()

        if not ntb_row:
            raise Exception(f'There is no id = {self.notebook_id} in database')

        ntb = self.row_to_dict(ntb_row)
        metadata = {
            'id': ntb['notebook_id'],
            'name': ntb['notebook_name'],
            'language': ntb['notebook_language'],
            'version': ntb['notebook_version']
        }
        return metadata

    def get_rows_filtered_by_notebook_id(self, table, conn):
        return (conn.query(table)
                .filter(CellDb.notebook_id == self.notebook_id)
                .filter(CellDb.cell_id == table.cell_id)
                ).all()

    def get_cells_from_db(self, conn):
        code_rows = self.get_rows_filtered_by_notebook_id(CodeCellDb,
                                                          conn)
        md_rows = self.get_rows_filtered_by_notebook_id(MdCellDb,
                                                        conn)

        cells_dict = {'code': [self.row_to_dict(row) for row in code_rows],
                      'markdown': [self.row_to_dict(row) for row in md_rows]}

        cells = []
        for cell_type, cells_list in cells_dict.items():
            for cell in cells_list:
                cell.update({
                    'num': cell['cell_num'],
                    'type': cell_type
                })
                cells.append(cell)

        return cells

    def get_notebook_features_from_db(self, conn):
        features_row = conn.query(NotebookFeaturesDb). \
            where(NotebookFeaturesDb.notebook_id == self.notebook_id).first()

        if not features_row:
            raise Exception(f'There is no id = {self.notebook_id} in database')

        features = self.row_to_dict(features_row)
        return features

    @staticmethod
    def row_to_dict(row):
        return dict(
            (col, getattr(row, col))
            for col in row.__table__.columns.keys()
        )


class ScriptReader(NotebookReader):
    _metadata = {}
    _cells = []

    def __init__(self, name):
        self._metadata['name'] = name
        self._metadata['language'], self._metadata['version'] = 'python', 'None'
        self._cells = [self.get_script_source()]

    @property
    def metadata(self):
        return self._metadata

    @property
    def cells(self):
        return self._cells

    def get_script_source(self):

        route = os.path.abspath('/Users/konstantingrotov/Documents/datasets/20kk_dataset') + '/'
        path = route + self._metadata['name']
        with open(path, 'r', encoding="utf-8") as f:
            source = f.read()
        if len(source) > 20_000:
            source = ''
        return {'type': 'code', 'num': 1, 'source': source}
