from .syntax import SyntaxRegistry, parse_block
from .utils import read_json, write_json, json_from_exec

class Factory():
    """Class to contain constructors for MOOSE syntax objects"""
    def __init__(self,exec_path,config_file=None):
        print("Loading syntax from library...")
        json_obj=json_from_exec(exec_path)
        print("Done.")

        print("Constructing syntax registry...")
        self.registry=SyntaxRegistry(json_obj)
        print("Done.")

        self.available_blocks=self.registry.get_available_blocks()

        print("Configuring objects to enable...")
        self.set_defaults()
        print("Done.")

        # if config_file is not None:
        #     self.load_config(config_file)
        print("Loading enabled objects...")
        self.load_enabled_objects(json_obj)
        print("Done.")

    def _load_root_syntax(self,block_name, block):
        """
        Retreive a tuple of abstract classes to mix to form our root syntax node.
        """
        assert not block.is_leaf
        self.root_syntax[block.longname]=block.get_mixins()

    def _load_leaf_syntax(self,block_name,block,json_obj):
        """
        Retreive a class with attributes matching the available syntax for the block.
        """
        assert block.is_leaf

        # Some details about the type of object
        relation=block.relation_key
        class_name=block.name
        parent_name=block.parent_longname

        # Convert string to SyntaxPath
        syntax_path=self.registry.syntax_dict[block_name]

        # Fetch syntax for block and make a new object type
        new_class=parse_block(json_obj,syntax_path)

        # Ensure dictionary initialised
        if parent_name not in self.constructors.keys():
            self.constructors[parent_name]={}
        if relation not in self.constructors[parent_name].keys():
            self.constructors[parent_name][relation]={}

        # Don't duplicate
        if class_name in self.constructors[parent_name][relation].keys():
            raise RuntimeError("Duplicated class name {} in namespace {}.{}".format(class_name,parent_name,relation))

        # Save class constructor
        self.constructors[parent_name][relation][class_name]=new_class
        print("New constructor constructors[{}][{}][{}]".format(parent_name,relation,class_name))

    def load_enabled_objects(self,json_obj):
        self.constructors={}
        self.root_syntax={}

        # Loop over enabled syntax blocks
        for block_name, block in self.available_blocks.items():
            if  not  block.enabled:
                continue

            if  block.is_leaf:
                self._load_leaf_syntax(block_name, block, json_obj)
            else:
                self._load_root_syntax(block_name, block)

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
        mixin_list=[]
        for relation_type,derived_type in obj_types.items():
            if relation_type not in mixins.keys():
                raise RuntimeError("{} is not an available mix-in".format(relation_type))
            mixin_base_class=mixins[relation_type]

            # Fetch derived class for mix-in
            class_now=self.constructors[root_name][relation_type][derived_type]

            # Check provided object type is of the correct type
            if not issubclass(class_now,mixin_base_class):
                raise RuntimeError("{} has wrong base class".format(derived_type))

            mixin_list.append(class_now)

        # Our fancy new mixin class
        # TODO: define to_dict...
        new_cls = type(root_name, tuple(mixin_list),{"__init__":self.__get_init_method(mixins)})
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

        syntax_to_enable=[syntax_name]

        while len(syntax_to_enable)>0:
            # Get front of queue
            syntax_name_now=syntax_to_enable.pop(0)

            # Enable top level block syntax
            self.available_blocks[syntax_name_now].enabled=True

            # Get sub-block types
            block_now=self.available_blocks[syntax_name_now]

            available_sub_syntax=self.registry.get_available_syntax(syntax_name_now)
            if available_sub_syntax is not None:
                for relation_shortname, syntax_list in available_sub_syntax.items():
                    # If enable_dict is provided, only enable user-specified types
                    if enable_dict and relation_shortname not in enable_dict.keys():
                        continue

                    for syntax_item in syntax_list:
                        if enable_dict and syntax_item not in enable_dict[relation_shortname]:
                            continue

                        # Get syntax lookup key and add to queue
                        new_syntax=block_now.path_to_child(relation_shortname,syntax_item)
                        syntax_to_enable.append(new_syntax)


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
        #self.enable_syntax("Mesh")
        mesh_enable_dict={
            "action": ["CreateDisplacedProblemAction",
                       "DisplayGhostingAction"],
            "obj_type": ["FileMesh","GeneratedMesh"]
        }
        self.enable_syntax("Mesh",enable_dict=mesh_enable_dict)
        #self.enable_syntax("Executioner")
        #self.enable_syntax("Problem")
        #self.enable_syntax("Variables")
