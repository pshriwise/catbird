from abc import ABC
from collections.abc import Iterable
import json
import numpy as np
from pathlib import Path
import subprocess
from copy import deepcopy

type_mapping = {'Integer' : int,
                'Boolean' : bool,
                'Float' : float,
                'Real' : float,
                'String' : str,
                'Array' : list}

_relation_syntax=["blocks","subblocks","actions","star","types","subblock_types"]
_relation_shorthands={
    "types": "types/",
    "actions":"actions/",
    "systems": "subblocks/",
    "type collections" : "star/subblock_types/",
    "action collections": "star/actions/",
    "system collections": "star/subblocks/"
}

class SyntaxRegistry():
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
        for shortname,relation in _relation_shorthands.items():
            syntax_list=self.get_children_of_type(syntax_key,relation)
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

class SyntaxPath():
    def __init__(self, syntax_path_in):
        # Initial values
        self.name=""
        self.unique_key=""
        self.has_params=False
        self.is_root=False
        self.parent_path=None
        self.parent_relation_path=None
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
            self.parent_relation=relation_path
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
        relation_key=self._key_from_list(child_syntax.parent_relation)
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

    # @property
    # def has_type(self):
    #     return self.has_child_type("types")

    # @property
    # def has_actions(self):
    #     return self.has_child_type("actions")

    # @property
    # def has_systems(self):
    #     return self.has_child_type("systems")

        # use child relation to parent type
        ## relation cases
        # Handle these in SyntaxBlock
        #['actions']-->has action
        #['subblocks']-->has system
        #['types']-->has type
        #['star', 'actions']-->has action_collection
        #['star', 'subblock_types']--> has typed_collection
        #['star', 'subblocks']--> has system_collection


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
            #if verbose:
            #    if  self.available_syntax:
            #        block_dict["available syntax"] = self.available_syntax
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

    def path_to_child(self,relation_type,child_name):
        path=self.path+"/"+_relation_shorthands[relation_type]+child_name
        return path

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


# convenience function for converting types
def _convert_to_type(t, val):
    if t == bool:
        val = bool(int(val))
    else:
        val = t(val)
    return val

# def get_params(json_dict,syntax):
#     assert isinstance(syntax,SyntaxPath)
#     assert syntax.has_params
#     key_list=deepcopy(syntax.path)
#     dict_now=json_dict
#     while len(key_list) > 0:
#         key_now=key_list.pop(0)
#         obj_now=dict_now[key_now]

#         assert isinstance(obj_now,dict)
#         dict_now=deepcopy(obj_now)

#     params=dict_now["parameters"]
#     return params

def get_block(json_dict,syntax):
    assert isinstance(syntax,SyntaxPath)

    key_list=deepcopy(syntax.path)
    assert len(key_list) > 0

    dict_now=json_dict
    while len(key_list) > 0:
        key_now=key_list.pop(0)
        obj_now=dict_now[key_now]

        assert isinstance(obj_now,dict)
        dict_now=deepcopy(obj_now)


    try:
        assert syntax.has_params
    except AssertionError:
        print(syntax.name)
        print(dict_now.keys())
        raise AssertionError

    return dict_now


class MooseParam():
    """
    Class to contain all information about a MOOSE parameter
    """
    def __init__(self):
        self.val=None
        self.attr_type=None
        self.default=None
        self.allowed_vals=None
        self.dim=0
        self.doc=""

