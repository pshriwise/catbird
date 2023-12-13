from abc import ABC

class MooseBase(ABC):
    """The most fundamental syntactical object."""
    def __init__(self):
        pass

    def to_str(self,print_default=False):
        pass
