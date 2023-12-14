from .base import MooseBase

class MooseAction(MooseBase):

    params_name="_moose_action_params"

    def __init__(self):
        print("I am an action")
