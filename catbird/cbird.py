from abc import ABC

import json

type_mapping = {'Integer' : int,
                'Boolean' : bool,
                'Float' : float,
                'Real' : float,
                'String' : str}


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

    def prop_set(self, name, attr_type, allowed_vals=None):
        """Returns a function for setting an attribute"""
        def fset(self, val):
            self.check_type(name, val, attr_type)
            if allowed_vals is not None:
                self.check_vals(name, val, allowed_vals)
            setattr(self.__class__, '_'+name, val)
        return fset

    def newattr(self, attr_name, attr_type=str, allowed_vals=None, desc=None):
        """Adds a property to the class"""
        if not isinstance(attr_name, str):
            raise ValueError('Attributes must be strings')
        prop = property(fget=self.prop_get(attr_name),
                        fset=self.prop_set(attr_name, attr_type, allowed_vals))
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
        list
            A list of Catbird classes -- one for each block name specified
        """

        def convert_to_type(t, val):
            if t == bool:
                val = bool(int(val))
            else:
                val = t(val)
            return val

        with open(json_file, 'r') as fh:
            j = json.loads(fh.read())


        # get problems block
        problems = j['blocks']['Problem']['types']

        instances_out = dict()

        for problem, block in problems.items():
            params = block['parameters']

            # create new subclass of Catbird
            new_cls = type(problem, (cls,), dict())
            inst = new_cls()


            for param_name, param_info in params.items():
                # skip array entries for now
                if 'Array' in param_info['basic_type']:
                    continue

                attr_type = type_mapping[param_info['basic_type']]

                allowed_values = None
                if param_info['options']:
                    values = param_info['options'].split()
                    allowed_values = [convert_to_type(attr_type, v) for v in values]

                inst.newattr(param_name,
                             attr_type,
                             desc=param_info.get('description'),
                             allowed_vals=allowed_values)

                if 'default' in param_info and param_info['default'] != 'none':
                    val = convert_to_type(attr_type, param_info['default'])
                    setattr(inst, param_name, val)

            instances_out[problem] = inst

        return instances_out
