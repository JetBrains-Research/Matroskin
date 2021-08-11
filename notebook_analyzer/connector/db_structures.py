from sqlalchemy import Column, String, Integer, Float, Text, Boolean, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

base = declarative_base()


class NotebookDb(base):
    __tablename__ = 'Notebook'
    notebook_id = Column(Integer, primary_key=True)
    notebook_name = Column(String, unique=True)
    notebook_language = Column(String)
    notebook_version = Column(String)


class CellDb(base):
    __tablename__ = 'Cell'
    cell_id = Column(Integer, primary_key=True)
    notebook_id = Column(Integer, ForeignKey('Notebook.notebook_id'))


class CodeCellDb(base):
    __tablename__ = 'Code_cell'
    cell_id = Column(Integer, ForeignKey('Cell.cell_id'),
                     primary_key=True)
    cell_num = Column(Integer)
    code_imports = Column(Text, default='')
    code_instructions_count = Column(Integer, default=0)
    code_lines_count = Column(Integer, default=0)
    code_chars_count = Column(Integer, default=0)
    ccn = Column(Integer, default=0)
    halstead = Column(Integer, default=0)
    sloc = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    blank_lines_count = Column(Integer, default=0)
    operation_complexity = Column(Float, default=0)
    classes_size = Column(Integer, default=0)
    npavg = Column(Float, default=0)
    functions_count = Column(Integer, default=0)
    override_methods_count = Column(Integer, default=0)
    new_methods_count = Column(Integer, default=0)
    private_methods_count = Column(Integer, default=0)
    protected_methods_count = Column(Integer, default=0)
    variables = Column(Text, default='')
    functions_and_inners = Column(Text, default='')
    mean_classes_coupling = Column(Float, default=0)
    defined_functions = Column(Text, default='')
    source = Column(Text)


class MdCellDb(base):
    __tablename__ = 'Md_cell'
    cell_id = Column(Integer, ForeignKey('Cell.cell_id'),
                     primary_key=True)
    cell_num = Column(Integer)
    sentences_count = Column(Integer, default=0)
    # words_count = Column(Integer, default=0)
    unique_words = Column(Text, default='')
    cell_language = Column(String, default='')
    latex = Column(Boolean, default=False)
    html = Column(Boolean, default=False)
    code = Column(Boolean, default=False)
    source = Column(Text)


class NotebookFeaturesDb(base):
    __tablename__ = 'Notebook_features'
    notebook_id = Column(Integer, ForeignKey('Notebook.notebook_id'),
                         primary_key=True)
    notebook_cells_number = Column(Integer)
    md_cells_count = Column(Integer)
    code_cells_count = Column(Integer)
    notebook_imports = Column(Text)


def create_db(name):
    engine = create_engine(f'sqlite:///{name}', echo=True)
    base.metadata.drop_all(engine)
    base.metadata.create_all(engine)