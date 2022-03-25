# Matroskin
Matroskin is a library for analyzing Jupyter notebooks on a large scale and saving the summary data in a convenient format. 
The library employs multiprocessing and can process Jupyter notebooks and usual Python files on a local device. 
You can configure your own local database, change multiprocessing settings, sample sizes, and structural metrics that will be calculated for the files.

## Getting Started
To start using Matroskin, install the library using pip:

```bash
pip install dist/matroskin-0.1.7-py3-none-any.whl
``` 

or build it using 

```bash
poetry build
```

The ["examples"](examples/) directory contains two examples of using the library --- [performing analysis with creating a database](examples/download_notebooks.py) and [reading data from the existing database](examples/get_notebooks.py).
The prerequisites for examples might be found the corresponding [requirements.txt](examples/requirements.txt) file, and installed via:

```bash
pip install -r examples/requirements.txt
```

To use the examples, run them from the [examples](examples/) directory:

```bash
python3 download_noteboooks.py
```

## Configuration
Matroskin provides developers with a lot of ways to configure various parameters.
The example of a [configuration file](examples/config.yml) is also located in the [examples](examples/) directory.

The configuration file consists of the following fields:
1. **`sql`** — a field that describes the parameters of the resulting database. A more detailed description of the parameters can be found below in the **Data** section.
2. **`data`** — a field that describes the parameters of the input data (mapping files that contain routes to Jupyter notebooks or Scripts, sample size of the data, and other parameters).
3. **`ray`** — a field that describes the number of CPU cores used during the analysis. In the examples, we used the `ray` library for multiprocessing.
4. **`metrics`** — a field that describes what metrics should be calculated during the analysis. All metrics are divided into 3 types: metrics applicable to Markdown cells (**`markdown`**  field), code cells (**`code`** field), and the entire notebook (**`notebook`**  field).


## Matroskin architecture
### Initialization
Matroskin is designed to work with the `Notebook` data type. To initialize a `Notebook`, it is enough to pass an absolute path to the `.ipynb` or `.py` file `name` or the path to the file on a remote Amazon server. 
In addition to the file path, you can additionally specify the path to the database `db_name`, where you can eventually save the results of the study or the notebook itself in a processed form:
```python
nb = Notebook(name, db_name)
```
*It is possible to create a `Notebook` class for a usual Python script. In this case, it will be perceived as a notebook with one code cell.*

During the initialization, Matroskin transforms the Jupyter notebook from JSON representation to the object with following attributes:
1.  **`metadata`** — a dictionary that contains information about the name of the notebook and the language properties.
2.  **`cells`** — a list of individual cells. Each cell has an attribute `type` (markdown or code), `source` (source code of the cell), and `numb` (the ordered number of a cell in the notebook). After calculating the metrics, they are stored in new keys of the dictionary of the corresponding cells.
3. **`features`** — a dictionary that contains the results of calculating the metrics for the entire notebook. 
Immediately after the initialization, this dictionary is empty.
4. \*  **`engine`** — the engine of the database, if `db_name` was passed.

### Calculating the metrics

Next, when a notebook has been initialized, the metrics can be calculated. 
In order to calculate certain metrics, you need to pass a configuration dictionary similar to the one stored in the configuration file in the **`metrics`** field. Then, you can calculate the cell's metrics: 
```python
nb.run_tasks(config)
```
and metrics for the entire notebook:
```python
nb.aggregate_tasks(config)
```

### Writing to the database
Finally, you can save all the results to the database:
```python
nb.write_to_db()
```
The databases are described in more detail in the **Data** section.

## Data
Matroskin allows you to store the data in a SQLite database or a Postgres database. The database consists of the following tables:
```
+-------------------+
|      database     |
+-------------------+
| Notebook          |
| Cell              |
| Notebook_features |
| Code_cell         |
| Md_cell           |
+-------------------+
```
1. **`Notebook`** — a table that stores the name, metadata, and unique ID of each notebook.
2. **`Cell`**  — a table that stores the unique ID of the cell and the ID of corresponding notebook for each cell.
```
+-------------------+	+-------------+
|      Notebook     |	|    Cell     |
+-------------------+	+-------------+
| notebook_id       |	| cell_id     |
| notebook_name     |	| notebook_id |
| notebook_language |	+-------------+
| notebook_version  |	
+-------------------+	
```
3-4. **`Code_cell`** and **`Md_cell`** — tables that store the unique ID of a cell and metrics, one for code metrics and one for Markdown metrics.
5. **`Notebook_features`** — a table that stores a unique ID of the notebook and metrics applicable for the entire notebook.
```
+-------------------------+	+----------------------------+
|   Code_cell / Md_cell   |	|      Notebook_features     |
+-------------------------+	+----------------------------+
| cell_id                 |	| notebook_id                |
| cell_num                |	| notebook_cells_number      |
| source                  |	|            ...             |
|           ...           |	|          Metrics           |
|         Metrics         |	|            ...             |
|           ...           |	+----------------------------+
+-------------------------+	
```

