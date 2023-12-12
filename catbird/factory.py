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
        self.load_root_syntax()
        self.load_enabled_objects(json_obj)

    def load_root_syntax(self):
        # Loop over enabled root nodes
        self.root_syntax={}
        for block_name, block in self.available_blocks.items():
            if  not ( block.enabled and block.is_root ):
                continue
            self.root_syntax[block.name]=block.get_mixins()

    def load_enabled_objects(self,json_obj):
        self.constructors={}
        # Loop over enabled leaf nodes
        for block_name, block in self.available_blocks.items():
            if  not ( block.enabled and block.is_leaf ):
                continue

            # Convert string to SyntaxPath
            syntax_path=self.registry.syntax_dict[block_name]

            # Fetch syntax for block and make a new object type
            new_class=parse_block(json_obj,syntax_path)

            # Some details about the type of object
            class_name=syntax_path.name
            namespace=syntax_path.parent_path[-1]
            if namespace not in self.constructors.keys():
                self.constructors[namespace]={}
            if class_name in self.constructors[namespace].keys():
                raise RuntimeError("Duplicated class name {} in namespace {}".format(class_name,namespace))

            # Save class constructor
            self.constructors[namespace][class_name]=new_class

    @staticmethod
    def __get_init_method(mixins):
        # Define an __init__ function for the class.
        def __init__(self, *args, **kwargs):
            # Call the __init__ functions of all the mix-ins
                for base in mixins:
                    base.__init__(self, *args, **kwargs)
        return __init__


    def derive_class(self,root_name,obj_types):
        # Get mixins boilerplate
        mixins=self.root_syntax[root_name]

        # Update mixins list by comparing types
        for obj_type in obj_types:
            class_now=self.constructors[root_name][obj_type]
            for i_mixin, mixin in enumerate(mixins):
                if issubclass(class_now,mixin):
                    mixins[i_mixin]=class_now
                    break

        # Our fancy new mixin class
        new_cls = type(root_name, tuple(mixins),{"__init__":self.__get_init_method(mixins)})
        return new_cls

    def construct_root(self,root_name,obj_types,kwargs):
        # Get class
        obj_class=self.derive_class(root_name, obj_types)
        obj=obj_class()

        # Handle keyword arguments
        for key, value in kwargs.items():
            if not hasattr(obj,key):
                msg="Object type {} does not have attribute {}".format(obj_type,key)
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