class Catbird(ABC):
    """
    Class to represent MOOSE syntax that can add type-checked properties to itself.
    """
    def __init__(self):
        self._syntax_name=""

    def set_syntax_name(self,syntax_name):
        self._syntax_name=syntax_name

    # @classmethod
    # def set_syntax_type(cls,syntax_type):
    #     cls._syntax_type=syntax_type

    # @classmethod
    # def set_syntax_category(cls,syntax_category):
    #     cls._syntax_category=syntax_category

    # @property
    # def syntax_block_name(self):
    #     if self.is_nested:
    #         return self._syntax_name
    #     else:
    #         return self._syntax_category

    # @property
    # def indent_level(self):
    #     if self.is_nested:
    #         return 2
    #     else:
    #         return 1

    # @property
    # def is_nested(self):
    #     return self._syntax_type =="nested" or self._syntax_type=="nested_system"

    @property
    def moose_params(self):
        return self._moose_params

    @staticmethod
    def check_type(name, val, attr_type):
        """Checks a value's type"""
        if not isinstance(val, attr_type):
            val_type_str = val.__class__.__name__
            exp_type_str = attr_type.__name__
            raise ValueError(f'Incorrect type "{val_type_str}" for attribute "{name}". '
                             f'Expected type "{exp_type_str}".')
        return val

    @staticmethod
    def check_vals(name, val, allowed_vals):
        """Checks that a value is in the set of allowed_values"""
        if val not in allowed_vals:
            raise ValueError(f'Value {val} for attribute {name} is not one of {allowed_vals}')

    @staticmethod
    def moose_property(name, param):
        """
        Returns a property, and creates an associated class attribute whose value is that of the supplied MooseParam.

        The property setter method will change the value of the underlying MooseParam.value, checking its type is consistent
        The property getter method will retrieve the value of the underlying MooseParam.value
        """

        def fget(self):
            # set to the default value if the internal attribute doesn't exist
            if not hasattr(self, '_'+name):
                setattr(self, '_'+name, param)
            param_now = getattr(self, '_'+name)
            return param_now.val

        def fset(self, val):
            if param.dim == 0:
                self.check_type(name, val, param.attr_type)
                if param.allowed_vals is not None:
                    self.check_vals(name, val, param.allowed_vals)
            else:
                val = np.asarray(val)
                self.check_type(name, val.flat[0].item(), param.attr_type)
                if len(val.shape) != param.dim:
                    raise ValueError(f'Dimensionality is incorrect. Expects a {dim}-D array.')
                for v in val.flatten():
                    if param.allowed_vals is not None:
                        self.check_vals(name, v, allowed_vals)

            param_now = getattr(self, '_'+name)
            param_now.val=val
            setattr(self, '_'+name, param_now)

        def fdel(self):
            param_now = getattr(self, '_'+name)
            del param_now


        return property(fget,fset,fdel,param.doc)

    # @staticmethod
    # def prop_get(name, default=None):
    #     """Returns function for getting an attribute"""
    #     def fget(self):
    #         # set to the default value if the internal attribute doesn't exist
    #         if not hasattr(self, '_'+name):
    #             setattr(self, '_'+name, default)
    #         value = getattr(self, '_'+name)
    #         return value
    #     return fget

    # @staticmethod
    # def prop_set(name, attr_type, dim=0, allowed_vals=None,doc=""):
    #     """Returns a function for setting an attribute"""
    #     def fset(self, val):
    #         if dim == 0:
    #             self.check_type(name, val, attr_type)
    #             if allowed_vals is not None:
    #                 self.check_vals(name, val, allowed_vals)
    #             setattr(self, '_'+name, val)
    #             #setattr(self, '_'+name, val)
    #         else:
    #             val = np.asarray(val)
    #             self.check_type(name, val.flat[0].item(), attr_type)
    #             if len(val.shape) != dim:
    #                 raise ValueError(f'Dimensionality is incorrect. Expects a {dim}-D array.')
    #             for v in val.flatten():
    #                 if allowed_vals is not None:
    #                     self.check_vals(name, v, allowed_vals)
    #             setattr(self, '_'+name, val)
    #     return fset

    # @staticmethod
    # def prop_doc(name, doc_str=""):
    #     def fdoc(self):
    #         print("retrieve doc")
    #         doc_str_now=""
    #         if doc_str != "":
    #             doc_str_now=doc_str
    #         else:
    #             value = getattr(self, '_'+name)
    #             doc_str_now=value.__doc__
    #         return doc_str_now
    #     return fdoc

    @classmethod
    def newattr(cls, attr_name, attr_type=str, dim=0, default=None, allowed_vals=None, description=None):
        """Adds a property to the class"""
        if not isinstance(attr_name, str):
            raise ValueError('Attributes must be strings')

        if attr_name.find("_syntax_") != -1:
            msg="'_syntax_' is reserved attribute string. Cannot add attibute {}".format(attr_name)
            raise RuntimeError(msg)

        # Set attribute docstring
        doc_str = f'\nType: {attr_type.__name__}\n'
        if description is not None:
            doc_str += description
        if allowed_vals is not None:
            doc_str += f'\nValues: {allowed_vals}'

        # Store parameter details in a structure
        moose_param=MooseParam()
        if default is not None:
            moose_param.val=default
        else:
            moose_param.val=attr_type()
        moose_param.attr_type=attr_type
        moose_param.default=default
        moose_param.dim=dim
        moose_param.allowed_vals=allowed_vals
        moose_param.doc=doc_str

        # Define a property and add to class (args are functions)
        # Should be able to add a docstring here....
        #prop = property(fget=cls.prop_get(attr_name, default),
        #                fset=cls.prop_set(attr_name, attr_type, dim, allowed_vals, doc_str))
        #setattr(cls, attr_name, prop)

        # Add attribute to the class using a method which returns a property
        setattr(cls, attr_name, cls.moose_property(attr_name,moose_param))

        # Keep track of the attributes we've added
        if not hasattr(cls,"_moose_params"):
            setattr(cls,"_moose_params",[])
        moose_param_list_local=getattr(cls,"_moose_params")
        moose_param_list_local.append(attr_name)
        setattr(cls,"_moose_params",moose_param_list_local)

    # # Todo - waspify
    # def to_node(self):
    #     """
    #     Create a pyhit node for this MOOSE object
    #     """
    #     import pyhit

    #     node = pyhit.Node(hitnode=self.__class__.__name__)

    #     for attr in self.__moose_attrs__:
    #         val = getattr(self, attr)

    #         getattr(self, '_'+name)
    #         if val is not None:
    #             node[attr] = val

    #     return node

    @property
    def indent(self):
        indent_str=""
        indent_per_level="  "
        for i_level in range(0,self.indent_level):
            indent_str+=indent_per_level
        return indent_str

    @property
    def prepend_indent(self):
        indent_str=""
        indent_per_level="  "
        if self.indent_level > 1:
            for i_level in range(0,self.indent_level-1):
                indent_str+=indent_per_level
        return indent_str

    def is_default(self,attr_name):
        attr_val = getattr(self, attr_name)
        param = getattr(self, "_"+attr_name)
        default_val = param.default
        if default_val is None:
            default_val = param.attr_type()
        return attr_val == default_val

    def attr_to_str(self,attr_name,print_default=False):
        attr_str=""
        if self.is_default(attr_name) and not print_default:
            return attr_str

        attr_val = getattr(self, attr_name)
        if attr_val is not None:
            attr_val = getattr(self, attr_name)
            attr_str=self.indent+'{}={}\n'.format(attr_name,attr_val)
        return attr_str

    def to_str(self,print_default=False):
        syntax_str='{}[{}]\n'.format(self.prepend_indent,self.syntax_block_name)
        param_list=self.moose_params

        # Formatting convention, start with type
        if "type" in  param_list:
            param_list.remove("type")
        syntax_str+=self.attr_to_str("type",True)

        for attr_name in param_list:
            syntax_str+=self.attr_to_str(attr_name,print_default)
        syntax_str+='{}[]\n'.format(self.prepend_indent)

        return syntax_str

    def print_me(self):
        name=self.block_name
        print("Name: ",name)

        param_list=self.moose_params
        for attr_name in param_list:
            attr_val = getattr(self, attr_name)
            if attr_val is not None:
                attr_str="{}.{}: {}".format(name,attr_name,attr_val)
            else:
                attr_str="{}.{}: None".format(name,attr_name)
            print(attr_str)