To configure the database, you should change the [configuration](examples/config.yml) file located in the [examples](examples/) directory.
The parameters of the database are stored in the **`sql`** field: 
1. **`engine`** (`sqlite` or `postgres`) — the type of the database.
2. **`pg_name`** — the name of the Postgres database.
3. **`password`** — the password to the database.
4. **`host`** — the host of the database.
5. **`name`** — the name of the database.

Also, the [configuration](examples/config.yml) file contains the field **`db`** with the parameter **`create_database`**, which is responsible for whether a new database needs to be created or not.

## Metrics
### Built-in metrics
```
+-------------------------+	+-------------------------+	
|    Code cell metrics    |	| ccn                     |	
+-------------------------+	| sloc                    |	
| cell_id                 |	| comments_count          |	
| notebook_id             |	| blank_lines_count       |	
| cell_num                |	| npavg                   |	
| code_imports            |	| functions_count         |	
| code_lines_count        |	| defined_functions       |	
| code_chars_count        |	| used_functions          |	
+-------------------------+	+-------------------------+	
```

```
+----------------------------+	+----------------------------+	
|      Notebook metrics      |	| comments_density           |	
+----------------------------+	| extended_comments_density  |	
| notebook_cells_number      |	| coupling_between_cells     |	
| md_cells_count             |	| coupling_between_functions |	
| code_cells_count           |	| coupling_between_methods   |	
| notebook_imports           |	| API_functions_count        |	
| ccn                        |	| defined_functions_count    |	
| npavg                      |	| API_functions_uses         |	
| sloc                       |	| defined_functions_uses     |	
| comments_count             |	| other_functions_uses       |	
| extended_comments_count    |	| build_in_functions_uses    |	
| blank_lines_count          |	| build_in_functions_count   |	
+----------------------------+	+----------------------------+
```
*You can find the detailed description of the metrics in the paper.*

### Adding custom metrics

It is possible to add your own metrics, for both types of cells and for the entire notebook.

The metrics that are calculated for the cells are located in files [`code_processor.py`](matroskin/processors/code_processor.py) 
and [`md_processor.py`](matroskin/processors/md_processor.py), respectively.
In order to add your own metric, you need to:
1. Add your function as a class method (`CodeProcessor` or `MdProcessor`). Requirements for methods: they must receive a dictionary 
   that describes one cell `cell` and return a dictionary of the calculated metrics.
2. Add this function to the `task_mapping` dictionary.
3. In the resulting dictionary, the name of the key must be the same as the name of the column in the database (if you want to store it in DB).


The metrics that are calculated for the entire notebook are located in the [`notebook.py`](matroskin/notebook/notebook.py) file.
In order to add your own metric, you need to:
1. Add your function as a method of the `Aggregator` class. `Aggregator` class stores notebooks with metrics as a Pandas DataFrame `cells_df`, where columns represent each cell's features. 
2. Add this function to the `task_mapping` dictionary.
3. In the resulting dictionary, the name of the key must be the same as the name of column in database (if you want to store it in DB).

   
## Credits
This project was carried out during the summer internship in the [Machine Learning Methods in Software Engineering](https://research.jetbrains.org/groups/ml_methods/) Group at JetBrains Research.

Main author: [Konstantin Grotov](https://github.com/konstantgr), ITMO University.

Supervisor and contributor: [Sergey Titov](https://github.com/TitovSergey).

## Contacts

If you have any questions or suggestions about the work, feel free to create an issue
or contact Sergey Titov at [sergey.titov@jetbrains.com](mailto:sergey.titov@jetbrains.com).
