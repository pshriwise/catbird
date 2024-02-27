"""Classes and functions to parse MOOSE syntax"""
from collections.abc import Iterable
from copy import deepcopy
from .obj import MooseObject
from .action import MooseAction
from .param import MooseParam
from .collection import *

type_mapping = {'Integer' : int,
                'Boolean' : bool,
                'Float' : float,
                'Real' : float,
                'String' : str,
                'Array' : list}

_relation_syntax=["blocks","subblocks","actions","star","types","subblock_types"]
_relation_shorthands={
    "types/":"obj_type",
    "actions/": "action",
    "subblocks/":"system",
    "star/subblock_types/":"collection_type",
    "star/actions/":"collection_action",
    "star/subblocks/":"nested_system",
    "star/star/actions/":"nested_collection_action",
    "star/star/subblock_types/":"nested_collection_type",
}

_mixin_map={
    "obj_type": MooseObject,
    "action": MooseAction,
    "system": MooseCollection,
    "collection_type" : MooseCollection,
    "collection_action": MooseCollection,
    "nested_system":  None, # The attribute should be added one layer down
    "nested_collection_action": None, # Don't support this syntax yet
    "nested_collection_type": None, # Don't support this syntax yet
}

_child_type_map={
    "obj_type": MooseObject,
    "action": MooseAction,
    "system": None,
    "collection_type" : MooseObject,
    "collection_action": MooseAction,
    "nested_system":  None,  # Don't support this syntax yet
    "nested_collection_action": None, # Don't support this syntax yet
    "nested_collection_type": None, # Don't support this syntax yet
}

_collection_type_map={
    "collection_type" : MooseObject,
    "collection_action": MooseAction,
}


def get_relation_kwargs():
    return _relation_shorthands.values()

class SyntaxPath():
    """
    A  helper class to store a path of keys from a nested dictionary structure.
    """
    def __init__(self, syntax_path_in):
        # Initial values
        self.name=""
        self.unique_key=""
        self.has_params=False
        self.is_root=False
        self.parent_path=None
        self.parent_relation=None
        self.child_paths={}
        self.path=deepcopy(syntax_path_in)


        syntax_path=deepcopy(syntax_path_in)

        # Type assertions
        assert isinstance(syntax_path,list)
        assert len(syntax_path)>1
        for key in syntax_path:
            assert isinstance(key,str)

        # Check for parameters
        pos_now=len(syntax_path)-1
        key_now = syntax_path.pop(pos_now)
        if key_now == "parameters":
            self.has_params=True
            self.path.pop(pos_now)
            pos_now=pos_now-1
            key_now = syntax_path.pop(pos_now)

        # Set object name
        self.name=key_now
        self.unique_key=self._get_lookup_key(syntax_path,key_now)

        if len(syntax_path) > 1 :
            relation_path=[]
            found_parent=False
            while not found_parent and len(syntax_path) > 0:
                pos_now=len(syntax_path)-1
                test_key=syntax_path.pop(pos_now)
                if test_key in _relation_syntax:
                    relation_path.insert(0,test_key)
                else:
                    found_parent=True
                    syntax_path.append(test_key)

            if not found_parent:
                raise RuntimeError("Should not get here")

            if relation_path:
                _parent_relation=self._key_from_list(relation_path)
                if _parent_relation not in _relation_shorthands.keys():
                    raise RuntimeError("unknown relation type: {}",format(_parent_relation))
                self.parent_relation=_parent_relation

            self.parent_path=syntax_path

        else:
            self.is_root=True


    def _key_from_list(self,path_in):
        path_str=""
        for key in path_in:
            path_str+=key
            path_str+="/"
        return path_str

    def _get_lookup_key(self,path_in,name_in):
        lookup_path=self._key_from_list(path_in)
        lookup_path+=name_in
        return lookup_path

    def add_child(self, child_syntax):
        assert isinstance(child_syntax,SyntaxPath)

        # Save mapping by relation type
        relation_key=_relation_shorthands[child_syntax.parent_relation]
        if relation_key not in self.child_paths.keys():
            self.child_paths[relation_key]=[]
        self.child_paths[relation_key].append(child_syntax.unique_key)

    def has_child_type(self,relation):
        return relation in self.child_paths.keys() and self.child_paths[relation] != None

    @property
    def parent_key(self):
        if not self.is_root:
            parent_path_now=deepcopy(self.parent_path)
            parent_len=len(parent_path_now)
            parent_name=parent_path_now.pop(parent_len-1)
            return self._get_lookup_key(parent_path_now,parent_name)
        else:
            return None

    @property
    def relation_to_parent(self):
        if self.parent_relation:
            relation=_relation_shorthands[self.parent_relation]
            return relation
        else:
            return None

