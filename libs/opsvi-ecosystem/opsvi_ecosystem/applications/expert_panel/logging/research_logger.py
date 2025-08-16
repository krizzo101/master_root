from shared.logging.shared_logger import SharedLogger


def get_logger(name):
    return SharedLogger(name=name).get_logger()
