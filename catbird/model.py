from .cbird import SyntaxBlock, parse_blocks, parse_blocks_types, read_json, write_json

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

    def construct(obj_type):
        return self.constructors[obj_type]()

    def enable_syntax(self,syntax_name,enabled_types="all"):
        if syntax_name not in self.available_blocks.keys():
            msg="Cannot enable unknown syntax {}".format(syntax_name)
            raise RuntimeError(msg)

        self.available_blocks[syntax_name].enabled=True

        enabled_type_list=list()
        if isinstance(enabled_types,list):
            enabled_type_list=enabled_types
        elif enabled_types=="all":
            enabled_type_list=list(self.available_blocks[syntax_name].enabled_types.keys())
        else:
            msg="Invalid format for enabled_types, type = {}".format(type(enabled_types))
            raise RuntimeError(msg)

        for current_type in enabled_type_list:
            self.available_blocks[syntax_name].enabled_types[current_type]=True


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
        self.enable_syntax("Mesh",enabled_types=["FileMesh","GeneratedMesh"])
        self.enable_syntax("Executioner",enabled_types=["Steady","Transient"])
        self.enable_syntax("Problem",enabled_types=["FEProblem"])
        self.enable_syntax("Variables",enabled_types=["MooseVariable"])

class MooseModel():
    def __init__(self,json_obj,config_file=None):
        self.moose_objects={}
        # Create a factory for moose objects and possibly configure from file
        self.factory=Factory(json_obj,config_file)
        self.set_defaults()
        self.create_all_objects()

    def set_defaults(self):
        self.add_to_model("Executioner", "Steady")
        self.add_to_model("Problem", "FEProblem")
        self.add_to_model("Mesh", "GeneratedMesh")

    def create_all_objects(self):
        for category, selected in self.moose_objects:
            self.add_object(selected)

    def add_object(self, object_type):
        obj=self.factory.construct(object_type)
        # Prefer non-capitalised attributes
        attr_name=category.lower()
        setattr(self, attr_name, cat_instance)

    def add_to_model(self, category, category_type):
        #if category not in self.moose_objects.keys():
        #    self.moose_objects[category]=list()
        self.moose_objects[category]=category_type

        # TODO enforce
        # Cases: if fundamental , just one
        # Cases: if nested , list


    def add_fundmental_blocks(self):
        # Executioner, problem, etc ..
        for fundamental_block in self.factory.fundamental_syntax :
            #self.add_object(fundamental_block)

            raise NotImplementedError

        # User Call me in inherited class or model file...
    def add_nested_block(self):
        # Variables, kernels
        # Just one type
        raise NotImplementedError

    # Some short-hands for common operations
    def add_variable(self):
        raise NotImplementedError

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
