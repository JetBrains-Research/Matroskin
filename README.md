# Matroskin — library for large scale Jupyter notebook analysis.
Matroskin is a library for analyzing notebooks and saving the summary data in a convenient format. 
This library uses multiprocessing and can process Jupyter notebooks and Python scripts on a local device. 
You can configure your own local database, change multiprocessing settings, sample sizes, and structural metrics that will be processed.

## Getting Started
To start using Matroskin, install the library using pip:<br/>
`pip install dist/matroskin-0.1.7-py3-none-any.whl` 
or build it using `poetry build` .

The ["examples" folder](examples/) contains 2 examples of using the library --- [performing analysis with creating a database](examples/download_notebooks.py) and [reading data from the existing database](examples/get_notebooks.py).
Prerequisites for examples might be found there in the [requirements.txt](examples/requirements.txt).
`pip install -r examples/requirements.txt`


To start examples, run them from [examples](examples/) folder.<br/>
`python3 download_noteboooks.py`

## Configuration
Matroskin provides developers with great freedom to configure various parameters.
The example of [configuration](examples/config.yml) file located in [examples](examples/) folder.

The configuration file consists of the following fields:
1. **`sql`** — a field that describes the parameters of the resulted database. A more detailed description of the parameters is described in the **Data** section.
2. **`data`** — a field that describes the parameters of input data (mapping files, which contain routes to Jupyter notebooks / Scripts, sample size of data and other extra parameters).
3. **`ray`** — a field that describes the number of CPU cores used during analyzing. In examples we used the ray library for multiprocessing.
4. **`metrics`** — a field that describes what metrics should be implemented during analysis. All metrics are divided into 3 types: metrics applicable to markdown cells (**`markdown`**  field), code cells (**`code`** field) and the entire notebook (**`notebook`**  field).


## Matroskin architecture
### Initialization
Matroskin is designed to work with the `Notebook` data type. To initialize a `Notebook`, it is enough to pass an absolute path to `.ipynb` or `.py` file `name` or the path to the file on a remote Amazon server. 
In addition to the file path, you can additionally specify the path to the database `db_name`, where you can eventually save the results of the study or the notebook itself in a processed form.
```python
nb = Notebook(name, db_name)
```
*It is also possible to create `Notebook` class for a Python script. In this case, it will be perceived as a notebook with one code cell.*

During initializing, Matroskin transforms Jupyter notebook from Json representation to the object with following attributes:
1.  **`metadata`** — dictionary, which contains information about name of notebook and language properties.
2.  **`cells`** — list of individual cells. Each cell after initialization has an attributes `type` (markdown or code) `source` (source code of the cell) and `numb` (order number of cell in notebook). After applying the metrics, they are stored in new keys of the dictionary of the corresponding cells.
3. **`features`** — dictionary, which contains results of metrics for whole notebook. 
Immediately after initialization is an empty dictionary.
4. \*  **`engine`** — engine of the database if `db_name` was passed.

### Metrics processing

Next, when a notebook has been initialized, metrics could be processed. 
In order to calculate certain metrics, you need to pass a configuration dictionary similar to the one stored in the configuration file in the **`metrics`** field. Then, you can calculate cell's metrics 
```python
nb.run_tasks(config)
```
and metrics for whole notebook
```python
nb.aggregate_tasks(config)
```

### Writing to the database
Save all results to the database
```python
nb.write_to_db()
```
More about databases described in **Data** section.

## Data
Matroskin allows you to store data in a sqlite database or a Postgres database. the database consists of the following tables:
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
1. **`Notebook`** — table, which stores name, metadata and unique id of the notebook
2. **`Cell`**  — table, which stores unique id of the cell and id of corresponding notebook.
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
3. **`Code_cell`**, **`Md_cell`** — tables, which stores unique id of cell and metrics, applicable for code/markdown cells.
5. **`Notebook_features`** — table, which stores unique id of notebook and metrics, applicable for whole notebook.
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

To configure database you should change [configuration](examples/config.yml) file located in [examples](examples/) folder.
Database parameters stored in field **`sql`**: 
1. **`engine`** (`sqlite` or `postgres`) — type of database.
2.   **`pg_name`** — name of postgres database
3.   **`password`** — password to database
4.   **`host`** — host of database
5.   **`name`** — name of database

Also [configuration](examples/config.yml) file contains field **`db`** with the parameter **`create_database`** which is responsible for whether a new database needs to be created or not.
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
*A more detailed description of the metrics could be found in the paper.*
### Adding custom metrics

It is possible to add your own metrics, both for both types of cells, and for the entire notebook.

The metrics that are calculated for the cells are in files [`code_processor.py`](matroskin/processors/code_processor.py) 
and [`md_processor.py`](matroskin/processors/md_processor.py), respectively.
In order to add your own metric you need to:
1. Add your function as a class method (`CodeProcessor` or `MdProcessor`). Requirements for methods — they must accept a dictionary 
   that describes one cell `cell` and return a dictionary of calculated metrics.
2. Add this function to `task_mapping` dictionary.
3. In the resulted dictionary, the name of the key must be the same with the name of column in the database (if you want to store it in DB).


The metrics that are calculated for the whole notebook are in files [`notebook.py`](matroskin/notebook/notebook.py).
In order to add your own metric you need to:
1. Add your function as a method of `Aggregator` class. `Aggregator` class stores notebooks with cells metrics as Pandas DataFrame `cells_df`, where columns are cell's features. 
2. Add this function to `task_mapping` dictionary.
3. In the resulted dictionary the name of the key must be the same with the name of column in database (if you want to store it in DB).

   
## Credits
This project was made during a summer internship in [Machine Learning for 
Software Engineering Research Group in JetBrains Research](https://research.jetbrains.org/groups/ml_methods/). <br/>
Supervisor and contributor of this project is [Sergey Titov](https://github.com/TitovSergey). <br/>
Author: [Konstantin Grotov](https://github.com/konstantgr), ITMO University.