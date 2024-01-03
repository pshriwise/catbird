from .base import MooseBase

class MooseObject(MooseBase):
    params_name="_moose_params"
    class_alias="Object"

    def __init__(self):
        super().__init__()

    @property
    def moose_object_params(self):
        """
        Return a unified list of all the parameters we've added.
        """
        moose_param_list_local=[]
        if hasattr(self,"_moose_params"):
            moose_param_dict_local=getattr(self,"_moose_params")
            moose_param_list_local=list(moose_param_dict_local.keys())
        return moose_param_list_local

    def inner_to_str(self,print_default=False):
        inner_str=""
        param_list=self.moose_object_params

        # Formatting convention, start with type
        if "type" in  param_list:
            param_list.remove("type")
        inner_str+=self.attr_to_str("type",True)

        for attr_name in param_list:
            inner_str+=self.attr_to_str(attr_name,print_default)
        return inner_str
