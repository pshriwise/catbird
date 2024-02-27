class MooseString():
    """Mixin to assist printing"""
    def set_lookup_name(self,name_in):
        self._lookup_name=name_in

    @property
    def lookup_name(self):
        """Optional property for externally set name"""
        if hasattr(self,"_lookup_name"):
            return self._lookup_name
        else:
            return None

    @property
    def print_name(self):
        """
        Return name for printing purposes
        """
        if self.lookup_name:
            return self.lookup_name

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
        """
        Inner indent string
        """
        indent_str=""
        for i_level in range(self.indent_level):
            # Use two space indent
            indent_str=indent_str+"  "
        return indent_str

    @property
    def prepend_indent(self):
        """
        Outer indent string
        """
        indent_str=""
        for i_level in range(self.indent_level-1):
            # Use two space indent
            indent_str=indent_str+"  "
        return indent_str

    def to_str(self,print_default=False):
        """
        Return syntax as a string
        """
        syntax_str='{}[{}]\n'.format(self.prepend_indent,self.print_name)
        syntax_str+=self.inner_to_str(print_default)
        syntax_str+='{}[]\n'.format(self.prepend_indent)
        return syntax_str

    def inner_to_str(self,print_default=False):
        # Override me
        pass

    def moose_doc(self):
        # Override me
        return ""
