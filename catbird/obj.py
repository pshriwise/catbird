from .base import MooseBase

class MooseObject(MooseBase):

    params_name="_moose_params"

    def __init__(self):
        print("I am an object")
