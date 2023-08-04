from abc import ABC
from collections.abc import Iterable, Mapping
import json
import numpy as np
from pathlib import Path
import subprocess
import warnings


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


def app_from_json(json_file, problem_names=None):
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

def nested_dict_iter(d):
    for a, b in d.items():
        yield (a, b)
        if isinstance(b, Mapping):
          for i in nested_dict_iter(b):
              yield i

def parse_default_value(obj_name, param_name, attr_type, ndim, param_info):
    if ndim > 1:
        return None
    try:
        if 'default' in param_info and param_info['default'] != 'none':
            # only supporting defaults for one dimensional dim types
            vals = [_convert_to_type(attr_type, v) for v in str(param_info['default']).split()]
            if not vals:
                return None
            elif ndim == 0:
                return vals[0]
            else:
                return np.array(vals)
    except:
        warnings.warn(f'Failed to parse default value for parameter: {obj_name}.{param_name}')
    return None

def parse_problems(json_obj, problem_names=None):
    # get problems block
    problems = json_obj['blocks']['Problem']['types']

    instances_out = dict()

    for problem, block in nested_dict_iter(json_obj['blocks']):
        # skip any blocks that we aren't looking for
        if problem_names is not None and problem not in problem_names:
            continue

        if not isinstance(block, dict) or 'parameters' not in block or 'basic_type' in block['parameters']:
            continue

        params = block['parameters']
        # create new subclass of Catbird with a name that matches the problem
        new_cls = type(problem, (Catbird,), dict())
        new_cls.__doc__ = description = block['description']


        # loop over the problem parameters
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
            default = parse_default_value(problem, param_name, attr_type, ndim, param_info)

            # add an attribute to the class instance for this parameter
            new_cls.newattr(param_name,
                            attr_type,
                            desc=param_info.get('description'),
                            default=default,
                            dim=ndim,
                            allowed_vals=allowed_values)

        # insert new instance into the output dictionary
        instances_out[problem] = new_cls

    return instances_out


def app_from_exec(exec, problem_names=None):
    """
    Returns the Python objects corresponding to the MOOSE
    application described by the json file.

    Parameters
    ----------
    json : str or Path
        Path to the MOOSE executable
    problems : Iterable of str
        Set of problems to generate classes for

    Returns
    -------
    dict
        A dictionary of problem objects
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

    return app_from_json(j_obj, problem_names=problem_names)
