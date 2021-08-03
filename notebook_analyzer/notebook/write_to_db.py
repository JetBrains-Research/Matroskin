from connector import db_structures


def write_notebook_to_db(conn, nb_metadata, cells):
    ntb = db_structures.NotebookDb(
        notebook_name=nb_metadata['name'],
        notebook_language=nb_metadata['language'],
        notebook_version=nb_metadata['version'],
    )
    conn.add(ntb)
    exists = conn.commit()
    if not exists:
        conn = write_cells_to_db(conn, cells, ntb.notebook_id)
        return ntb.notebook_id
    else:
        return 0


def write_cells_to_db(conn, cells, notebook_id):
    cell_ids = []
    processed_cells = []

    for cell in cells:
        cell_db = db_structures.CellDb(notebook_id=notebook_id)
        conn.add(cell_db)
        conn.commit()  # TODO try again with bulk_save_objects

        cell_ids.append(cell_db.cell_id)
        processed_cells.append(process_cell(cell))

    for i, cell_id in enumerate(cell_ids):
        processed_cells[i].cell_id = cell_id

    conn.bulk_save_objects(processed_cells)
    conn.commit()

    return conn


def flatten(dictionary):
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

    for key in flatten(cell).keys():
        cell_attributes = [name for name in dir(cell_db)
                           if not name.startswith('_')]
        if key in cell_attributes:
            setattr(cell_db, key, flatten(cell)[key])

    return cell_db
