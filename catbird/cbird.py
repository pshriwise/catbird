from abc import ABC
from collections.abc import Iterable
import json
import numpy as np


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
    Class for creation of Python objects representing available MOOSE blocks for
    a given app.
    """

    def __init__(self):
        pass

    @staticmethod
    def check_type(name, val, attr_type):
        """Checks a value's type"""
        if not isinstance(val, attr_type):
            val_type_str = val.__class__.__name__
            exp_type_str = attr_type.__name__
            raise ValueError(f'Incorrect type {val_type_str} for attribute {name}. Expected type {exp_type_str}.')
        return val

    @staticmethod
    def check_vals(name, val, allowed_vals):
        """Checks that a value is in the set of allowed_values"""
        if val not in allowed_vals:
            raise ValueError(f'Value {val} for attribute {name} is not one of {allowed_vals}')

    def prop_get(self, name):
        """Returns function for getting an attribute"""
        def fget(self):
            value = getattr(self, '_'+name)
            return value
        return fget

    def prop_set(self, name, attr_type, dim=0, allowed_vals=None):
        """Returns a function for setting an attribute"""
        def fset(self, val):
            if dim == 0:
                self.check_type(name, val, attr_type)
                if allowed_vals is not None:
                    self.check_vals(name, val, allowed_vals)
                setattr(self.__class__, '_'+name, val)
            else:
                val = np.asarray(val)
                self.check_type(name, val.flat[0].item(), attr_type)
                if len(val.shape) != dim:
                    raise ValueError(f'Dimensionality is incorrect. Expects a {dim}-D array.')
                for v in val.flatten():
                    if allowed_vals is not None:
                        self.check_vals(name, v, allowed_vals)
                setattr(self.__class__, '_'+name, val)
        return fset

    def newattr(self, attr_name, attr_type=str, dim=0, allowed_vals=None, desc=None):
        """Adds a property to the class"""
        if not isinstance(attr_name, str):
            raise ValueError('Attributes must be strings')
        prop = property(fget=self.prop_get(attr_name),
                        fset=self.prop_set(attr_name, attr_type, dim, allowed_vals))
        setattr(self.__class__, attr_name, prop)
        setattr(self.__class__, '_'+attr_name, None)

        # set attribute docstring
        doc_str = ''
        if desc is not None:
            doc_str += desc
        if allowed_vals is not None:
            doc_str += f'\nValues: {allowed_vals}'

        if doc_str:
            getattr(self.__class__, attr_name).__doc__ = doc_str

    @classmethod
    def from_json(cls, json_file, block_names=None):
        """Creates a class from a JSON block

        Parameters
        ----------
        json_file : str or Path
            Location of the json file to read
        block_names : iterable of str
            List of block names to generate classes for. If not specified,
            a class will be generated for every supported block type.

        Returns
        -------
        dict
            Dictionary of classes with their names as values and instances as values
        """

        # open the json file
        with open(json_file, 'r') as fh:
            j = json.loads(fh.read())

        # get problems block
        problems = j['blocks']['Problem']['types']

        #
        instances_out = dict()

        for problem, block in problems.items():
            # skip any blocks that we aren't looking for
            if block_names is not None and problem not in block_names:
                continue

            params = block['parameters']

            # create new subclass of Catbird with a name that matches the problem
            new_cls = type(problem, (cls,), dict())
            inst = new_cls()

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

                # add an attribute to the class instance for this parameter
                inst.newattr(param_name,
                             attr_type,
                             desc=param_info.get('description'),
                             dim=ndim,
                             allowed_vals=allowed_values)

                # apply the default value if provided
                if 'default' in param_info and param_info['default'] != 'none':
                    # only supporting defaults for one dimensional dim types
                    vals = [_convert_to_type(attr_type, v) for v in param_info['default'].split()]

                    if ndim == 0:
                        setattr(inst, param_name, vals[0])
                    else:
                        setattr(inst, param_name, np.array(vals))

            # insert new instance into the output dictionary
            instances_out[problem] = inst

        return instances_out
