from .base import MooseBase

class MooseAction(MooseBase):
    params_name="_moose_action_params"
    class_alias="Action"

    def __init__(self):
        if hasattr(self,"_action_moose_params"):
            # Dictionary of the attributes this class should have
            moose_param_dict_local=getattr(self,"_moose_action_params")

            # Loop over and make into attributes
            for attr_name, moose_param in moose_param_dict_local.items():
                # Crucially, acts on the instance, not the class.
                setattr(self,attr_name,moose_param.val)

    @property
    def moose_action_params(self):
        """
        Return a unified list of all the parameters we've added.
        """
        moose_param_list_local=[]
        if hasattr(self,"_moose_action_params"):
            moose_param_dict_local=getattr(self,"_moose_action_params")
            moose_param_list_local=list(moose_param_dict_local.keys())
        return moose_param_list_local

    def inner_to_str(self,print_default=False):
        inner_str=""
        param_list=self.moose_action_params

        # We don't print the type of actions
        if "type" in  param_list:
            param_list.remove("type")

        for attr_name in param_list:
            inner_str+=self.attr_to_str(attr_name,print_default)
        return inner_str