class SyntaxBlock():
    """
    A class to represent one block of MOOSE syntax
    """
    def  __init__(self):
        self.name=""
        self.path=""
        self.has_params=False
        self.enabled=False
        self.available_syntax={}
        self.relation_key=None
        self.parent_blocks=[]
        self.depth=0

    def to_dict(self, print_depth=3, verbose=False):
        config_entry=None
        if ( self.enabled and self.depth < print_depth ) or verbose:
            block_dict={
                "name": self.name,
                "enabled": self.enabled,
                "params": self.has_params,
            }
            if verbose:
                if  self.available_syntax:
                    block_dict["available syntax"] = self.available_syntax
            #    if  self.parent_blocks:
            #        block_dict["parents"] =  self.parent_blocks

            config_entry= { self.path : block_dict }

        return config_entry

    @property
    def is_leaf(self):
        return self.available_syntax==None

    @property
    def is_root(self):
        return self.depth==0

    def path_to_child(self,relation_shortname,child_name):
        # Invert dictionary
        found=False
        relation_type=None
        for test_relation_type,test_shortname in _relation_shorthands.items():
            if relation_shortname == test_shortname:
                found=True
                relation_type=test_relation_type

        if not found:
            msg="No known relation syntax maps onto shortname {}".format(relation_shortname)
            raise RuntimeError(msg)
        path=self.path+"/"+relation_type+child_name
        return path

    def get_mixins(self):
        mixin_dict={}
        for relation_type in self.available_syntax.keys():
            mixin_now=_mixin_map[relation_type]
            if mixin_now is not None:
                mixin_dict[relation_type]=mixin_now
        return mixin_dict

    def get_collection_mixins(self):
        mixin_dict={}
        for relation_type in self.available_syntax.keys():
            if relation_type in _collection_type_map.keys():
                mixin_now=_collection_type_map[relation_type]
                if mixin_now is not None:
                    mixin_dict[relation_type]=mixin_now
        return mixin_dict

    @property
    def parent_longname(self):
        _longname=""
        for parent_name in self.parent_blocks:
            _longname=_longname+parent_name+"."
        _longname=_longname.rstrip(".")
        return _longname

    @property
    def longname(self):
        _longname=""
        for parent_name in self.parent_blocks:
            _longname=_longname+parent_name+"."
        _longname=_longname+self.name
        return _longname

    # def __init__(self, _name, _syntax_type, _known_types):
    #     self.name=_name
    #     self.syntax_type=_syntax_type
    #     self.enabled=False
    #     self.enabled_types={}
    #     if _known_types is not None:
    #         for known_type_name in _known_types:
    #             self.enabled_types[known_type_name]=False

    #     # Store what the default type should be
    #     self.default_type=None

    # def to_dict(self):
    #     syntax_dict={
    #         "name": self.name,
    #         "syntax_type": self.syntax_type,
    #         "enabled": self.enabled,
    #         "enabled_types": self.enabled_types,
    #     }
    #     return syntax_dict

    # @property
    # def enabled_subblocks(self):
    #     if self.enabled_types is not None:
    #         enabled_type_list=[ type_name  for  type_name, enabled in self.enabled_types.items() if enabled ]
    #     else:
    #         enabled_type_list=None
    #     return enabled_type_list


class SyntaxRegistry():
    """
    A class to store MOOSE syntax extracted from a highly nested dictionary in a flattened format.


    Entries in the registry are stored  in a dictionary with a unique key that maps onto a SyntaxPath object. A unique SyntaxPath may be parsed to identify relationships with child / parent paths to produce a SyntaxBlock that represents a block of syntax in a MOOSE input.
    """
    def __init__(self, all_json):
        # Flatten highly nested json dict
        syntax_paths=key_search_recurse(all_json,[],"parameters",20)
        assert isinstance(syntax_paths,list)

        self.syntax_dict={}
        for path_now in syntax_paths:
            self._recurse_path(path_now)

    def _recurse_path(self, path_in, children=None):
        syntax=SyntaxPath(path_in)
        self._add_syntax(syntax)

        # Add / update parents
        if syntax.parent_key is not None:
            if syntax.parent_key not in self.syntax_dict:
                self._recurse_path(syntax.parent_path)
            # Add current node to parent
            self.syntax_dict[syntax.parent_key].add_child(syntax)

    def _add_syntax(self, syntax):
        assert isinstance(syntax,SyntaxPath)
        assert syntax.unique_key not in self.syntax_dict.keys()
        self.syntax_dict[syntax.unique_key]=syntax

    def get_children_of_type(self,syntax_key,relation_type):
        children=[]
        parent=self.syntax_dict[syntax_key]
        if parent.has_child_type(relation_type):
            for child_path in parent.child_paths[relation_type]:
                child=self.syntax_dict[child_path]
                children.append(child.name)
        return children

    def get_available_syntax(self,syntax_key):
        available={}
        for relation,shortname in _relation_shorthands.items():
            syntax_list=self.get_children_of_type(syntax_key,shortname)
            if len(syntax_list)>0:
                available[shortname]=syntax_list
        if len(available.keys()) == 0:
            available=None
        return available

    def make_block(self,syntax_key):
        syntax=self.syntax_dict[syntax_key]

        block=SyntaxBlock()
        block.name=syntax.name
        block.path=syntax_key
        block.has_params=syntax.has_params
        block.available_syntax=self.get_available_syntax(syntax_key)
        block.relation_key=syntax.relation_to_parent

        # Set block depth and parents
        if not syntax.is_root:
            # Recurse until we find root
            syntax_now=syntax
            depth=0
            while not syntax_now.is_root:
                depth=depth+1
                parent_key=syntax_now.parent_key
                syntax_now=self.syntax_dict[parent_key]
                parent_name=syntax_now.name
                block.parent_blocks.insert(0,parent_name)
            block.depth=depth

        return block

    def get_available_blocks(self):
        available={}
        for unique_key in self.syntax_dict.keys():
            available[unique_key]=self.make_block(unique_key)
        return available

    # def get_available_blocks_sorted_by_depth(self):
    #     available_by_depth={}
    #     for unique_key in self.syntax_dict.keys():
    #         block_now=self.make_block(unique_key)
    #         depth_now=block_now.depth
    #         if depth_now not in available_by_depth.keys():
    #             available_by_depth[depth_now]={}
    #         available_by_depth[depth_now][unique_key]=block_now
    #     return available_by_depth

    # def blocks_by_depth(self, request_depth):
    #     return [ unique_key for unique_key, syntax in self.syntax_dict.items() if syntax.depth == request_depth ]

    # @property
    # def root_keys(self):
    #    return [ unique_key for unique_key, syntax in self.syntax_dict.items() if syntax.is_root ]