def json_from_exec(exec):
    """
    Returns the Python objects corresponding to the MOOSE application described
    by the json file.

    Parameters
    ----------
    json_file : str, or Path
        Either an open file handle, or a path to the json file. If `json` is a
        dict, it is assumed this is a pre-parsed json object.

    Returns
    -------
    dict
        A dictionary of all MOOSE objects
    """
    json_proc = subprocess.Popen([exec, '--json'], stdout=subprocess.PIPE)
    json_str = ''

    # filter out the header and footer from the json data
    while True:
        line = json_proc.stdout.readline().decode()
        if not line:
            break
        if '**START JSON DATA**' in line:
            continue
        if '**END JSON DATA**' in line:
            continue

        json_str += line

    j_obj = json.loads(json_str)

    return j_obj

def write_json(json_dict_out,name):
    """
    Write a dictionary in JSON format

    Parameters
    ----------
    json_dict_out : dict
    name: str
      Save as name.json
    """
    json_output = json.dumps(json_dict_out, indent=4)
    json_name=name
    if json_name.find(".json") < 0 :
        json_name = name+".json"

    with open(json_name, "w") as fh:
        fh.write(json_output)
        fh.write("\n")
    print("Wrote to ",json_name)


def read_json(json_file):
    """
    Load the contents of a JSON file into a dict.

    Parameters
    ----------
    json_file: str
      Name of JSON file
    """
    json_dict = {}
    with open(json_file) as handle:
        json_dict = json.load(handle)
    return json_dict

