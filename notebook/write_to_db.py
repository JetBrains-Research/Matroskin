from connector import db_structures


def write_notebook_to_db(conn, nb_metadata):
    ntb = db_structures.NotebookDb(
        notebook_name=nb_metadata['name'],
        notebook_language=nb_metadata['language'],
        notebook_version=nb_metadata['version'],
    )
    conn.add(ntb)
    exists = conn.commit()
    if not exists:
        conn.commit()
        return ntb.notebook_id
    else:
        return 0


def write_cells_to_db(conn, cells, notebook_id):
    success = []
    for cell in cells:
        cell['id'] = write_cell_to_db(conn, notebook_id)
        result = write_processed_cell_to_db(cell, conn)
        success.append(result)
    return min(success, default=1)


def write_cell_to_db(conn, notebook_id):
    cell = db_structures.CellDb(notebook_id=notebook_id)
    conn.add(cell)
    conn.commit()
    return cell.cell_id


def write_processed_cell_to_db(cell, conn):
    if cell['type'] == 'markdown':
        cell_db = db_structures.MdCellDb(
            cell_id=cell['id'],
            cell_num=cell['num'],
            source=cell['source']
        )
    else:
        cell_db = db_structures.CodeCellDb(
            cell_id=cell['id'],
            cell_num=cell['num'],
            source=cell['source']
        )

    for key in cell.keys():
        cell_attributes = [name for name in dir(cell_db)
                           if not name.startswith('_')]
        if key in (cell_attributes + ['content', 'metrics']):
            if (key == 'content' and cell['type'] == 'markdown') \
                    or (key == 'metrics' and cell['type'] == 'code'):  # TODO reconsider handling content
                content = cell[key]
                for k, value in content.items():
                    setattr(cell_db, k, value)
                continue
            setattr(cell_db, key, cell[key])

    conn.add(cell_db)
    conn.commit()
    return 1
