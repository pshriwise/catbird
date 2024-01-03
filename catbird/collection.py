from collections.abc import MutableSet
from .base import MooseBase
from .action import MooseAction
from .obj import MooseObject
from .string import MooseString

class MooseCollection(MutableSet,MooseString):
    """A collection of MOOSE objects"""
    def __init__(self):
        self.objects={}

    # Define mandatory methods
    def __contains__(self,key):
        return key in self.objects.keys()

    def __iter__(self):
        return iter(self.objects)

    def __len__(self):
        return len(self.objects)

    def _check_type(self,obj):
        assert issubclass(type(obj),MooseBase)

    def add(self,obj,lookup_name):
        # Type checking on object, raise an error if fails
        self._check_type(obj)

        # Set the name of the object
        obj.set_lookup_name(lookup_name)

        # Don't duplicate entries in collection
        if lookup_name in self.objects.keys():
            msg="Collection already contains named block {}".format(block_name)
            raise RuntimeError(msg)

        # Save
        self.objects[lookup_name]=obj

    def discard(self,key):
        self.objects.pop(key)

    def inner_to_str(self,print_default=False):
        inner_str=""
        for name, obj in self.objects.items():
            inner_str+=obj.to_str(print_default)
        return inner_str
