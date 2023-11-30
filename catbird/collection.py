from collections.abc import MutableSet
from .cbird import Catbird

class MOOSECollection(MutableSet):
    """A collection of MOOSE (Catbird) objects"""
    def __init__(self):
        self.objects={}

    # Define mandatory methods
    def __contains__(self,key):
        return key in self.objects.keys()

    def __iter__(self):
        return iter(self.objects)

    def __len__(self):
        return len(self.objects)

    def add(self,obj):
        # Ensure type inherits from Catbird
        assert issubclass(type(obj),Catbird)

        block_name=obj.syntax_block_name

        if block_name in self.objects.keys():
            msg="Collection already contains named block {}".format(block_name)
            raise RuntimeError(msg)

        # Index
        self.objects[block_name]=obj

    def discard(self,key):
        self.objects.pop(key)

    def to_str(self):
        collection_str="[{}]\n".format(self.__class__.__name__)
        for name, obj in self.objects.items():
            collection_str+=obj.to_str()
        collection_str+="[]\n"
        return collection_str
