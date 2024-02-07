from abc import ABC
from collections.abc import Iterable
from .param import MooseParam
from .string import MooseString

class MooseBase(ABC,MooseString):
    """
    Class that can add type-checked properties to itself.
    """
    def __setattr__(self, attr_name, value_in):
        value_to_set=value_in
        if hasattr(self,attr_name):
            attr_val_now=getattr(self,attr_name)
            type_now=type(attr_val_now)

            sub_type_now=None
            if issubclass(type_now, Iterable) and type_now != str :
                sub_type_now=type(attr_val_now[0])

            if not isinstance(value_in,type_now):
                # If not the right type, try to cast
                values=None
                if isinstance(value_in,str):
                    values=value_in.split()

                try:
                    if sub_type_now is not None:
                        if values:
                            value_to_set=[ sub_type_now(v) for v in values ]
                        else:
                            value_to_set=[sub_type_now(value_in)]
                    else:
                        value_to_set=type_now(value_in)
                except ValueError:
                    msg="Attribute {} should have type {}".format(attr_name,type_now)
                    raise ValueError(msg)
        super().__setattr__(attr_name, value_to_set)


    @staticmethod
    def check_type(name, val, attr_type):
        """Checks a value's type"""
        if not isinstance(val, attr_type):
            val_type_str = val.__class__.__name__
            exp_type_str = attr_type.__name__
            raise ValueError(f'Incorrect type "{val_type_str}" for attribute "{name}". '
                             f'Expected type "{exp_type_str}".')
        return val

    @staticmethod
    def check_vals(name, val, allowed_vals):
        """Checks that a value is in the set of allowed_values"""
        if val not in allowed_vals:
            raise ValueError(f'Value {val} for attribute {name} is not one of {allowed_vals}')

    @classmethod
    def add_moose_param(cls,moose_param):
        assert isinstance(moose_param,MooseParam)

        # Check name
        attr_name=moose_param.name
        if attr_name.find("_syntax_") != -1:
            msg="'_syntax_' is reserved attribute string. Cannot create attibute {}".format(attr_name)
            raise RuntimeError(msg)

        # Store attribute in dict
        params_name=None
        if cls.params_name:
            if not hasattr(cls,cls.params_name):
                setattr(cls,cls.params_name,{})
            moose_param_dict_local=getattr(cls,cls.params_name)
            moose_param_dict_local[attr_name]=moose_param
            setattr(cls,cls.params_name,moose_param_dict_local)

    def get_param(self,attr_name):
        """Return MooseParam corresponding to attribute name.

        Raise KeyError if not found.
        """
        dict_now=getattr(self,self.params_name)
        return dict_now[attr_name]

    def is_default(self,attr_name):
        # Get current value
        attr_val = getattr(self, attr_name)

        # Look up the default value
        param=self.get_param(attr_name)
        default_val = param.default
        if default_val is None:

            default_val = param.attr_type()

        # Compare and return
        return attr_val == default_val

    def attr_to_str(self,attr_name,print_default=False):
        attr_str=""
        if self.is_default(attr_name) and not print_default:
            return attr_str

        attr_val=getattr(self, attr_name)
        if attr_val is None:
            return attr_str

        type_now=type(attr_val)
        attr_val_str=""
        if issubclass(type_now, Iterable) and type_now != str :
            str_list = [ str(v)+" " for v in attr_val ]
            attr_val_str="".join(str_list)
            attr_val_str=attr_val_str.rstrip()
            attr_val_str="'"+attr_val_str+"'"
        else:
            attr_val_str=str(attr_val)

        attr_str=self.indent+'{}='.format(attr_name)+attr_val_str+'\n'
        return attr_str

    @classmethod
    def moose_doc(cls, param_list):
        """Generate documentation for all the MOOSE parameters"""
        # Obtain class info for header
        class_string=''
        if hasattr(cls,'class_alias'):
            class_name_now=getattr(cls,'class_alias')
            class_string=" "+class_name_now
        param_string='MOOSE'+class_string+' Parameters'
        dash_len=len(param_string)
        dashes=''.ljust(dash_len,"-")

        # Write header
        doc_now=param_string
        doc_now+="\n"+dashes

        # Loop over parameters' documentation
        for param in param_list:
            assert isinstance(param,MooseParam)
            # We don't document the type as it is fixed
            if param.name == "type":
                continue
            doc_now=doc_now+param.doc

        # Footer
        more_dashes=''.ljust(65,"-")
        doc_now+=more_dashes
        doc_now+="\n"

        return doc_now
