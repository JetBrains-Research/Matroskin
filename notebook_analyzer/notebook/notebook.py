from sqlalchemy.orm.session import sessionmaker

from ..processors import MdProcessor
from ..processors import CodeProcessor
from ..connector import Connector
from .write_to_db import write_notebook_to_db


class Aggregator:
    def __init__(self):
        self.a = None


class Notebook(object):

    processors = [CodeProcessor, MdProcessor]
    aggregator = Aggregator()
    cells = []
    metadata = {}
    nlp = None

    def __init__(self, name, db_name=""):

        connector = Connector(name, db_name)

        self.engine = connector.engine
        self.metadata = connector.data.metadata
        self.cells = connector.data.cells

    def add_nlp_model(self, nlp):
        self.nlp = nlp

        return 1

    def write_to_db(self):
        session = sessionmaker(bind=self.engine)()

        with session as conn:
            self.metadata['id'] = write_notebook_to_db(conn, self.metadata, self.cells)

        return 1

    def run_tasks(self, config):
        for i, cell in enumerate(self.cells):
            self.cells[i] = self.processors[0](cell).process_cell(config['code']) \
                if cell['type'] == 'code' \
                else self.processors[1](cell, self.nlp).process_cell(config['markdown'])

        return self.cells

