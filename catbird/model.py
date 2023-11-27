from .cbird import parse_blocks_types

class MooseModel():
    def __init__(self,json_obj,params=None):
        if params==None:
            params=self.default_params()

        self.objects={}

        for category, cat_type in params.items():
            cat_dict=parse_blocks_types(json_obj,category,category_names=[cat_type])
            cat_constructor=cat_dict[cat_type]
            cat_instance=cat_constructor()
            self.objects[category]=cat_instance

    @staticmethod
    def default_params():
        defaults = {
            "Mesh" : "GeneratedMesh",
            "Executioner" : "Steady",
            "Problem" : "FEProblem",
        }
        return defaults
