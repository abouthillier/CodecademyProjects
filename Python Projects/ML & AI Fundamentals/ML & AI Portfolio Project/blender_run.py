import bpy
import os
import sys
import importlib

# Specify the script to be executed
scriptFile = "blender_render.py"

# Check if script is executed in Blender and get absolute path of current folder
if bpy.context.space_data is not None:
    cwd = os.path.dirname(bpy.context.space_data.text.filepath)
else:
    cwd = os.path.dirname(os.path.abspath(__file__))

#print(os.path.dirname(bpy.context.space_data.text.filepath))
#print(os.path.dirname(os.path.abspath(__file__)))

#Override Blender check. Blender check returns '//' for some reason, breaking execution
#cwd = os.path.dirname(os.path.abspath(__file__))
#print(cwd)

# Get scripts folder and add it to the search path for modules
sys.path.append(cwd)

# Change current working directory to scripts folder
#os.chdir(cwd)

# Compile and execute script file
file = os.path.join(cwd, scriptFile)

# Reload the previously imported modules
import utils
if 'utils' in locals():
    importlib.reload(utils)


exec(compile(open(file).read(), scriptFile, 'exec'))
