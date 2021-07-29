from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from . import get_data


class Connector:

    def __init__(self, notebook_id, db_name):
        self.data = None
        self.engine = create_engine(f"sqlite:///{db_name}")
        self.engine.dispose()

        if isinstance(notebook_id, int):
            try:
                self.data = get_data.NotebookReaderDb(notebook_id, db_name)
            except OperationalError as e:
                with open("../logs/log.txt", "a") as f:
                    f.write(f'{notebook_id}\t{type(e).__name__}\n')
            finally:
                return

        elif isinstance(notebook_id, str):
            self.data = get_data.NotebookReaderAmazon(notebook_id)

        else:
            raise Exception("Incorrect input name format")

