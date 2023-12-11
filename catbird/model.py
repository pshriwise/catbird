from .cbird import SyntaxRegistry, SyntaxBlock, parse_block, read_json, write_json, json_from_exec
from .collection import MOOSECollection

class Factory():
    def __init__(self,exec_path,config_file=None):
        json_obj=json_from_exec(exec_path)
        self.registry=SyntaxRegistry(json_obj)
        self.available_blocks=self.registry.get_available_blocks()
        self.set_defaults()
        # if config_file is not None:
        #     self.load_config(config_file)
        self.load_enabled_objects(json_obj)

    def load_enabled_objects(self,json_obj):
        self.constructors={}
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

    def construct(self,namespace,obj_type,**kwargs):
        obj=self.constructors[namespace][obj_type]()

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

    #     self.enable_syntax("Mesh",default="FileMesh",enabled_types=["FileMesh","GeneratedMesh"])
    #     self.enable_syntax("Executioner",default="Steady",enabled_types=["Steady","Transient"])
    #     self.enable_syntax("Problem",default="FEProblem",enabled_types=["FEProblem"])
    #     self.enable_syntax("Variables",default="MooseVariable",enabled_types=["MooseVariable"])

class MooseModel():
    def __init__(self,factory_in):
        assert isinstance(factory_in,Factory)
        self.factory=factory_in

        # Add attributes to this model with default assignments
        self.moose_objects={}
        self.set_defaults()

    # Envisage this being overridden downstream.
    def set_defaults(self):
        self.add_object("Executioner", "Steady")
        self.add_object("Problem", "FEProblem")
        self.add_object("Mesh", "GeneratedMesh")

    #def  add_category(self, category, category_type, syntax_name=""):
    # # Ensure this is valid syntax
        # if category not in self.factory.constructors.keys():
        #     msg="Invalid block type {}".format(category)
        #     raise RuntimeError(msg)

        # # First look up the syntax type
        # syntax_type=self.factory.available_blocks[category].syntax_type

        # # How to add depends on syntax type
        # if syntax_type == "fundamental":
        #     # If fundmantal, just add. We're done.
        #     self.add_object(category,category_type)
        # elif syntax_type == "nested":
        #     if not hasattr(self,category):
        #         self.add_collection(category)
        #     self.add_to_collection(category,category_type,syntax_name)
        # elif syntax_type == "system":
        #     raise NotImplementedError()
        # elif syntax_type == "nested_system":
        #     raise NotImplementedError()
        # else:
        #     msg="Unhandled syntax type {}".format(syntax_type)
        #     raise RuntimeError(msg)

        # # Object has been constructed, now just book-keeping
        # category_key=category.lower()
        # if category_key not in self.moose_objects.keys():
        #     self.moose_objects[category_key]=list()
        # self.moose_objects[category_key].append(category_type)

    def add_object(self,namespace,object_type,**kwargs):
        obj=self.factory.construct(namespace,object_type,**kwargs)
        # Prefer non-capitalised attributes
        attr_name=namespace.lower()
        setattr(self,attr_name,obj)

    def add_collection(self, collection_type):
        # E.g. Variables, Kernels, BCs, Materials
        # Create new subclass of with a name that matches the collection_type
        new_cls = type(collection_type, (MOOSECollection,), dict())

        # Prefer non-capitalised attributes
        attr_name=collection_type.lower()

        # Construct and add the to model
        setattr(self, attr_name, new_cls())

    def add_to_collection(self, collection_type, object_type, syntax_name, **kwargs):
        # Construct object
        obj=self.factory.construct(object_type,**kwargs)
        if syntax_name=="":
            raise RuntimeError("Must supply syntax_name for nested syntax")

        obj.set_syntax_name(syntax_name)

        # Obtain the object for this collection type
        collection = getattr(self, collection_type.lower())

        # Store in collection
        collection.add(obj)

    # Some short-hands for common operations
    def add_variable(self,name,variable_type="MooseVariable"):
        raise NotImplementedError
        #self.add_category("Variables",variable_type,name)

    def add_bc(self):
        raise NotImplementedError

    def add_ic(self):
        raise NotImplementedError

    def to_str(self,print_default=False):
        model_str=""
        for obj_type in self.moose_objects:
            obj=getattr(self,obj_type)
            model_str+=obj.to_str(print_default)
        return model_str

    def write(self, filename):
        file_handle = open(filename,'w')
        file_handle.write(self.to_str())
        file_handle.close()
        print("Wrote to ",filename)
