from .obj import MooseObject
from .syntax import type_mapping, _convert_to_type
from .utils import json_from_exec, write_json

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

    #all_syntax=[]
    parsed_blocks={}

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
                #fundamental_blocks[block_name]=block_types_now
                parsed_blocks[block_name]=SyntaxBlock(block_name,"fundamental",block_types_now)

                #all_syntax.append(SyntaxBlock(block_name,"fundamental",block_types_now))
            except AttributeError :
                # Otherwise
                block_types_now = block_dict_now[types_key]
                if block_types_now == None:
                    #systems.append(block_name)
                    parsed_blocks[block_name]=SyntaxBlock(block_name,"system",None)
                    #all_syntax.append(SyntaxBlock(block_name,"systems",None))
                    continue

            #print(block_name," available types: ", block_types_now)
        elif wildcard_key in block_dict_now.keys() and nested_block_key in block_dict_now[wildcard_key].keys():
            try:
                types_now = list(block_dict_now[wildcard_key][nested_block_key].keys())
                #nested_blocks[block_name]=types_now
                parsed_blocks[block_name]=SyntaxBlock(block_name,"nested",types_now)
                #all_syntax.append(SyntaxBlock(block_name,"nested",types_now))

            except AttributeError :
                types_now  = block_dict_now[wildcard_key][nested_block_key]
                if types_now == None:
                    #nested_systems.append(block_name)
                    #all_syntax.append(SyntaxBlock(block_name,"nested_system",None))
                    parsed_blocks[block_name]=SyntaxBlock(block_name,"nested_system",None)
                    continue

        elif nested_key in block_dict_now.keys():
            #nested_systems.append(block_name)
            #all_syntax.append(SyntaxBlock(block_name,"nested_system",None))
            parsed_blocks[block_name]=SyntaxBlock(block_name,"nested_system",None)

        else:
            print(block_name," has keys: ",block_dict_now.keys())
            raise RuntimeError("unhandled block category")


    # parsed_block_list={}
    # parsed_block_list["Systems"]=systems
    # parsed_block_list["Nested systems"]=nested_systems
    # parsed_block_list["Fundamental blocks"]=fundamental_blocks
    # parsed_block_list["Nested blocks"]=nested_blocks

    #return parsed_block_list
    return parsed_blocks

