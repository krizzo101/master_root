try:
    # Try absolute import first
    from shared.logging.shared_logger import SharedLogger
except ImportError:
    # Fallback to relative import with path manipulation
    import sys
    import os

    # Add the src directory to the path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(current_dir, "..", "..", "..", "..")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    from shared.logging.shared_logger import SharedLogger


def get_logger(name):
    return SharedLogger(name=name).get_logger()
