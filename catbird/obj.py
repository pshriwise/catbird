

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
            setattr(self, '_'+name, val)
        return fset

    def newattr(self, attr_name, attr_type=str, allowed_vals=None):
        if not isinstance(attr_name, str):
            raise ValueError('Attributes must be strings')
        prop = property(fget=self.prop_get(attr_name),
                        fset=self.prop_set(attr_name, attr_type, allowed_vals))
        setattr(self.__class__, attr_name, prop)
        setattr(self.__class__, '_'+attr_name, None)

