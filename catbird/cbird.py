from abc import ABC
from collections.abc import Iterable
import json
import numpy as np
from pathlib import Path
import subprocess


type_mapping = {'Integer' : int,
                'Boolean' : bool,
                'Float' : float,
                'Real' : float,
                'String' : str,
                'Array' : list}


# convenience function for converting types
def _convert_to_type(t, val):
    if t == bool:
        val = bool(int(val))
    else:
        val = t(val)
    return val


class Catbird(ABC):
    """
    Class that can add type-checked properties to itself.
    """

    def __init__(self):
        self.__moose_attrs__ = []

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
    def prop_get(name, default=None):
        """Returns function for getting an attribute"""
        def fget(self):
            # set to the default value if the internal attribute doesn't exist
            if not hasattr(self, '_'+name):
                setattr(self, '_'+name, default)
            value = getattr(self, '_'+name)
            return value
        return fget

    @staticmethod
    def prop_set(name, attr_type, dim=0, allowed_vals=None):
        """Returns a function for setting an attribute"""
        def fset(self, val):
            if dim == 0:
                self.check_type(name, val, attr_type)
                if allowed_vals is not None:
                    self.check_vals(name, val, allowed_vals)
                setattr(self, '_'+name, val)
            else:
                val = np.asarray(val)
                self.check_type(name, val.flat[0].item(), attr_type)
                if len(val.shape) != dim:
                    raise ValueError(f'Dimensionality is incorrect. Expects a {dim}-D array.')
                for v in val.flatten():
                    if allowed_vals is not None:
                        self.check_vals(name, v, allowed_vals)
                setattr(self, '_'+name, val)
            # self.__moose_attrs__ += [name]
        return fset

    @classmethod
    def newattr(cls, attr_name, attr_type=str, dim=0, default=None, allowed_vals=None, desc=None):
        """Adds a property to the class"""
        if not isinstance(attr_name, str):
            raise ValueError('Attributes must be strings')
        prop = property(fget=cls.prop_get(attr_name, default),
                        fset=cls.prop_set(attr_name, attr_type, dim, allowed_vals))
        setattr(cls, attr_name, prop)

        # set attribute docstring
        doc_str = f'\nType: {attr_type.__name__}\n'
        if desc is not None:
            doc_str += desc
        if allowed_vals is not None:
            doc_str += f'\nValues: {allowed_vals}'

        if doc_str:
            getattr(cls, attr_name).__doc__ = doc_str

    def to_node(self):
        """
        Create a pyhit node for this MOOSE object
        """
        import pyhit

        node = pyhit.Node(hitnode=self.__class__.__name__)

        for attr in self.__moose_attrs__:
            val = getattr(self, attr)
            if val is not None:
                node[attr] = val

        return node


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

    # Systems have a type == None
    systems=[]

    # Do not have a type, do have a sub-block
    nested_systems=[]

    # Fundamental blocks are top level-blocks with a type
    fundamental_blocks={}

    # Blocks which may have many entries, each with a type
    nested_blocks={}

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
                fundamental_blocks[block_name]=block_types_now
            except AttributeError :
                # Otherwise
                block_types_now = block_dict_now[types_key]
                if block_types_now == None:
                    systems.append(block_name)
                    continue

            #print(block_name," available types: ", block_types_now)
        elif wildcard_key in block_dict_now.keys() and nested_block_key in block_dict_now[wildcard_key].keys():
            try:
                types_now = list(block_dict_now[wildcard_key][nested_block_key].keys())
                nested_blocks[block_name]=types_now
            except AttributeError :
                types_now  = block_dict_now[wildcard_key][nested_block_key]
                if types_now == None:
                    nested_systems.append(block_name)
                    continue

        elif nested_key in block_dict_now.keys():
            nested_systems.append(block_name)
        else:
            print(block_name," has keys: ",block_dict_now.keys())
            raise RuntimeError("unhandled block category")


    parsed_block_list={}
    parsed_block_list["Systems"]=systems
    parsed_block_list["Nested systems"]=nested_systems
    parsed_block_list["Fundamental blocks"]=fundamental_blocks
    parsed_block_list["Nested blocks"]=nested_blocks

    return parsed_block_list


def parse_problems(json_obj, problem_names=None):
    return parse_blocks_types(json_obj,'Problem',category_names=problem_names)

def get_block_types(json_obj,category):
    block_types=None

    if category not in json_obj['blocks'].keys():
        msg="Unknown block name {}".format(category)
        raise RuntimeError(msg)

    if 'types' in json_obj['blocks'][category].keys():
        block_types =json_obj['blocks'][category]['types']
    elif 'star' in json_obj['blocks'][category].keys() and 'subblock_types' in json_obj['blocks'][category]['star'].keys():
        block_types=json_obj['blocks'][category]['star']['subblock_types']
    else:
        msg="Catergory {} does not have a type".format(category)
        raise RuntimeError(msg)

    return block_types




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

    requested_blocks = get_block_types(json_obj,category)

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
                            desc=param_info.get('description'),
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