def problems_from_json(json_file, problem_names=None):
    """
    Returns the Python objects corresponding to the MOOSE application described
    by the json file.

    Parameters
    ----------
    json_file : dict, str, or Path
        Either an open file handle, or a path to the json file. If `json` is a
        dict, it is assumed this is a pre-parsed json object.
    problems : Iterable of str
        Set of problems to generate classes for

    Returns
    -------
    dict
        A dictionary of problem objects
    """

    if isinstance(json_file, dict):
        json_obj = json_file
    else:
        json_obj = json.load(json_file)

    out = dict()

    out['problems'] = parse_problems(json_obj, problem_names=problem_names)

    return out

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


def parse_blocks(json_obj):
    """
    Returns the a dictionary of block types corresponding to the MOOSE application described
    by the json file.

    Parameters
    ----------
    json_obj : dict
        Dictionary of full MOOSE object tree

    Returns
    -------
    dict
        Dictionary of available block types organised by category
    """

    # Get all top level categories of block
    block_name_list = json_obj['blocks'].keys()

    #all_syntax=[]
    parsed_blocks={}

    types_key='types'
    wildcard_key='star'
    nested_key='subblocks'
    nested_block_key='subblock_types'

    for block_name in block_name_list:
        block_dict_now = json_obj['blocks'][block_name]
        if types_key in block_dict_now.keys():
            try :
                # If dict
                block_types_now = list(block_dict_now[types_key].keys())
                #fundamental_blocks[block_name]=block_types_now
                parsed_blocks[block_name]=SyntaxBlock(block_name,"fundamental",block_types_now)

                #all_syntax.append(SyntaxBlock(block_name,"fundamental",block_types_now))
            except AttributeError :
                # Otherwise
                block_types_now = block_dict_now[types_key]
                if block_types_now == None:
                    #systems.append(block_name)
                    parsed_blocks[block_name]=SyntaxBlock(block_name,"system",None)
                    #all_syntax.append(SyntaxBlock(block_name,"systems",None))
                    continue

            #print(block_name," available types: ", block_types_now)
        elif wildcard_key in block_dict_now.keys() and nested_block_key in block_dict_now[wildcard_key].keys():
            try:
                types_now = list(block_dict_now[wildcard_key][nested_block_key].keys())
                #nested_blocks[block_name]=types_now
                parsed_blocks[block_name]=SyntaxBlock(block_name,"nested",types_now)
                #all_syntax.append(SyntaxBlock(block_name,"nested",types_now))

            except AttributeError :
                types_now  = block_dict_now[wildcard_key][nested_block_key]
                if types_now == None:
                    #nested_systems.append(block_name)
                    #all_syntax.append(SyntaxBlock(block_name,"nested_system",None))
                    parsed_blocks[block_name]=SyntaxBlock(block_name,"nested_system",None)
                    continue

        elif nested_key in block_dict_now.keys():
            #nested_systems.append(block_name)
            #all_syntax.append(SyntaxBlock(block_name,"nested_system",None))
            parsed_blocks[block_name]=SyntaxBlock(block_name,"nested_system",None)

        else:
            print(block_name," has keys: ",block_dict_now.keys())
            raise RuntimeError("unhandled block category")


    # parsed_block_list={}
    # parsed_block_list["Systems"]=systems
    # parsed_block_list["Nested systems"]=nested_systems
    # parsed_block_list["Fundamental blocks"]=fundamental_blocks
    # parsed_block_list["Nested blocks"]=nested_blocks

    #return parsed_block_list
    return parsed_blocks

