import sys
sys.path.append("..")  # TODO very very bad
from sqlalchemy.orm.session import sessionmaker

from processors.md_processor import MdProcessor
from processors.code_processor import CodeProcessor
from connector.connector import Connector
from . import write_to_db


class Aggregator:
    def __init__(self):
        self.a = 1


class Notebook(object):

    processors = [CodeProcessor, MdProcessor]
    aggregator = Aggregator()
    cells = []
    metadata = {}
    nlp = None

    def __init__(self, name, db_name=''):

        connector = Connector(name, db_name)

        self.engine = connector.engine
        self.metadata = connector.data.get_notebook
        self.cells = connector.data.get_cells

    def add_nlp_model(self, nlp):
        self.nlp = nlp
        return 1

    def write_to_db(self):
        session = sessionmaker(bind=self.engine)()

        with session as conn:
            self.metadata['id'] = write_to_db.write_notebook_to_db(conn, self.metadata)
            success = write_to_db.write_cells_to_db(conn, self.cells, self.metadata['id'])
        return success

    def run_tasks(self, config):
        for i, cell in enumerate(self.cells):
            self.cells[i] = self.processors[0](cell).process_cell(config['code']) \
                if cell['type'] == 'code' \
                else self.processors[1](cell, self.nlp).process_cell(config['markdown'])

        return self.cells

