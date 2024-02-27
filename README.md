![CI](https://github.com/pshriwise/catbird/actions/workflows/ci.yml/badge.svg)

Catbird
-------

A code for generation of Python objects and input for various [MOOSE](https://moose.inl.gov/SitePages/Home.aspx).

Prerequisites
-------------

  - Python version >=3.6
  - [NumPy](https://numpy.org/)
  - `pytest` (for testing)

Installation
------------

From a terminal, run

```bash
pip install .
```

To include packages for testsing, run

```bash
pip install .[test]
```

# Usage

## Load syntax into a Factory
First, import the package and load available syntax from a MOOSE application.

```python
>>> from catbird import *
>>> factory=Factory('./heat_conduction-opt')
```
This may take a few minutes, so don't panic if it hangs. The syntax first has to be dumped from the original application as json and then parsed;
the factory then converts "available" syntax into python object constructors. The more syntax we enable the longer it takes, so if you want
to speed things up you should only enable the syntax you intend to use. To write out what objects are  currently enabled, try:
```python
>>> factory.write_config("config.json")
```
We could then edit that file and load it via an optional constructor argument to `Factory`:
```python
>>> lightweight_factory=factory=Factory('./heat_conduction-opt', config="lighweight_config.json")
```
However, modifying the config file directory is likely to be very laborious if done manually. Another option
is to derive your own Factory class and override the `set_defaults` method. To limit the enabled syntax, we can pass in dictionaries
of enabled syntax into the `enable_syntax` method, e.g.:
```
executioner_enable_dict={
  "obj_type": ["Steady","Transient"]
}
self.enable_syntax("Mesh")
self.enable_syntax("Executioner", executioner_enable_dict)
```

## Create a Model
With our factory built, all we have in practice is bunch of constructor objects. We now need to create the objects and assemble them as a `Model`:
```python
>>> model=MooseModel(factory)
```
This will have created a "boiler-plate" model with some sensible base objects to work with. We can now start to set their attributes in an object-oriented way.
```
>>> model.mesh.dim=2
```
To see the available attributes for a given object, just use "help" to obtain useful documentation e.g.:
```
>>> help(model.mesh)
```
The help will also print the type and valid options. Type checking of attributes is performed, and if the type (i) incompatible with the expected type
and (ii) not castable as the expected type then a ValueError exception is raised, e.g.
```
>>> model.mesh.dim='2' # This is fine, MOOSE expects string
>>> model.mesh.dim=2 # This is fine, str(2) is valid
>>> model.mesh.nx=1 # This is fine, MOOSE expects in
>>> model.mesh.nx="hello" # This raises a ValueError as int("hello") is invalid
```

Many of the objects are `Collection` types, i.e. a collection MOOSE objects, for example Variables. To add a variable, we must call:
```
>>> model.add_variable("T", order="SECOND")
```
Notice the use of key-word arguments in this function call. We can also act on the created object directly, via
```
>>> model.add_variable("T")
>>> model.variables.objects["T"].order="SECOND"
```

Even if the root-level syntax hasn't been added to the model (but is available in the factory) we can still add it to our model through `add_syntax` calls:
```
model.add_syntax("VectorPostprocessors")
```
Since this is a Collection type, to add a specific VectorPostprocessor, we call the add_to_collection method:
```
model.add_to_collection("VectorPostprocessors","VectorPostprocessor","t_sampler")
```

It is generally expected that the user will develop their own class derived from `MooseModel`, overriding the method `load_default_syntax`.
See for example TransientModel in `model.py`.


## Write to file
Finally if we are happy with our model we can write to file:
```python
>>> model.write("catbird_input.i")
```
You can run that input from the command line as you normally would or launch a subprocess.

Note, if you inspect our file `catbird_input.i` you may not see all attributes written out. The default behaviour is that parameters that are unchanged relative to
their default value are suppressed when writing to file. To see all attributes, instead run
```python
>>> model.write("catbird_input_full.i", print_default=True)
```

Example
-------
A fully worked heat conduction example may be found in: `catbird/examples/thermal.py`. Run with
```bash
$ python examples/thermal.py
```

