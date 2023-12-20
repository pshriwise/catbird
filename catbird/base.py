from abc import ABC
from .string import MooseString

class MooseParam():
    """
    Class to contain all information about a MOOSE parameter
    """
    def __init__(self):
        self.val=None
        self.attr_type=None
        self.default=None
        self.allowed_vals=None
        self.dim=0
        self.doc=""

# class MyDescriptor:
#     def __init__(self, value, attr_type, dim):
#         self._value = value
#         self._attr_type=attr_type
#         self._dim=dim

#     def __get__(self, owner_instance, owner_type):
#         print("We're getting from MyDescriptor")
#         return owner_instance._value

#     def __set__(self, owner_instance, value):
#         print("We're setting from MyDescriptor")
#         value_to_set=value
#         if isinstance(value,MyDescriptor):
#             value_to_set=value._value

#         if self._.dim == 0:
#             self.check_type(value_to_set,self._attr_type)
#             #             if param.allowed_vals is not None:
#             #                 obj.check_vals(name, val, param.allowed_vals)
#         else:
#             val = np.asarray(value_to_set)
#             self.check_type(val.flat[0].item(), self._attr_type)
#             if len(val.shape) != param.dim:
#                 raise ValueError(f'Dimensionality is incorrect. Expects a {dim}-D array.')
#             #             for v in val.flatten():
#             #                 if param.allowed_vals is not None:
#             #                     obj.check_vals(name, v, allowed_vals)
#         self._value = value_to_set

#     @staticmethod
#     def check_type(val, attr_type):
#         """Checks a value's type"""
#         if not isinstance(val, attr_type):
#             val_type_str = val.__class__.__name__
#             exp_type_str = attr_type.__name__
#             raise ValueError(f'Incorrect type "{val_type_str}".'
#                              f'Expected type "{exp_type_str}".')

#     @staticmethod
#     def check_vals(val, allowed_vals):
#         """Checks that a value is in the set of allowed_values"""
#         if val not in allowed_vals:
#             raise ValueError(f'Value {val} is not one of {allowed_vals}')

class MooseBase(ABC,MooseString):
    """
    Class that can add type-checked properties to itself.
    """
    def __setattr__(self, attr_name, value):
        if hasattr(self,attr_name):
            type_now=type(getattr(self,attr_name))
            if not isinstance(value,type_now):
                msg="Attribute {} should have type {}".format(attr_name,type_now)
                raise ValueError(msg)
        super().__setattr__(attr_name, value)

    # def __getattribute__(self, attr):
    #     print("We're here")
    #     # If the attribute does not exist, super().__getattribute__()
    #     # will raise an AttributeError
    #     got_attr = super().__getattribute__(attr)
    #     try:
    #         # Try "manually" invoking the descriptor protocol __get__()
    #         return got_attr.__get__(self, type(self))
    #     except AttributeError:
    #         # Attribute is not a descriptor, just return it:
    #         return got_attr


    def __init__(self):
        print("In the MooseBase init method of ",self.__class__.__name__)

        # List of the attributes this class should have
        moose_param_dict_local=getattr(self,self.params_name)

        # Loop over and make into properties
        for attr_name, moose_param in moose_param_dict_local.items():
            # Crucially, acts on the instance, not the class.
            setattr(self,attr_name,moose_param.val)

            # print("  Adding property: ",attr_name)

            # # Property object (hopefully acts on OBJ)
            # new_prop=self.moose_property(self,attr_name,moose_param)
            # self.add_as_property(self,attr_name,new_prop)


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

    # @staticmethod
    # def moose_property(obj,name,param):
    #     """
    #     Returns a property, and creates an associated class attribute whose value is that of the supplied MooseParam.

    #     The property setter method will change the value of the underlying MooseParam.value, checking its type is consistent
    #     The property getter method will retrieve the value of the underlying MooseParam.value
    #     """

    #     def fget(self):
    #         # set to the default value if the internal attribute doesn't exist
    #         if not hasattr(obj, '_'+name):
    #             setattr(obj, '_'+name, param)
    #         param_now = getattr(obj, '_'+name)
    #         return param_now.val

    #     def fset(self, val):
    #         print("setting", obj.lookup_name)
    #         if param.dim == 0:
    #             obj.check_type(name, val, param.attr_type)
    #             if param.allowed_vals is not None:
    #                 obj.check_vals(name, val, param.allowed_vals)
    #         else:
    #             val = np.asarray(val)
    #             obj.check_type(name, val.flat[0].item(), param.attr_type)
    #             if len(val.shape) != param.dim:
    #                 raise ValueError(f'Dimensionality is incorrect. Expects a {dim}-D array.')
    #             for v in val.flatten():
    #                 if param.allowed_vals is not None:
    #                     obj.check_vals(name, v, allowed_vals)

    #         param_now = getattr(obj, '_'+name)
    #         param_now.val=val
    #         setattr(obj, '_'+name, param_now)

    #     def fdel(self):
    #         param_now = getattr(obj, '_'+name)
    #         del param_now


    #     return property(fget,None,fdel,param.doc)

    @classmethod
    def newattr(cls, attr_name, attr_type=str, dim=0, default=None, allowed_vals=None, description=None):
        """Adds a property to the class"""
        if not isinstance(attr_name, str):
            raise ValueError('Attributes must be strings')

        if attr_name.find("_syntax_") != -1:
            msg="'_syntax_' is reserved attribute string. Cannot add attibute {}".format(attr_name)
            raise RuntimeError(msg)

        # Set attribute docstring
        doc_str = f'\nType: {attr_type.__name__}\n'
        if description is not None:
            doc_str += description
        if allowed_vals is not None:
            doc_str += f'\nValues: {allowed_vals}'

        # Store parameter details in a structure
        moose_param=MooseParam()
        if default is not None:
            moose_param.val=default
        else:
            moose_param.val=attr_type()
        moose_param.attr_type=attr_type
        moose_param.default=default
        moose_param.dim=dim
        moose_param.allowed_vals=allowed_vals
        moose_param.doc=doc_str

        # Store attribute in dict
        params_name=None
        if cls.params_name:
            if not hasattr(cls,cls.params_name):
                setattr(cls,cls.params_name,{})
            moose_param_dict_local=getattr(cls,cls.params_name)
            moose_param_dict_local[attr_name]=moose_param
            setattr(cls,cls.params_name,moose_param_dict_local)


    @staticmethod
    def add_as_property(obj,attr_name,property_obj):
        setattr(obj, attr_name, property_obj)

    def is_default(self,attr_name):
        attr_val = getattr(self, attr_name)
        param = getattr(self, "_"+attr_name)
        default_val = param.default
        if default_val is None:
            default_val = param.attr_type()
        return attr_val == default_val

    def attr_to_str(self,attr_name,print_default=False):
        attr_str=""
        if self.is_default(attr_name) and not print_default:
            return attr_str

        attr_val = getattr(self, attr_name)
        if attr_val is not None:
            attr_str=self.indent+'{}={}\n'.format(attr_name,attr_val)
        return attr_str

    def moose_doc(self):
        doc_now="Custom MooseBase docstring\n"
        #     moose_param_dict_local={}
        #     if hasattr(self,"_moose_params"):
        #         moose_param_dict_local=getattr(self,"_moose_params")
        #     for attr_name, param in moose_param_dict_local.items():
        #         doc_now=doc_now+param.doc
        #     docs_now=super().__doc__+doc_now
        return doc_now
