from .obj import MooseObject

class MooseAction(MooseObject):
    def __init__(self):
        print("I am an action")
        pass

    def to_str(self,print_default=False):
        pass
