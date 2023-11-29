from .cbird import parse_blocks_types

class MooseModel():
    def __init__(self,json_obj,params=None):
        if params==None:
            params=self.default_params()

        self.moose_objects=[]

        for category, cat_type in params.items():
            cat_dict=parse_blocks_types(json_obj,category,category_names=[cat_type])
            cat_constructor=cat_dict[cat_type]
            cat_instance=cat_constructor()

            # Prefer non-capitalised attributes
            attr_name=category.lower()
            setattr(self, attr_name, cat_instance)
            self.moose_objects.append(attr_name)

    @staticmethod
    def default_params():
        defaults = {
            "Mesh" : "GeneratedMesh",
            "Executioner" : "Steady",
            "Problem" : "FEProblem",
        }
        return defaults

    def to_str(self):
        model_str=""
        for obj_type in self.moose_objects:
            obj=getattr(self,obj_type)
            model_str+=obj.to_str()
        return model_str
