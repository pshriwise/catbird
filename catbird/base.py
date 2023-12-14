from abc import ABC

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

class MooseBase(ABC):
    """
    Class that can add type-checked properties to itself.
    """
    def __init__(self):
        pass

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

        # Add attribute to the class using a method which returns a property
        setattr(cls, attr_name, cls.moose_property(attr_name,moose_param))

        # Keep track of the attributes we've added
        params_name=None
        if cls.params_name:
            if not hasattr(cls,cls.params_name):
                setattr(cls,cls.params_name,[])
            moose_param_list_local=getattr(cls,cls.params_name)
            moose_param_list_local.append(attr_name)
            setattr(cls,cls.params_name,moose_param_list_local)


    @property
    def moose_params(self):
        """
        Return a unified list of all the parameters we've added.
        """
        moose_param_list_local=[]
        if hasattr(self,"_moose_params"):
            moose_param_list_local.extend(getattr(self,"_moose_params"))

        if hasattr(self,"_moose_action_params"):
            moose_param_list_local.extend(getattr(self,"_moose_action_params"))

        return moose_param_list_local

    @property
    def print_name(self):
        """
        Return name for printing purposes
        """
        class_name=self.__class__.__name__
        class_path=class_name.split(sep=".")
        print_name=class_path[-1]
        return print_name

    @property
    def indent_level(self):
        """
        Return level of indent for printing purposes
        """
        class_name=self.__class__.__name__
        class_path=class_name.split(sep=".")
        indent_level=len(class_path)
        return indent_level

    @property
    def indent(self):
        indent_str=""
        for i_level in range(self.indent_level):
            # Use two space indent
            indent_str=indent_str+"  "
        return indent_str

    @property
    def prepend_indent(self):
        indent_str=""
        for i_level in range(self.indent_level-1):
            # Use two space indent
            indent_str=indent_str+"  "
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
            attr_str=self.indent+'{}={}\n'.format(attr_name,attr_val)
        return attr_str


    def to_str(self,print_default=False):
        syntax_str='{}[{}]\n'.format(self.prepend_indent,self.print_name)

        param_list=self.moose_params

        # Formatting convention, start with type
        if "type" in  param_list:
            param_list.remove("type")
        syntax_str+=self.attr_to_str("type",True)

        for attr_name in param_list:
            syntax_str+=self.attr_to_str(attr_name,print_default)
        syntax_str+='{}[]\n'.format(self.prepend_indent)

        return syntax_str