def key_search_recurse(dict_in, test_path, key_test, level_stop=15):
    """
    Parse blocks recursively until we hit the given key
    """
    if not isinstance(dict_in,dict):
        return list()

    if len(test_path) == level_stop:
        return list()

    if key_test in dict_in.keys():
        # Success at leaf node! Found key, return path to here
        success_path=deepcopy(test_path)
        success_path.append(key_test)
        return [ success_path ]

    success_paths=[]
    for key_now, test_obj in dict_in.items():
        # Path to be tested
        path_now=deepcopy(test_path)
        path_now.append(key_now)

        paths_to_success=key_search_recurse(test_obj,path_now,key_test,level_stop)

        # If search fails, paths will be empty
        # Otherwise add to our known list of success paths from this node
        if len( paths_to_success ) != 0:
            success_paths.extend(paths_to_success)

    return success_paths

def fetch_syntax(json_dict,syntax):
    assert isinstance(syntax,SyntaxPath)
    assert syntax.has_params

    key_list=deepcopy(syntax.path)
    assert len(key_list) > 0

    dict_now=json_dict
    while len(key_list) > 0:
        key_now=key_list.pop(0)
        obj_now=dict_now[key_now]

        assert isinstance(obj_now,dict)
        dict_now=deepcopy(obj_now)

    return dict_now

def parse_block(json_obj,syntax_path,class_name):
    # Construct Moose parameters
    moose_param_list=get_params_list(json_obj,syntax_path)

    # Deduce type of object by its relation to parent
    relation=_relation_shorthands[syntax_path.parent_relation]
    class_type=_child_type_map[relation]

    # Generate class documentation
    doc_now=class_type.moose_doc(moose_param_list)

    # Create new class with a name that matches the block
    new_cls = type(class_name,
                   (class_type,),
                   {
                       "__doc__": doc_now,
                   })

    # Add the parameters to the class
    for moose_param in moose_param_list:
        new_cls.add_moose_param(moose_param)

    # Return our new class
    return new_cls

def get_params_list(json_obj,syntax_path):
    # Available syntax for this block as dict
    block=fetch_syntax(json_obj,syntax_path)

    # Lift parameters dictionary
    params=block["parameters"]
    moose_param_list=[]

    for param_name, param_info in params.items():
        attr_types = tuple(type_mapping[t] for t in param_info['basic_type'].split(':'))
        attr_type = attr_types[-1]

        is_array=False
        if len(attr_types) > 1:
            for t in attr_types[:-1]:
                assert issubclass(t, Iterable)
            is_array=True

        # Set allowed values if present
        allowed_values = None
        if param_info['options']:
            values = param_info['options'].split()
            allowed_values = [_convert_to_type(attr_type, v) for v in values]

        # Apply the default value if provided
        # TODO: default values need to be handled differently. They are replacing
        # properties in the type definition as they are now
        default = None
        if 'default' in param_info.keys() and param_info['default'] != None and param_info['default'] != '':
            if is_array:
                defaults = param_info['default']
                if type(defaults) == str:
                    default = [_convert_to_type(attr_type, v) for v in defaults.split()]
                elif issubclass(type(defaults), Iterable):
                    default = [_convert_to_type(attr_type, v) for v in defaults]
                else:
                    default = [defaults]
            else:
                default = _convert_to_type(attr_type, param_info['default'])

        # Create and add a MOOSE parameter
        moose_param=MooseParam(param_name,
                               attr_type,
                               is_array,
                               default=default,
                               allowed_vals=allowed_values,
                               description=param_info.get('description'),
        )

        moose_param_list.append(moose_param)

    # Return list
    return moose_param_list


# convenience function for converting types
def _convert_to_type(t, val):
    if t == bool:
        val = bool(int(val))
    else:
        val = t(val)
    return val
