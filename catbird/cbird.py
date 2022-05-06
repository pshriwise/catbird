import json

type_mapping = {'Integer' : int,
                'Boolean' : bool,
                'Float' : float,
                'String' : str}


class Catbird:

    def __init__(self):
        pass

    @staticmethod
    def check_type(name, val, attr_type):
        if not isinstance(val, attr_type):
            val_type_str = val.__class__.__name__
            exp_type_str = attr_type.__name__
            raise ValueError(f'Incorrect type {val_type_str} for attribute {name}. Expected type {exp_type_str}.')
        return val

    @staticmethod
    def check_vals(name, val, allowed_vals):
        if val not in allowed_vals:
            raise ValueError(f'Value {val} for attribute {name} is not one of {allowed_vals}')

    def prop_get(self, name):
        def fget(self):
            value = getattr(self, '_'+name)
            return value
        return fget

    def prop_set(self, name, attr_type, allowed_vals=None):
        def fset(self, val):
            self.check_type(name, val, attr_type)
            if allowed_vals is not None:
                self.check_vals(name, val, allowed_vals)
            setattr(self.__class__, '_'+name, val)
        return fset

    def newattr(self, attr_name, attr_type=str, allowed_vals=None, desc=None):
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
    def from_json(cls, json_file):

        def convert_to_type(t, val):
            if t == bool:
                val = bool(int(val))
            else:
                val = t(val)
            return val

        # create new subclass of Catbird
        new_cls = type('cardinal', (cls,), dict())
        inst = new_cls()

        with open(json_file, 'r') as fh:
            j = json.loads(fh.read())

        # get "parameters" block

        params = j['parameters']

        for param_name, param_info in params.items():
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

        return inst
