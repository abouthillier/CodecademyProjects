import os
import numpy as np
from pyproj import Proj
from mathutils import Matrix, Vector
from matplotlib import cm
import matplotlib.pyplot as plt
import pandas as pd
import bpy
import bmesh
import utils
from math import sin, cos, pi
# from geopy.geocoders import Nominatim

def normalize_points(points):
    """Normalize points while preserving aspect ratio"""

    data = np.array(points)

    minX, minY = np.min(data, axis=0)
    maxX, maxY = np.max(data, axis=0)
    rangeX, rangeY = maxX - minX, maxY - minY

    if rangeX > rangeY:
        data[:, 0] = (data[:, 0] - minX - 0.5*rangeX) / rangeX + 0.5
        data[:, 1] = (data[:, 1] - minY - 0.5*rangeY) / rangeX + 0.5
    else:
        data[:, 0] = (data[:, 0] - minX - 0.5*rangeX) / rangeY + 0.5
        data[:, 1] = (data[:, 1] - minY - 0.5*rangeY) / rangeY + 0.5

    return data


def heatmap_grid(data, sigma_sq=0.0001, n=20, m=2):
    """Create n by n grid with heatmap from data with gaussian distribution of input data set"""

    X = np.ndarray((n, n), dtype=object)
    for idx in np.arange(len(points)):
        # print('Index: ', idx, ' Row Data: ', data[idx])
        x, y = data[idx]
        i, j = int(x * (n - 1)), int(y * (n - 1))
        # print('i: ', i)
        # print('j: ', j)
        if X[i, j] is None:
            X[i, j] = [(x, y)]
        else:
            X[i, j].append((x, y))
    
    grid = np.zeros((n, n))

    for i0 in range(n):
        for j0 in range(n):
            x0, y0 = i0 / (n - 1), j0 / (n - 1)

            # Sum all available neighboring elements
            for i in range(max(0, i0 - m), min(i0 + m, n)):
                for j in range(max(0, j0 - m), min(j0 + m, n)):
                    if X[i, j] is not None:
                        for x, y in X[i, j]:
                            grid[i0][j0] += np.exp(- ((x0 - x)**2)/
                                (2*sigma_sq) - ((y0 - y)**2)/(2*sigma_sq))

    return grid


def heatmap_barplot(grid, h=4, width=10, bar_scale=0.95, num_colors=10, colormap=cm.summer, bevel_width=0.015, logarithmic=False):
    """Create 3D barplot from heatmap grid"""

    # Logarithmic scale
    if logarithmic:
        grid = np.log(grid + 1)

    # Find maximum value
    z_max = np.max(grid)

    n, m = grid.shape
    bar_width = bar_scale * width / max(n, m)

    # List of bmesh elements for each color group
    bmList = [bmesh.new() for _ in range(num_colors)]

    # Iterate over grid
    for i in range(n):
        for j in range(m):
            x, y, z = i / (n - 1), j / (m - 1), grid[i][j]
            if z > 0.001:
                bar_height = ((h - bar_width) * z / z_max) + bar_width
                t = 1 - np.exp(-(z / z_max)/0.2)
                k = min(int(num_colors*t), num_colors - 1)
                bm = bmList[k]

                T = Matrix.Translation(Vector((
                    width*(x - 0.5),
                    width*(y - 0.5),
                    bar_height / 2)))

                S = Matrix.Scale(bar_height / bar_width, 4, Vector((0, 0, 1)))

                if bpy.app.version < (2, 80, 0):
                    bmesh.ops.create_cube(bm, size=bar_width, matrix=T*S)
                else:
                    bmesh.ops.create_cube(bm, size=bar_width, matrix=T@S)

    objList = []
    for i, bm in enumerate(bmList):
        # Create object
        obj = utils.bmesh_to_object(bm)

        # Create material with colormap
        color = colormap(i / num_colors)
        mat = utils.simple_material(color[:3])
        obj.data.materials.append(mat)
        objList.append(obj)

        # Add bevel modifier
        bevel = obj.modifiers.new('Bevel', 'BEVEL')
        bevel.width = bevel_width

    ground = utils.create_ground(color[:3])


