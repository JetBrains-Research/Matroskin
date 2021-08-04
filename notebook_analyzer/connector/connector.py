from sqlalchemy import create_engine

from .get_data import NotebookReaderDb, NotebookReaderAmazon, ScriptReader


class Connector:

    def __init__(self, notebook_id, db_name):
        self.data = None
        self.engine = create_engine(f"sqlite:///{db_name}")

        if isinstance(notebook_id, int):
            self.data = NotebookReaderDb(notebook_id, self.engine)

        elif isinstance(notebook_id, str):
            if notebook_id[-2:] == 'py':  # Handling python scripts
                self.data = ScriptReader(notebook_id)
            else:
                self.data = NotebookReaderAmazon(notebook_id)

        else:
            raise Exception("Incorrect input name format")

