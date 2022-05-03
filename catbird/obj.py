

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

    def prop_get(self, name):
        def fget(self):
            value = getattr(self, '_'+name)
            return value
        return fget

    def prop_set(self, name, attr_type):
        def fset(self, val):
            self.check_type(name, val, attr_type)
            setattr(self, '_'+name, val)
        return fset

    def newattr(self, attr_name, attr_type=str):
        if not isinstance(attr_name, str):
            raise ValueError('Attributes must be strings')
        prop = property(fget=self.prop_get(attr_name), fset=self.prop_set(attr_name, attr_type))
        setattr(self.__class__, attr_name, prop)
        setattr(self.__class__, '_'+attr_name, None)