from .collection import MOOSECollection
from .factory import Factory

class MooseModel():
    """Class to represent a MOOSE model"""
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
        raise NotImplementedError
        
        # # Construct object
        # obj=self.factory.construct(collection_type,object_type,**kwargs)
        # if syntax_name=="":
        #     raise RuntimeError("Must supply syntax_name for nested syntax")

        # obj.set_syntax_name(syntax_name)

        # # Obtain the object for this collection type
        # collection = getattr(self, collection_type.lower())

        # # Store in collection
        # collection.add(obj)

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
