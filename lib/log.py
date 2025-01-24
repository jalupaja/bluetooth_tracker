import logging

class log:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logging.basicConfig(level=logging.DEBUG) # TODO does this work?
        return cls._instance

    def debug(message):
        logging.debug(message)

    def info(message):
        logging.info(message)

    def warning(message):
        logging.warning(message)

    def error(message):
        logging.exception(message)
