from abc import ABC
from copy import deepcopy
import numpy as np

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

class Catbird(ABC):
    """
    Class to represent MOOSE syntax that can add type-checked properties to itself.
    """
    def __init__(self):
        self._syntax_name=""

    def set_syntax_name(self,syntax_name):
        self._syntax_name=syntax_name

    # @classmethod
    # def set_syntax_type(cls,syntax_type):
    #     cls._syntax_type=syntax_type

    # @classmethod
    # def set_syntax_category(cls,syntax_category):
    #     cls._syntax_category=syntax_category

    # @property
    # def syntax_block_name(self):
    #     if self.is_nested:
    #         return self._syntax_name
    #     else:
    #         return self._syntax_category

    # @property
    # def indent_level(self):
    #     if self.is_nested:
    #         return 2
    #     else:
    #         return 1

    # @property
    # def is_nested(self):
    #     return self._syntax_type =="nested" or self._syntax_type=="nested_system"

    @property
    def moose_params(self):
        return self._moose_params

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

    @staticmethod
    def moose_property(name, param):
        """
        Returns a property, and creates an associated class attribute whose value is that of the supplied MooseParam.

        The property setter method will change the value of the underlying MooseParam.value, checking its type is consistent
        The property getter method will retrieve the value of the underlying MooseParam.value
        """

        def fget(self):
            # set to the default value if the internal attribute doesn't exist
            if not hasattr(self, '_'+name):
                setattr(self, '_'+name, param)
            param_now = getattr(self, '_'+name)
            return param_now.val

        def fset(self, val):
            if param.dim == 0:
                self.check_type(name, val, param.attr_type)
                if param.allowed_vals is not None:
                    self.check_vals(name, val, param.allowed_vals)
            else:
                val = np.asarray(val)
                self.check_type(name, val.flat[0].item(), param.attr_type)
                if len(val.shape) != param.dim:
                    raise ValueError(f'Dimensionality is incorrect. Expects a {dim}-D array.')
                for v in val.flatten():
                    if param.allowed_vals is not None:
                        self.check_vals(name, v, allowed_vals)

            param_now = getattr(self, '_'+name)
            param_now.val=val
            setattr(self, '_'+name, param_now)

        def fdel(self):
            param_now = getattr(self, '_'+name)
            del param_now


        return property(fget,fset,fdel,param.doc)

    # @staticmethod
    # def prop_get(name, default=None):
    #     """Returns function for getting an attribute"""
    #     def fget(self):
    #         # set to the default value if the internal attribute doesn't exist
    #         if not hasattr(self, '_'+name):
    #             setattr(self, '_'+name, default)
    #         value = getattr(self, '_'+name)
    #         return value
    #     return fget

    # @staticmethod
    # def prop_set(name, attr_type, dim=0, allowed_vals=None,doc=""):
    #     """Returns a function for setting an attribute"""
    #     def fset(self, val):
    #         if dim == 0:
    #             self.check_type(name, val, attr_type)
    #             if allowed_vals is not None:
    #                 self.check_vals(name, val, allowed_vals)
    #             setattr(self, '_'+name, val)
    #             #setattr(self, '_'+name, val)
    #         else:
    #             val = np.asarray(val)
    #             self.check_type(name, val.flat[0].item(), attr_type)
    #             if len(val.shape) != dim:
    #                 raise ValueError(f'Dimensionality is incorrect. Expects a {dim}-D array.')
    #             for v in val.flatten():
    #                 if allowed_vals is not None:
    #                     self.check_vals(name, v, allowed_vals)
    #             setattr(self, '_'+name, val)
    #     return fset

    # @staticmethod
    # def prop_doc(name, doc_str=""):
    #     def fdoc(self):
    #         print("retrieve doc")
    #         doc_str_now=""
    #         if doc_str != "":
    #             doc_str_now=doc_str
    #         else:
    #             value = getattr(self, '_'+name)
    #             doc_str_now=value.__doc__
    #         return doc_str_now
    #     return fdoc

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

        # Define a property and add to class (args are functions)
        # Should be able to add a docstring here....
        #prop = property(fget=cls.prop_get(attr_name, default),
        #                fset=cls.prop_set(attr_name, attr_type, dim, allowed_vals, doc_str))
        #setattr(cls, attr_name, prop)

        # Add attribute to the class using a method which returns a property
        setattr(cls, attr_name, cls.moose_property(attr_name,moose_param))

        # Keep track of the attributes we've added
        if not hasattr(cls,"_moose_params"):
            setattr(cls,"_moose_params",[])
        moose_param_list_local=getattr(cls,"_moose_params")
        moose_param_list_local.append(attr_name)
        setattr(cls,"_moose_params",moose_param_list_local)

    # # Todo - waspify
    # def to_node(self):
    #     """
    #     Create a pyhit node for this MOOSE object
    #     """
    #     import pyhit

    #     node = pyhit.Node(hitnode=self.__class__.__name__)

    #     for attr in self.__moose_attrs__:
    #         val = getattr(self, attr)

    #         getattr(self, '_'+name)
    #         if val is not None:
    #             node[attr] = val

    #     return node

    @property
    def indent(self):
        indent_str=""
        indent_per_level="  "
        for i_level in range(0,self.indent_level):
            indent_str+=indent_per_level
        return indent_str

    @property
    def prepend_indent(self):
        indent_str=""
        indent_per_level="  "
        if self.indent_level > 1:
            for i_level in range(0,self.indent_level-1):
                indent_str+=indent_per_level
        return indent_str

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
            attr_val = getattr(self, attr_name)
            attr_str=self.indent+'{}={}\n'.format(attr_name,attr_val)
        return attr_str

    def to_str(self,print_default=False):
        syntax_str='{}[{}]\n'.format(self.prepend_indent,self.syntax_block_name)
        param_list=self.moose_params

        # Formatting convention, start with type
        if "type" in  param_list:
            param_list.remove("type")
        syntax_str+=self.attr_to_str("type",True)

        for attr_name in param_list:
            syntax_str+=self.attr_to_str(attr_name,print_default)
        syntax_str+='{}[]\n'.format(self.prepend_indent)

        return syntax_str

    def print_me(self):
        name=self.block_name
        print("Name: ",name)

        param_list=self.moose_params
        for attr_name in param_list:
            attr_val = getattr(self, attr_name)
            if attr_val is not None:
                attr_str="{}.{}: {}".format(name,attr_name,attr_val)
            else:
                attr_str="{}.{}: None".format(name,attr_name)
            print(attr_str)

