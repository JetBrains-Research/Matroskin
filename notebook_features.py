from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
import urllib.request
import nbformat

from db_structures import Notebook, Notebook_features
from cells_features import get_code_cells, get_md_cells, add_code_cells, add_md_cells

engine = create_engine("sqlite:///test.db")

def get_kernel(notebook: nbformat.NotebookNode) -> str:
    lang_info = notebook.get('metadata').get('language_info')
    if not lang_info:
        return 'None None'
    kernel = f'{lang_info.get("name")} ' \
             f'{lang_info.get("version")}'.strip()
    return kernel


def open_notebook(ntb_name):
    host = 'http://github-notebooks-update1.s3-eu-west-1.amazonaws.com/'
    link = host + ntb_name

    with urllib.request.urlopen(link) as url:
        notebook_string = url.read().decode() 

    return notebook_string


def add_notebook(notebook, ntb_name, conn):
    ntb_kernel = get_kernel(notebook)
    ntb_lang, ntb_version = ntb_kernel.split()
    ntb_cells = len(notebook['cells'])

    notebook_sql = Notebook(
        notebook_name = ntb_name, 
        notebook_language = ntb_lang,
        notebook_version = ntb_version,
    )
    conn.add(notebook_sql)

    exists = conn.commit()
    if not exists:
        conn.commit()
        return notebook_sql.notebook_id, conn
    else: return -1, conn


def add_notebook_features(imports, code_cells_count, md_cells_count, notebook_id, conn):
    conn.add(Notebook_features(
            notebook_id=notebook_id,
            notebook_cells_number=md_cells_count + code_cells_count,
            md_cells_count=md_cells_count,
            code_cells_count=code_cells_count,
            notebook_imports=" ".join(set((" ".join(imports)).split()))
        ))
    conn.commit()


def get_features(notebook, notebook_id, conn):
    code_cells_with_nums = get_code_cells(notebook)
    md_cells_wth_nums = get_md_cells(notebook)
    
    imports = add_code_cells(code_cells_with_nums, 
                             notebook_id, conn)
    add_md_cells(md_cells_wth_nums, notebook_id, conn)
    
    code_cells_count = len(list(code_cells_with_nums))
    md_cells_count = len(list(md_cells_wth_nums))

    add_notebook_features(imports, code_cells_count, 
                          md_cells_count, notebook_id, conn)


def get_ntb(ntb_name):
    try:
        ntb_string = open_notebook(ntb_name)
        notebook = nbformat.reads(ntb_string, 4)

        engine.dispose()
        session = sessionmaker(bind=engine)()
        
        with session as conn:
            notebook_id, conn = add_notebook(notebook, ntb_name, conn)
            if notebook_id != -1:
                get_features(notebook, notebook_id, conn)
                return 1
    except:
        return {'name': ntb_name}