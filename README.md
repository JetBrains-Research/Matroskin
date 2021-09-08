# Jupyter Notebook Analyzer
It is a library for analyzing notebooks and saving summary data in a convenient format. This library works with multiprocessing and can process notebooks from a [given dataset](https://github-notebooks-update1.s3-eu-west-1.amazonaws.com/) using [unique notebooks names](https://github-notebooks-samples.s3-eu-west-1.amazonaws.com/ntbs_list.json) or Python scripts located on a local device. 
You can configure your own local database, change multiprocessing settings, sample sizes and metrics, which will proccessed.

## Getting Started
Library examples located in [examples folder](examples/). There are 2 examples: download notebooks or scripts to local database and getting notebooks with processed metrics from local database.

To start using library you should install .whl file using pip:
`pip install filename.whl`

In root folder create folder databases. Download in root folder json list of jupyter notebooks names using next command:
`wget "https://github-notebooks-samples.s3-eu-west-1.amazonaws.com/ntbs_list.json"`

To change database in which will download processed notebooks go to `examples/config.yml` and change sql parameters; If you're using sqlite just change name of database. 
To change multiprocessing parameters go to `examples/config.yml` and change `ray_multiprocessing` parameters.

After that you can get processed notebooks using `examples/download_notebooks.py` file or get processed data from local database using `examples/get_notebooks.py` file.
## Available metrics
...
...
...

## Credits
This project was made during a summer internship in [Machine Learning for 
Software Engineering Research Group in JetBrains Research](https://research.jetbrains.org/groups/ml_methods/).
Supervisor and contributor of this project is [Sergey Titov](https://github.com/TitovSergey).
Author: [Konstantin Grotov](https://github.com/konstantgr), ITMO University.
