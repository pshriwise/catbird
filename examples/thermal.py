from catbird import *
import os
import subprocess
import sys

def main():
    # Get path to MOOSE
    moose_path=os.environ['MOOSE_DIR']

    # Path to executable and inputs
    module_name="heat_transfer"
    app_name=module_name+"-opt"
    app_path=os.path.join(moose_path,"modules",module_name)
    app_exe=os.path.join(app_path,app_name)

    # Create a factory of available objects from our MOOSE executable
    factory=Factory(app_exe)
     
    config_name="config_heat_conduction.json"
    factory.write_config(config_name)

    # Create a boiler plate MOOSE model from a template
    model=TransientModel(factory)

    # Set executioner attributes
    model.executioner.end_time=5
    model.executioner.dt=1 # Default

    # Add a mesh generator
    model.add_mesh_generator("generated","GeneratedMeshGenerator",
                             dim=2,
                             nx=10,
                             ny=10,
                             xmax=2,
                             ymax=1)
    
    # Add variables
    var_name="T"
    model.add_variable(var_name, initial_condition=300.0)

    # Add kernels
    model.add_kernel("heat_conduction", kernel_type="HeatConduction", variable=var_name)
    model.add_kernel("time_derivative", kernel_type="HeatConductionTimeDerivative", variable=var_name)

    # Add boundary conditions
    model.add_bc("t_left",
                 bc_type="DirichletBC",
                 variable=var_name,
                 value = 300,
                 boundary='left')

    model.add_bc("t_right",
                 bc_type="FunctionDirichletBC",
                 variable=var_name,
                 function = "'300+5*t'",
                 boundary = 'right')

    # Add materials
    model.add_material("thermal",
                       mat_type="HeatConductionMaterial",
                       thermal_conductivity=45.0,
                       specific_heat=0.5)

    model.add_material("density",
                       mat_type="GenericConstantMaterial",
                       prop_names='density',
                       prop_values=8000.0)

    model.outputs.exodus=True
    model.add_output("csv",output_type="CSV",
                     file_base='thermal_out',
                     execute_on='final')    
        
    # Add some input syntax that wasn't in the vanilla boilerplate model
    model.add_syntax("VectorPostprocessors")
    model.add_to_collection("VectorPostprocessors",
                            "VectorPostprocessor",
                            "t_sampler",
                            collection_type="LineValueSampler",
                            variable=var_name,
                            start_point='0 0.5 0',
                            end_point='2 0.5 0',
                            num_points=20,                            
                            sort_by='x')
    
    # Write out our input file
    input_name="thermal.i"
    model.write(input_name)

    # Run
    args=[app_exe,'-i',input_name]
    moose_process=subprocess.Popen(args)
    stream_data=moose_process.communicate()[0]
    retcode=moose_process.returncode 

    # Return moose return code
    sys.exit(retcode)

if __name__ == "__main__":
    main()

    
