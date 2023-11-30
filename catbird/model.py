from .cbird import SyntaxBlock, parse_blocks, parse_blocks_types, read_json, write_json
from .collection import MOOSECollection

class Factory():
    def __init__(self,json_obj,config_file=None):
        self.available_blocks=parse_blocks(json_obj)
        self.constructors={}
        self.set_defaults()
        if config_file is not None:
            self.load_config(config_file)
        self.load_enabled_objects(json_obj)

    def load_enabled_objects(self,json_obj):
        for enabled_block in self.enabled_syntax:
            enabled_types=self.available_blocks[enabled_block].enabled_subblocks
            syntax_type=self.available_blocks[enabled_block].syntax_type
            if syntax_type=="fundamental" or syntax_type=="nested":
                self.constructors.update(parse_blocks_types(json_obj,enabled_block,category_names=enabled_types))
            else:
                msg="Unsupported syntax type {}".format(syntax_type)
                raise NotImplementedError(msg)

    def construct(self,obj_type,**kwargs):
        obj=self.constructors[obj_type]()

        # Handle keyword arguments
        for key, value in kwargs.items():
            if not hasattr(obj,key):
                msg="Object type {} does not have attribute {}".format(obj_type,key)
                raise RuntimeError()
            setattr(obj, key, value)

        return obj

    def enable_syntax(self,syntax_name,default=None,enabled_types="all"):
        """
        Configure what MOOSE syntax to enable.

        Objects with enabled syntax will be converted to Python classes.
        """
        # Check syntax is known
        if syntax_name not in self.available_blocks.keys():
            msg="Cannot enable unknown syntax {}".format(syntax_name)
            raise RuntimeError(msg)

        # Enable top level block syntax
        self.available_blocks[syntax_name].enabled=True

        # Enable sub-block types
        enabled_type_list=list()
        if isinstance(enabled_types,list):
            enabled_type_list=enabled_types
        elif enabled_types=="all":
            enabled_type_list=list(self.available_blocks[syntax_name].enabled_types.keys())
        else:
            msg="Invalid format for enabled_types, type = {}".format(type(enabled_types))
            raise RuntimeError(msg)

        # Ensure default is enabled
        if default not in enabled_type_list and default is not None:
            enabled_type_list.append(default)

        for current_type in enabled_type_list:
            # Ensure valid
            if current_type not in self.available_blocks[syntax_name].enabled_types.keys():
                msg="Unknown type {} for block {}".format(current_type,syntax_name)
                raise KeyError(msg)

            self.available_blocks[syntax_name].enabled_types[current_type]=True

        # Set default for typed blocks
        syntax_type = self.available_blocks[syntax_name].syntax_type
        if default is not None:
            self.available_blocks[syntax_name].default_type=default
        elif syntax_type == "fundamental" or syntax_type == "nested":
            msg="Please set a default for typed blocks"
            raise RuntimeError(msg)


    def write_config(self,filename):
        config_dict={}
        for block_name, block in self.available_blocks.items():
            config_dict[block_name]=block.to_dict()
        write_json(config_dict,filename)

    def load_config(self,filename):
        config_in=read_json(filename)
        #read from file
        for block_name, block_dict in config_in.items():
            self.available_blocks[block_name].enable_from_dict(block_dict)

    @property
    def enabled_syntax(self):
        enabled=[ block_name  for  block_name, block in self.available_blocks.items() if block.enabled ]
        return enabled

    @property
    def fundamental_syntax(self):
        fundamental=[ block_name  for  block_name, block in self.available_blocks.items() if block.syntax_type=="fundamental"]
        return fundamental

    def set_defaults(self):
        self.enable_syntax("Mesh",default="FileMesh",enabled_types=["FileMesh","GeneratedMesh"])
        self.enable_syntax("Executioner",default="Steady",enabled_types=["Steady","Transient"])
        self.enable_syntax("Problem",default="FEProblem",enabled_types=["FEProblem"])
        self.enable_syntax("Variables",default="MooseVariable",enabled_types=["MooseVariable"])

class MooseModel():
    def __init__(self,json_obj,config_file=None):
        self.moose_objects={}
        # Create a factory for moose objects and possibly configure from file
        self.factory=Factory(json_obj,config_file)
        # Add attributes to this model with default assignments
        self.set_defaults()

    # Envisage this being overridden downstream.
    def set_defaults(self):
        # Fundamental Types
        self.add_category("Executioner", "Steady")
        self.add_category("Problem", "FEProblem")
        self.add_category("Mesh", "GeneratedMesh")

    def add_category(self, category, category_type, syntax_name=""):
        # Ensure this is valid syntax
        if category not in self.factory.enabled_syntax:
            msg="Invalid block type {}".format(category)
            raise RuntimeError(msg)

        # First look up the syntax type
        syntax_type=self.factory.available_blocks[category].syntax_type

        # How to add depends on syntax type
        if syntax_type == "fundamental":
            # If fundmantal, just add. We're done.
            self.add_object(category,category_type)
        elif syntax_type == "nested":
            if not hasattr(self,category):
                self.add_collection(category)
            self.add_to_collection(category,category_type,syntax_name)
        elif syntax_type == "system":
            raise NotImplementedError()
        elif syntax_type == "nested_system":
            raise NotImplementedError()
        else:
            msg="Unhandled syntax type {}".format(syntax_type)
            raise RuntimeError(msg)

        # Object has been constructed, now just book-keeping
        category_key=category.lower()
        if category_key not in self.moose_objects.keys():
            self.moose_objects[category_key]=list()
        self.moose_objects[category_key].append(category_type)

    def add_object(self,object_category,object_type,**kwargs):
        obj=self.factory.construct(object_type,**kwargs)
        # Prefer non-capitalised attributes
        attr_name=object_category.lower()
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
        model.add_category("Variables",name,variable_type)

    def add_bc(self):
        raise NotImplementedError

    def add_ic(self):
        raise NotImplementedError

    def to_str(self):
        model_str=""
        for obj_type in self.moose_objects:
            obj=getattr(self,obj_type)
            model_str+=obj.to_str()
        return model_str

    def write(self, filename):
        file_handle = open(filename,'w')
        file_handle.write(self.to_str())
        file_handle.close()
        print("Wrote to ",filename)