def get_block_types(json_obj,block_name):
    block_types=None
    syntax_type=""

    blocks_dict=json_obj['blocks']

    if block_name not in blocks_dict.keys():
        msg="Unknown block name {}".format(block_name)
        raise RuntimeError(msg)

    current_block_dict=blocks_dict[block_name]

    syntax_type_to_block_types={
        "fundamental":{},
        "system":{},
        "nested":{},
        "nested_system":{},
        "action":{},
        "double_nested":{},
    }

    # 6 cases, but not limited to single type at once
    # TODO this is awful... refactor
    # Suggest recursing down until found a "parameter" key
    if 'types' in current_block_dict.keys() and current_block_dict['types'] is not None:
        block_types=current_block_dict['types']
        syntax_type_to_block_types["fundamental"].update(block_types)

    if 'star' in current_block_dict.keys() and current_block_dict['star'] is not None:
        if 'subblock_types' in current_block_dict['star'].keys():
            block_types=current_block_dict['star']['subblock_types']
            if block_types is not None:
                syntax_type_to_block_types["nested"].update(block_types)

        if 'actions' in current_block_dict['star'].keys():
            block_types=current_block_dict['star']['actions']
            if block_types is not None:
                syntax_type_to_block_types["nested_action"].update(block_types)

    if 'subblocks' in current_block_dict.keys() and current_block_dict['subblocks'] is not None:

        system_type_dict={}
        nested_type_dict={}
        double_nested_type_dict={}

        for subblock_name in current_block_dict['subblocks'].keys():
            subblock_dict=current_block_dict['subblocks'][subblock_name]

            if 'types' in subblock_dict.keys() and subblock_dict['types'] is not None:
                block_types=subblock_dict['types']
                system_type_dict[subblock_name]=block_types

            if 'star' in subblock_dict.keys() and subblock_dict['star'] is not None:
                if 'subblock_types' in subblock_dict['star'].keys():
                    block_types=subblock_dict['star']['subblock_types']
                    if block_types is not None:
                        nested_type_dict[subblock_name]=block_types

            if 'subblocks' in subblock_dict.keys() and subblock_dict['subblocks'] is not None:

                double_nested_type_dict[subblock_name]={}

                for subsubblock_name in subblock_dict['subblocks'].keys():
                    subsubblock_dict=subblock_dict['subblocks'][subsubblock_name]

                    if 'actions' in subsubblock_dict.keys() and subsubblock_dict['actions'] is not None:
                        double_nested_type_dict[subblock_name][subsubblock_name]=subsubblock_dict['actions']

                    if 'star' in subsubblock_dict.keys() and subsubblock_dict['star'] is not None:
                        if 'actions' in subsubblock_dict['star'].keys() and subsubblock_dict['star']['actions'] is not None:
                            double_nested_type_dict[subblock_name][subsubblock_name]=subsubblock_dict['star']['actions']


        if len(system_type_dict) >0:
            syntax_type_to_block_types["system"].update(system_type_dict)
        if len(nested_type_dict) >0:
            syntax_type_to_block_types["nested_system"].update(nested_type_dict)
        if len(double_nested_type_dict) >0:
            syntax_type_to_block_types["double_nested"].update(double_nested_type_dict)


    if 'actions' in current_block_dict.keys() and current_block_dict['actions'] is not None:
        block_types=current_block_dict['actions']
        syntax_type_to_block_types["action"].update(block_types)


    count_types=0
    for syntax_type in syntax_type_to_block_types.keys():
        block_types=syntax_type_to_block_types[syntax_type]
        if len(block_types) > 0:
            count_types+=1

    if count_types == 0:
        msg="Block {} is undocumented".format(block_name)
        print(msg)
        #raise RuntimeError(msg)
        #block_types=None
        #syntax_type="Unknown"

    elif count_types > 1:
        msg="Block {} is has {} types".format(block_name,count_types)
        print(msg)

    #return block_types, syntax_type
    return syntax_type_to_block_types


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

    requested_blocks,syntax_type = get_block_types(json_obj,category)

    instances_out = dict()

    for block_type, block_attributes in requested_blocks.items():
        # skip any blocks that we aren't looking for
        if category_names is not None and block_type not in category_names:
            continue

        # Todo add auto-documntations
        #dict_keys(['description', 'file_info', 'label', 'moose_base', 'parameters', 'parent_syntax', 'register_file', 'syntax_path'])

        params = block_attributes['parameters']

        # Create new subclass of MooseObject with a name that matches the block_type
        new_cls = type(block_type, (MooseObject,), dict())

        # Set the block title
        new_cls.set_syntax_type(syntax_type)

        if syntax_type != "nested":
            new_cls.syntax_block_name=category

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
                            description=param_info.get('description'),
                            default=default,
                            dim=ndim,
                            allowed_vals=allowed_values)

        # insert new instance into the output dictionary
        instances_out[block_type] = new_cls

    return instances_out

def parse_problems(json_obj, problem_names=None):
    return parse_blocks_types(json_obj,'Problem',category_names=problem_names)

def problems_from_json(json_obj, problem_names=None):
    """
    Returns the Python objects corresponding to the MOOSE application described
    by the json file.

    Parameters
    ----------
    json_obj : dict
        Pre-parsed json object containing MOOSE syntax
    problems : Iterable of str
        Set of problems to generate classes for

    Returns
    -------
    dict
        A dictionary of problem objects
    """

    assert isinstance(json_obj, dict)

    out = dict()
    out['problems'] = parse_problems(json_obj, problem_names=problem_names)
    return out

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
