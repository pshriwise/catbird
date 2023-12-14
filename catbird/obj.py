from .base import MooseBase

class MooseObject(MooseBase):
    _moose_params=[]

    def __init__(self):
        print("I am an object")

    # def set_syntax_name(self,syntax_name):
    #     self._syntax_name=syntax_name

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

    # @property
    # def moose_params(self):
    #     return self._moose_params

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
