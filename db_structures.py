from sqlalchemy import Column, String, Integer, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

base = declarative_base()        

class Notebook(base):
    __tablename__ = 'Notebook'
    notebook_id = Column(Integer, primary_key=True)
    notebook_name = Column(String, unique=True)
    notebook_language  = Column(String)
    notebook_version  = Column(String)
    

class Cell(base):
    __tablename__ = 'Cell'
    cell_id = Column(Integer, primary_key=True)
    notebook_id = Column(Integer, ForeignKey('Notebook.notebook_id'))
    

class Code_cell(base):
    __tablename__ = 'Code_cell'
    cell_id = Column(Integer, ForeignKey('Cell.cell_id'),
                     primary_key=True)
    cell_num = Column(Integer)
    code_imports = Column(Text)
    code_lines_count = Column(Integer)
    code_chars_count = Column(Integer)
    source = Column(Text)

              
class Md_cell(base):
    __tablename__ = 'Md_cell'
    cell_id = Column(Integer, ForeignKey('Cell.cell_id'), 
                     primary_key=True)
    cell_num = Column(Integer)
    sentences_count = Column(Integer)
    words_count = Column(Integer)
    unique_words = Column(Text)
    cell_language = Column(String)
    latex = Column(Boolean)
    html = Column(Boolean)
    code = Column(Boolean)
    source = Column(Text)
    
              
class Notebook_features(base):
    __tablename__ = 'Notebook_features'
    notebook_id = Column(Integer, ForeignKey('Notebook.notebook_id'), 
                         primary_key=True)
    notebook_cells_number = Column(Integer)
    md_cells_count = Column(Integer)
    code_cells_count = Column(Integer)
    notebook_imports = Column(Text)
