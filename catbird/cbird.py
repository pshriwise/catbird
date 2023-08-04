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


def nested_dict_iter(d):
    for a, b in d.items():
        yield (a, b)
        if isinstance(b, Mapping):
            for i in nested_dict_iter(b):
                yield i


class AppManager:
    """
    A class that manages new block class generation and file I/O

    Parameters
    ----------
    blocks : dict
        A dictionary with block names as keys and the corresponding Catbird block types as values
    """
    def __init__(self, blocks=None):
        if blocks is not None and blocks:
            assert 1 == len(set(type(v) for v in blocks.values()))
        self._blocks = blocks

    def create_instance(self, object_name):
        return self._blocks[object_name]()

    @staticmethod
    def _parse_default_value(obj_name, param_name, attr_type, ndim, param_info):
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

    @staticmethod
    def parse_problems(json_obj, block_names=None):
        instances_out = dict()

        for block_name, block in nested_dict_iter(json_obj['blocks']):
            # skip any blocks that we aren't looking for
            if block_names is not None and block_name not in block_names:
                continue

            if not isinstance(block, dict) or 'parameters' not in block or 'basic_type' in block['parameters']:
                continue

            params = block['parameters']
            # create new subclass of Catbird with a name that matches the block_name
            new_cls = type(block_name, (Catbird,), dict())
            if 'description' in block:
                new_cls.__doc__ = block['description']

            # loop over the block_name parameters
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
                default = AppManager._parse_default_value(block_name, param_name, attr_type, ndim, param_info)

                # add an attribute to the class instance for this parameter
                new_cls.newattr(param_name,
                                attr_type,
                                desc=param_info.get('description'),
                                default=default,
                                dim=ndim,
                                allowed_vals=allowed_values)

            # insert new instance into the output dictionary
            instances_out[block_name] = new_cls

        return instances_out

    @classmethod
    def from_exec(cls, exec, block_names=None):
        """
        Returns the Python objects corresponding to the MOOSE
        application described by the json file.

        Parameters
        ----------
        exec : str or Path
            Path to the MOOSE executable
        block_names : Iterable of str
            Set of objects to generate classes for

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

        return cls.from_json(j_obj, block_names=block_names)

    @classmethod
    def from_json(cls, json_file, block_names=None):
        """
        Returns the Python objects corresponding to the MOOSE application described
        by the json file.

        Parameters
        ----------
        json_file : dict, str, or Path
            Either an open file handle, or a path to the json file. If `json` is a
            dict, it is assumed this is a pre-parsed json object.
        block_names : Iterable of str
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

        blocks = cls.parse_problems(json_obj, block_names=block_names)

        return cls(blocks)

    def write_input(self, object_blocks, filename='input.i'):
        """
        Write a set of CatBird classes from

        Parameters
        ----------
        object_blocks : Iterable of Catbird
            Object blocks to write to to the resulting input file
        filename : str
            Path to the resulting input file
        """
        import pyhit
        root_node = pyhit.Node()

        for block in object_blocks:
            root_node[block.name] = object_blocks.to_node()

        root_node.write(filename, root_node)