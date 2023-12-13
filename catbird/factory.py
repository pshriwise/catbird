from .syntax import SyntaxRegistry, parse_block
from .utils import read_json, write_json, json_from_exec

class Factory():
    """Class to contain constructors for MOOSE syntax objects"""
    def __init__(self,exec_path,config_file=None):
        json_obj=json_from_exec(exec_path)
        self.registry=SyntaxRegistry(json_obj)
        self.available_blocks=self.registry.get_available_blocks()
        self.set_defaults()
        # if config_file is not None:
        #     self.load_config(config_file)
        self.load_enabled_objects(json_obj)

    def _load_root_syntax(self,block_name, block):
        """
        Retreive a tuple of abstract classes to mix to form our root syntax node.
        """
        assert block.is_root and block.enabled
        self.root_syntax[block.name]=block.get_mixins()

    def _load_leaf_syntax(self,block_name, block,json_obj):
        """
        Retreive a class with attributes matching the available syntax for the block.
        """
        assert block.is_leaf and block.enabled

        # Convert string to SyntaxPath
        syntax_path=self.registry.syntax_dict[block_name]

        # Fetch syntax for block and make a new object type
        new_class=parse_block(json_obj,syntax_path)

        # Some details about the type of object
        class_name=syntax_path.name
        parent_name=syntax_path.parent_path[-1]
        relation=block.relation_key
        if parent_name not in self.constructors.keys():
            self.constructors[parent_name]={}
        if relation not in self.constructors[parent_name].keys():
            self.constructors[parent_name][relation]={}

        if class_name in self.constructors[parent_name][relation].keys():
            raise RuntimeError("Duplicated class name {} in namespace {}.{}".format(class_name,parent_name,relation))

        # Save class constructor
        self.constructors[parent_name][relation][class_name]=new_class

    def load_enabled_objects(self,json_obj):
        self.constructors={}
        self.root_syntax={}

        # Loop over enabled syntax blocks
        for block_name, block in self.available_blocks.items():
            if  not  block.enabled:
                continue

            if block.is_leaf:
                self._load_leaf_syntax(block_name, block, json_obj)
            elif  block.is_root:
                self._load_root_syntax(block_name, block)
            else:
                print(block_name)

    @staticmethod
    def __get_init_method(mixins):
        # The returned init method should call each of the mix-in base class init methods in turn.
        def __init__(self, *args, **kwargs):
            for base in mixins:
                base.__init__(self, *args, **kwargs)
        return __init__

    def derive_class(self,root_name,obj_types):
        """
        Form a new mix-in class from a tuple of classes

        Parameters
        ----------
        rootname : str
        obj_types: dict
        """

        # Get mixins boilerplate
        mixins=self.root_syntax[root_name]

        # Update mixins list by comparing types
        for relation_type, obj_type in obj_types.items():
            # Look up type
            class_now=self.constructors[root_name][relation_type][obj_type]
            for i_mixin, mixin in enumerate(mixins):
                if issubclass(class_now,mixin):
                    mixins[i_mixin]=class_now
                    break

        # Our fancy new mixin class
        # TODO: define to_dict...
        new_cls = type(root_name, tuple(mixins),{"__init__":self.__get_init_method(mixins)})
        return new_cls

    def construct_root(self,root_name,obj_types,kwargs):
        """
        Parameters
        ----------
        rootname : str
        obj_types: dict
        kwargs: dict
        """
        # Get class
        obj_class=self.derive_class(root_name, obj_types)
        obj=obj_class()

        # Handle keyword arguments
        for key, value in kwargs.items():
            if not hasattr(obj,key):
                msg="Object type {} does not have attribute {}".format(root_name,key)
                raise RuntimeError()
            setattr(obj, key, value)

        return obj

    def enable_syntax(self,block_name,enable_dict=None):
        """
        Configure what MOOSE syntax to enable.

        Objects with enabled syntax will be converted to Python classes.
        """
        # Construct full name
        syntax_name="blocks/"+block_name

        # Check syntax is known
        if syntax_name not in self.available_blocks.keys():
            msg="Cannot enable unknown syntax {}".format(syntax_name)
            raise RuntimeError(msg)

        # Enable top level block syntax
        self.available_blocks[syntax_name].enabled=True
        block_now=self.available_blocks[syntax_name]

        # Enable sub-block types
        available_sub_syntax=self.registry.get_available_syntax(syntax_name)
        for syntax_shortname, syntax_list in available_sub_syntax.items():

            # If provided, only enable user-specified types
            if enable_dict and syntax_shortname not in enable_dict.keys():
                continue

            for syntax_item in syntax_list:
                if enable_dict and syntax_item not in enable_dict[syntax_shortname]:
                    continue

                # Get longname and enable
                enable_key=block_now.path_to_child(syntax_shortname,syntax_item)
                self.available_blocks[enable_key].enabled=True


    def write_config(self,filename,print_depth=3,verbose=False):
        config_dict={}
        for block_name, block in self.available_blocks.items():
            config_entry=block.to_dict(print_depth,verbose)
            if config_entry is not None:
                config_dict.update(config_entry)
        write_json(config_dict,filename)

    def load_config(self,filename):
        # Fetch enabled objects from filename
        config_in=read_json(filename)
        for block_name, block_dict in config_in.items():
            self.available_blocks[block_name].enabled=block_dict["enabled"]

    def set_defaults(self):
        self.enable_syntax("Mesh")
        self.enable_syntax("Executioner")
        self.enable_syntax("Problem")
        self.enable_syntax("Variables")
