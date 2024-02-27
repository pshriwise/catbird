"""I/O utilities"""
import json
import subprocess

def json_from_exec(exec):
    """
    Returns the Python objects corresponding to the MOOSE application described
    by the json file.

    Parameters
    ----------
    json_file : str, or Path
        Either an open file handle, or a path to the json file. If `json` is a
        dict, it is assumed this is a pre-parsed json object.

    Returns
    -------
    dict
        A dictionary of all MOOSE objects
    """
    json_proc = subprocess.Popen([exec, '--json'], stdout=subprocess.PIPE)
    json_str = ''

    # filter out the header and footer from the json data
    while json_proc.stdout.readline().decode().find('**START JSON DATA**') < 0:
        pass

    while True:
        line = json_proc.stdout.readline().decode()
        if not line or line.find('**END JSON DATA**') >= 0:
            break
        json_str += line

    j_obj = json.loads(json_str)

    return j_obj

def write_json(json_dict_out,name):
    """
    Write a dictionary in JSON format

    Parameters
    ----------
    json_dict_out : dict
    name: str
      Save as name.json
    """
    json_output = json.dumps(json_dict_out, indent=4)
    json_name=name
    if json_name.find(".json") < 0 :
        json_name = name+".json"

    with open(json_name, "w") as fh:
        fh.write(json_output)
        fh.write("\n")
    print("Wrote to ",json_name)


def read_json(json_file):
    """
    Load the contents of a JSON file into a dict.

    Parameters
    ----------
    json_file: str
      Name of JSON file
    """
    json_dict = {}
    with open(json_file) as handle:
        json_dict = json.load(handle)
    return json_dict
