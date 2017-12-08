import logging


def enable(level=logging.ERROR):
    logger.consoleHandler.setLevel(level)
    logger.disabled = False


def disable():
    logger.disabled = False


def _prepare():
    consoleHandler = logging.StreamHandler()
    fileHandler = logging.FileHandler('rega.log')
    fileHandler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(levelname)s] %(message)s (%(name)s)')
    consoleHandler.setFormatter(formatter)
    fileHandler.setFormatter(formatter)
    logger.addHandler(consoleHandler)
    logger.addHandler(fileHandler)
    logger.disabled = True


logger = logging.getLogger('regalog')
_prepare()
