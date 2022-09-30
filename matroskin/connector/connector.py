from sqlalchemy import create_engine

from .get_data import NotebookReaderDb, NotebookReaderAmazon, ScriptReaderFile, ScriptReaderStream


class Connector:

    def __init__(self, notebook_id, db_name="", stream_data=False):
        self.data = None
        self.engine = create_engine(db_name) if db_name else None

        if isinstance(notebook_id, int) and not stream_data:
            self.data = NotebookReaderDb(notebook_id, self.engine)

        elif isinstance(notebook_id, str) and not stream_data:
            if notebook_id.strip()[-2:] == 'py':  # Handling python scripts
                self.data = ScriptReaderFile(notebook_id)
            else:
                self.data = NotebookReaderAmazon(notebook_id)
        elif isinstance(notebook_id, str) and stream_data:
            self.data = ScriptReaderStream(notebook_id, stream_data)

        else:
            raise Exception("Incorrect input name format")