def parse_problems(json_obj, problem_names=None):
    return parse_blocks_types(json_obj,'Problem',category_names=problem_names)

def get_block_types(json_obj,block_name):
    block_types=None
    syntax_type=""

    blocks_dict=json_obj['blocks']

    if block_name not in blocks_dict.keys():
        msg="Unknown block name {}".format(block_name)
        raise RuntimeError(msg)

    current_block_dict=blocks_dict[block_name]

    syntax_type_to_block_types={
        "fundamental":{},
        "system":{},
        "nested":{},
        "nested_system":{},
        "action":{},
        "double_nested":{},
    }

    # 6 cases, but not limited to single type at once
    # TODO this is awful... refactor
    # Suggest recursing down until found a "parameter" key
    if 'types' in current_block_dict.keys() and current_block_dict['types'] is not None:
        block_types=current_block_dict['types']
        syntax_type_to_block_types["fundamental"].update(block_types)

    if 'star' in current_block_dict.keys() and current_block_dict['star'] is not None:
        if 'subblock_types' in current_block_dict['star'].keys():
            block_types=current_block_dict['star']['subblock_types']
            if block_types is not None:
                syntax_type_to_block_types["nested"].update(block_types)

        if 'actions' in current_block_dict['star'].keys():
            block_types=current_block_dict['star']['actions']
            if block_types is not None:
                syntax_type_to_block_types["nested_action"].update(block_types)

    if 'subblocks' in current_block_dict.keys() and current_block_dict['subblocks'] is not None:

        system_type_dict={}
        nested_type_dict={}
        double_nested_type_dict={}

        for subblock_name in current_block_dict['subblocks'].keys():
            subblock_dict=current_block_dict['subblocks'][subblock_name]

            if 'types' in subblock_dict.keys() and subblock_dict['types'] is not None:
                block_types=subblock_dict['types']
                system_type_dict[subblock_name]=block_types

            if 'star' in subblock_dict.keys() and subblock_dict['star'] is not None:
                if 'subblock_types' in subblock_dict['star'].keys():
                    block_types=subblock_dict['star']['subblock_types']
                    if block_types is not None:
                        nested_type_dict[subblock_name]=block_types

            if 'subblocks' in subblock_dict.keys() and subblock_dict['subblocks'] is not None:

                double_nested_type_dict[subblock_name]={}

                for subsubblock_name in subblock_dict['subblocks'].keys():
                    subsubblock_dict=subblock_dict['subblocks'][subsubblock_name]

                    if 'actions' in subsubblock_dict.keys() and subsubblock_dict['actions'] is not None:
                        double_nested_type_dict[subblock_name][subsubblock_name]=subsubblock_dict['actions']

                    if 'star' in subsubblock_dict.keys() and subsubblock_dict['star'] is not None:
                        if 'actions' in subsubblock_dict['star'].keys() and subsubblock_dict['star']['actions'] is not None:
                            double_nested_type_dict[subblock_name][subsubblock_name]=subsubblock_dict['star']['actions']


        if len(system_type_dict) >0:
            syntax_type_to_block_types["system"].update(system_type_dict)
        if len(nested_type_dict) >0:
            syntax_type_to_block_types["nested_system"].update(nested_type_dict)
        if len(double_nested_type_dict) >0:
            syntax_type_to_block_types["double_nested"].update(double_nested_type_dict)


    if 'actions' in current_block_dict.keys() and current_block_dict['actions'] is not None:
        block_types=current_block_dict['actions']
        syntax_type_to_block_types["action"].update(block_types)


    count_types=0
    for syntax_type in syntax_type_to_block_types.keys():
        block_types=syntax_type_to_block_types[syntax_type]
        if len(block_types) > 0:
            count_types+=1

    if count_types == 0:
        msg="Block {} is undocumented".format(block_name)
        print(msg)
        #raise RuntimeError(msg)
        #block_types=None
        #syntax_type="Unknown"

    elif count_types > 1:
        msg="Block {} is has {} types".format(block_name,count_types)
        print(msg)

    #return block_types, syntax_type
    return syntax_type_to_block_types


