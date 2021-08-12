from typing import Dict

from ..connector import db_structures


def write_notebook_to_db(conn, nb_metadata, cells):
    ntb = db_structures.NotebookDb(
        notebook_name=nb_metadata['name'],
        notebook_language=nb_metadata['language'],
        notebook_version=nb_metadata['version'],
    )

    exists = conn.query(
        conn.query(db_structures.NotebookDb).
        filter_by(notebook_name=nb_metadata['name']).exists()
    ).scalar()

    if not exists:
        conn.add(ntb)
        conn.commit()
        conn = write_cells_to_db(conn, cells, ntb.notebook_id)

        return ntb.notebook_id
    else:
        return 0


def write_features_to_db(conn, nb_metadata, features):
    nbf = db_structures.NotebookFeaturesDb(
        notebook_id=nb_metadata['id']
    )
    cell_flatten = flatten(features)
    for key in cell_flatten.keys():
        cell_attributes = [name for name in dir(nbf)
                           if not name.startswith('_')]
        if key in cell_attributes:
            setattr(nbf, key, cell_flatten[key])

    conn.add(nbf)
    conn.commit()

    return cell_flatten


def write_cells_to_db(conn, cells, notebook_id):
    cells_to_db = []
    processed_cells = []

    for cell in cells:
        cell_db = db_structures.CellDb(notebook_id=notebook_id)
        cells_to_db.append(cell_db)

        processed_cells.append(process_cell(cell))

    conn.add_all(cells_to_db)
    conn.commit()

    for i, cell in enumerate(cells_to_db):
        processed_cells[i].cell_id = cell.cell_id

    conn.add_all(processed_cells)
    conn.commit()

    return conn


def flatten(dictionary) -> Dict:
    """
    This function makes dictionary flattening by following rule:
    example_dict = {
                "test1": "string here",
                "test2": "another string",
                "test3": {
                        "test4": 25,
                        "test5": {
                                  "test7": "very nested."
                        },
                        "test6": "yep, another string"
                },
    }

    To

    resulting_dict = {
                "test1": "string here",
                "test2": "another string",
                "test4": 25,
                "test7": "very nested.",
                "test6": "yep, another string"
    }

    And returns flattened dictionary
    """

    output = dict()
    for key, value in dictionary.items():
        if isinstance(value, dict):
            output.update(flatten(value))
        else:
            output[key] = value

    return output


def process_cell(cell):
    if cell['type'] == 'markdown':
        cell_db = db_structures.MdCellDb(
            cell_num=cell['num'],
            source=cell['source']
        )
    else:
        cell_db = db_structures.CodeCellDb(
            cell_num=cell['num'],
            source=cell['source']
        )

    cell_flatten = flatten(cell)
    for key in cell_flatten.keys():
        cell_attributes = [name for name in dir(cell_db)
                           if not name.startswith('_')]
        if key in cell_attributes:
            setattr(cell_db, key, cell_flatten[key])

    return cell_db
