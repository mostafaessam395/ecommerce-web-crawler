import logging

def getChild(name):
    """Get a logger that is a child of the root logger."""
    return logging.getLogger(name)
