import urllib.request
import urllib.request
import nbformat
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
from abc import ABC

from . import db_structures


class NotebookReader(ABC):
    _metadata = {}
    _cells = []

    @property
    def get_notebook(self) -> dict:
        return self._metadata

    @property
    def get_cells(self) -> list:
        return self._cells


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
    def get_notebook(self):
        return self._metadata

    @property
    def get_cells(self):
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

    def __init__(self, notebook_id, db_name):
        self.notebook_id = notebook_id
        self.engine = create_engine(f"sqlite:///{db_name}")
        self.engine.dispose()

        session = sessionmaker(bind=self.engine)()
        with session as conn:
            self._metadata = self.get_notebook_from_db(conn)
            self._cells = self.get_cells_from_db(conn)

    @property
    def get_notebook(self):
        return self._metadata

    @property
    def get_cells(self):
        return self._cells

    def get_notebook_from_db(self, conn):
        ntb_row = conn.query(db_structures.NotebookDb). \
            where(db_structures.NotebookDb.notebook_id == self.notebook_id).first()

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
                .filter(db_structures.CellDb.notebook_id == self.notebook_id)
                .filter(db_structures.CellDb.cell_id == table.cell_id)
                ).all()

    def get_cells_from_db(self, conn):
        code_rows = self.get_rows_filtered_by_notebook_id(db_structures.CodeCellDb,
                                                          conn)
        md_rows = self.get_rows_filtered_by_notebook_id(db_structures.MdCellDb,
                                                        conn)

        cells_dict = {'code': [self.row_to_dict(row) for row in code_rows],
                      'markdown': [self.row_to_dict(row) for row in md_rows]}

        cells = []
        for cell_type, cells_list in cells_dict.items():
            for cell in cells_list:
                cells.append({
                    'type': cell_type,
                    'num': cell['cell_num'],
                    'source': cell['source']
                })
        return cells

    @staticmethod
    def row_to_dict(row):
        return dict(
            (col, getattr(row, col))
            for col in row.__table__.columns.keys()
        )
