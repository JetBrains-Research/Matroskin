from sqlalchemy import create_engine

from .get_data import NotebookReaderDb, NotebookReaderAmazon, ScriptReader


class Connector:

    def __init__(self, notebook_id, db_name=""):
        self.data = None
        self.engine = create_engine(db_name) if db_name else None

        if isinstance(notebook_id, int):
            self.data = NotebookReaderDb(notebook_id, self.engine)

        elif isinstance(notebook_id, str):
            if notebook_id.strip()[-2:] == 'py':  # Handling python scripts
                self.data = ScriptReader(notebook_id)
            else:
                self.data = NotebookReaderAmazon(notebook_id)

        else:
            raise Exception("Incorrect input name format")

