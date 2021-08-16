import time
# import spacy
# from spacy_langdetect import LanguageDetector
# from spacy.language import Language
from loguru import logger


class LogFilter:

    def __init__(self, level):
        self.level = level

    def __call__(self, record):
        levelno = logger.level(self.level).no
        return record["level"].no >= levelno


def log_exceptions(func):

    def function_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_filter = LogFilter("WARNING")
            fmt = "{time:X}\t{name}\t{level}\t{message}"
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


# @Language.factory('language_detector')
# def language_detector(nlp, name):
#     return LanguageDetector()


def set_nlp_model():
    # nlp = spacy.load('en_core_web_sm')
    # nlp.max_length = 2000000
    # nlp.add_pipe('language_detector', last=True)
    # return nlp

    return None
