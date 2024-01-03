class MooseParam():
    """
    Class to contain all information about a MOOSE parameter
    """
    def __init__(self,attr_name, attr_type, dim=0, default=None, allowed_vals=None, description=None):
        self.attr_type=attr_type
        self.default=default
        self.allowed_vals=allowed_vals
        self.dim=dim

        # Set name
        if not isinstance(attr_name, str):
            raise ValueError('Attribute names must be strings')
        self.name=attr_name

        # Set value
        if default is not None:
            self.val=default
        else:
            self.val=attr_type()

        # Set docstring
        doc_str = '\n'
        doc_str += attr_name+' : '
        doc_str += f'{attr_type.__name__}\n'
        if description is not None and description != "":
            doc_str += "  "
            doc_str += description
            doc_str += "\n"
        if allowed_vals is not None:
            doc_str += f'  Allowed values: {allowed_vals}\n'
        if default is not None:
            doc_str += f'  Default value: {default}\n'

        self.doc=doc_str