def parse_block(json_obj,block_path):
    # Available syntax for this block as dict
    block=get_block(json_obj,block_path)

    # Create new subclass of Catbird with a name that matches the block
    name=block_path.name
    new_cls = type(name, (Catbird,), dict())

    # Add parameters as attributes
    params=block["parameters"]
    for param_name, param_info in params.items():
        # Determine the type of the parameter
        attr_types = tuple(type_mapping[t] for t in param_info['basic_type'].split(':'))
        attr_type = attr_types[-1]

        if len(attr_types) > 1:
            for t in attr_types[:-1]:
                assert issubclass(t, Iterable)
                ndim = len(attr_types) - 1
        else:
            ndim = 0

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
            if ndim == 0:
                default = _convert_to_type(attr_type, param_info['default'])
            else:
                default = [_convert_to_type(attr_type, v) for v in param_info['default'].split()]

        # Add an attribute to the class instance for this parameter
        new_cls.newattr(param_name,
                        attr_type,
                        description=param_info.get('description'),
                        default=default,
                        dim=ndim,
                        allowed_vals=allowed_values)


    # Return our new class
    return new_cls

def parse_blocks_types(json_obj,category,category_names=None):
    """
    Make python objects out of MOOSE syntax for a fundamental category of block
    (E.g. Executioner, Problem)

    Parameters
    ----------
    json_obj : dict
        A dictionary of all MOOSE objects

    category: str
        A string naming the category of fundamental MOOSE block

    category_names: list(str)
        Optional field. If provided, only return objects for specified types.

    Returns
    -------
    dict
        A dictionary of pythonised MOOSE objects of the given category.
    """

    requested_blocks,syntax_type = get_block_types(json_obj,category)

    instances_out = dict()

    for block_type, block_attributes in requested_blocks.items():
        # skip any blocks that we aren't looking for
        if category_names is not None and block_type not in category_names:
            continue

        # Todo add auto-documntations
        #dict_keys(['description', 'file_info', 'label', 'moose_base', 'parameters', 'parent_syntax', 'register_file', 'syntax_path'])

        params = block_attributes['parameters']

        # create new subclass of Catbird with a name that matches the block_type
        new_cls = type(block_type, (Catbird,), dict())

        # Set the
        new_cls.set_syntax_type(syntax_type)

        if syntax_type != "nested":
            new_cls.syntax_block_name=category

        # loop over the block_type parameters
        for param_name, param_info in params.items():
            # determine the type of the parameter
            attr_types = tuple(type_mapping[t] for t in param_info['basic_type'].split(':'))
            attr_type = attr_types[-1]

            if len(attr_types) > 1:
                for t in attr_types[:-1]:
                    assert issubclass(t, Iterable)
                ndim = len(attr_types) - 1
            else:
                ndim = 0

            # set allowed values if present
            allowed_values = None
            if param_info['options']:
                values = param_info['options'].split()
                allowed_values = [_convert_to_type(attr_type, v) for v in values]

                # apply the default value if provided
            # TODO: default values need to be handled differently. They are replacing
            # properties in the type definition as they are now
            default = None
            if 'default' in param_info.keys() and param_info['default'] != None:
                default = _convert_to_type(attr_type, param_info['default'])
                # # only supporting defaults for one dimensional dim types
                # vals = [_convert_to_type(attr_type, v) for v in param_info['default'].split()]
                # if ndim == 0:
                #     default = vals[0]
                # else:
                #     default = np.array(vals)

            # add an attribute to the class instance for this parameter
            new_cls.newattr(param_name,
                            attr_type,
                            description=param_info.get('description'),
                            default=default,
                            dim=ndim,
                            allowed_vals=allowed_values)

        # insert new instance into the output dictionary
        instances_out[block_type] = new_cls

    return instances_out

def problem_from_exec(exec, problem_names=None):
    """
    Returns the Python objects corresponding to the MOOSE
    application described by the json file.

    Parameters
    ----------
    problems : Iterable of str
        Set of problems to generate classes for

    Returns
    -------
    dict
        A dictionary of problem objects
    """
    j_obj = json_from_exec(exec)

    return problems_from_json(j_obj, problem_names=problem_names)

def export_all_blocks_from_exec(exec,name):
    j_obj = json_from_exec(exec)
    block_dict=parse_blocks(j_obj)
    write_json(block_dict,name)
