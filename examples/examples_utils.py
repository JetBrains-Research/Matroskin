import time
import os
import yaml
from loguru import logger


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class LogFilter:

    def __init__(self, level):
        self.level = level

    def __call__(self, record):
        levelno = logger.level(self.level).no
        return record["level"].no >= levelno


def log_exceptions(func):
    def function_wrapper(*args, **kwargs):
        try:
            if args[1] % 10_000 == 0:
                log_work = LogFilter("INFO")
                fmt = "{time:X}\t{name}\t{level}\t{message}"
                logger.add("../logs/log.log", filter=log_work, level=0, format=fmt)
                logger.info(f'Processed:\t{args[1]}')
            return func(*args, **kwargs)

        except Exception as e:
            if type(e).__name__ != 'AttributeError':
                log_filter = LogFilter("WARNING")
                fmt = "{time:}\t{name}\t{level}\t{message}"
                logger.add("../logs/log.log", filter=log_filter, level=0, format=fmt)
                logger.error(f'{args[0]}\t{type(e).__name__}\t{e}')
            return 0

    return function_wrapper


def timing(func):
    def function_wrapper(*args, **kwargs):
        start_time = time.monotonic()
        func(*args, **kwargs)
        print("--- {:.1f} seconds ---".format(time.monotonic() - start_time))

    return function_wrapper


def get_config(filename):
    with open(filename, "r") as yml_config:
        cfg = yaml.safe_load(yml_config)
        return cfg


def get_db_name(sql_config):
    if sql_config['engine'] == 'postgresql':
        db_name = f'{sql_config["engine"]}:{sql_config["pg_name"]}:{sql_config["password"]}//@{sql_config["host"]}/{sql_config["name"]}'

    else:  # Engine = sqlite
        abs_path_to_db = os.path.join(BASE_DIR, sql_config["name"])
        db_name = f'{sql_config["engine"]}:////{abs_path_to_db}'

    print(f'Database name is {db_name}')
    return db_name
