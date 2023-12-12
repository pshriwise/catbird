from collections.abc import MutableSet
from .action import MooseAction
from .cbird import MooseObject
from .system import MooseSystem

class MooseCollection(MutableSet):
    """A collection of MOOSE objects"""
    def __init__(self):
        self.objects={}
        self._type=None

    # Define mandatory methods
    def __contains__(self,key):
        return key in self.objects.keys()

    def __iter__(self):
        return iter(self.objects)

    def __len__(self):
        return len(self.objects)

    def _check_type(self,obj):
        pass

    def add(self,obj):
        # Type checking on object, raise an error if fails
        self._check_type(obj)

        block_name=obj.syntax_block_name
        if block_name in self.objects.keys():
            msg="Collection already contains named block {}".format(block_name)
            raise RuntimeError(msg)

        # Index
        self.objects[block_name]=obj

    def discard(self,key):
        self.objects.pop(key)

    def to_str(self,print_default=False):
        collection_str="[{}]\n".format(self.__class__.__name__)
        for name, obj in self.objects.items():
            collection_str+=obj.to_str(print_default)
        collection_str+="[]\n"
        return collection_str

class MooseObjectCollection(MooseCollection):
    def __init__(self):
        super().__init__()

    def _check_type(self,obj):
        assert issubclass(type(obj),MooseObject)

class MooseActionCollection(MooseCollection):
    def __init__(self):
        super().__init__()

    def _check_type(self,obj):
        assert issubclass(type(obj),MooseAction)

class MooseSystemCollection(MooseCollection):
    def __init__(self):
        super().__init__()

    def _check_type(self,obj):
        assert issubclass(type(obj),MooseSystem)