def heatmap_barplot_separate(grid, h=4, width=10, bar_scale=0.95, num_colors=10, colormap=cm.summer, bevel_width=0.015, logarithmic=False, animation=False):
    """Create 3D barplot from heatmap grid"""

    # Logarithmic scale
    if logarithmic:
        grid = np.log(grid + 1)

    # Find maximum value
    z_max = np.max(grid)

    n, m = grid.shape
    bar_width = bar_scale * width / max(n, m)

    # List of bmesh elements
    bmList = []

    # Iterate over grid
    for i in range(n):
        for j in range(m):
            x, y, z = i / (n - 1), j / (m - 1), grid[i][j]
            if z > 0.001:

                bar_height = ((h - bar_width) * z / z_max) + bar_width

                bm = bmesh.new()
                bmList.append(bm)

                T = Matrix.Translation(Vector((
                    width*(x - 0.5),
                    width*(y - 0.5),
                    bar_height / 2)))

                S = Matrix.Scale(bar_height / bar_width, 4, Vector((0, 0, 1)))

                if bpy.app.version < (2, 80, 0):
                    bmesh.ops.create_cube(bm, size=bar_width, matrix=T*S)
                else:
                    bmesh.ops.create_cube(bm, size=bar_width, matrix=T@S)

                obj = utils.bmesh_to_object(bm)

                if animation:
                    start = obj.location - Vector((0,0,bar_height+0.01))
                    obj.location = start
                    obj.keyframe_insert(data_path='location', frame=12)
                    obj.location = start + Vector((0,0,bar_height))
                    obj.keyframe_insert(data_path='location', frame=52)

                # Add bevel modifier
                bevel = obj.modifiers.new('Bevel', 'BEVEL')
                bevel.width = bevel_width

                # Create material with colormap
                color = colormap((z/z_max))
                mat = utils.simple_material(color[:3])
                obj.data.materials.append(mat)

    ground = utils.create_ground(colormap(z_max))

# Load data points
filepath = 'data/Electric_Vehicle_Charging_Stations.csv'
# filepath = 'data/data.csv'

longitude = 'LONGITUDE'
latitude = 'LATITDE'
quantity = ''

# longitude = 'X'
# latitude = 'Y'
# quantity = 'num_Indivi'

# Check if script is executed in Blender and get absolute path of current folder
if bpy.context.space_data is not None:
    cwd = os.path.dirname(bpy.context.space_data.text.filepath) + '/'
else:
    cwd = os.path.dirname(os.path.abspath(__file__))

datapath = cwd + '/' + filepath
dataframe = pd.read_csv(datapath)

points = dataframe.get([longitude, latitude]).values.tolist()

print('Number of points: {}'.format(len(points)))

# Project points into Mercator projection
p = Proj("epsg:3785")  # Popular Visualisation CRS / Mercator
points_projected = np.apply_along_axis(lambda x : p(*x), 1, points)

data = normalize_points(points_projected)

print('Points projected and normalized.')

"""

Blender Scene Variables

"""
print('Setting the scene...')

# # Get the name of the geographic location specified
# geolocator = Nominatim(user_agent="blender_render")
# latlong = str(points[0][0])+","+str(points[0][-1])
# print(latlong)
# location = geolocator.reverse(latlong)
# print(location)
# state = location.address.get('state', '')

# Set resolution of rendered image
res_x, res_y = 1280, 720
graphic_width = 10
camera_position = (10, -25, 20)
target_position = (0.3, -1.8, 4)
label_text = filepath[5:-4].replace('_', ' ')
label_position = (0, -6, 0.01)
label_scale = 0.5
camera_type, ortho_scale, lens = 'PERSP', 18, 50
bg_color = (0.9, 0.9, 0)
animation = True
num_frames = 250

# Remove all default elements in the scene
if bpy.app.version < (2, 80, 0):
    bpy.ops.object.select_by_layer()
else:
    bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Create scene
target = utils.create_target(name='SunTarget', origin=target_position)
camera = utils.create_camera(camera_position, camera_type=camera_type, ortho_scale=ortho_scale, lens=lens, animation=animation)
sun = utils.create_lamp((5, 5, 10), 'SUN', target=target)
label = utils.create_text(text=label_text, position=label_position, label_scale=label_scale)
#utils.create_text(str(max(weight)), (0,0,5), (pi/2,0,0))

# Set background color
if bpy.app.version < (2, 80, 0):
    bpy.context.scene.world.horizon_color = bg_color
else:
    bpy.context.scene.world.color = bg_color

# Ambient occlusion
bpy.context.scene.world.light_settings.use_ambient_occlusion = True
if bpy.app.version < (2, 80, 0):
    bpy.context.scene.world.light_settings.samples = 8


"""
Generate a 2D Heatmap from the X,Y data

"""
print('Generating Heatmap...')
hist = heatmap_grid(data, sigma_sq=0.00005, n=100, m=2) 

if quantity:
# Rather than ony map density of X,Y, weight the coordinates based on the num_Indivi values
    weight = np.ravel(dataframe.get([quantity]).values.tolist())
    heatmap = [[hist[row][col] * weight[row] for col in range(len(hist[0]))] for row in range(len(hist))]
else:
    heatmap = hist

"""
Generate 3D barplot from the heatmap grid

Color Map Reference:
https://matplotlib.org/stable/gallery/color/colormap_reference.html

Perceptually Uniform Options: viridis, plasma, inferno, magma, cividis

"""
print('Generating 3D barplot...')
heatmap_barplot_separate(np.array(heatmap), colormap=cm.viridis, animation=animation)


"""
Render the barplot to an exported image

"""
render_folder = 'render'
render_name = 'render'
utils.render_to_folder(render_folder, render_name, res_x=res_x, res_y=res_y, animation=animation, frame_end=num_frames, render_opengl=False)
