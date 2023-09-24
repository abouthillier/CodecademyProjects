import os
import bpy
import bmesh
from matplotlib import cm
from math import pi

def simple_material(diffuse_color):
    mat = bpy.data.materials.new('Material')

    # Diffuse
    if bpy.app.version < (2, 80, 0):
        mat.diffuse_shader = 'LAMBERT'
        mat.diffuse_intensity = 0.9
        mat.diffuse_color = diffuse_color
    else:
        _diffuse_color = (diffuse_color + (0.9,))
        mat.diffuse_color = _diffuse_color

    # Specular
    mat.specular_intensity = 0

    return mat

def bmesh_to_object(bm, name='Object'):
    mesh = bpy.data.meshes.new(name+'Mesh')
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    if bpy.app.version < (2, 80, 0):
        bpy.context.scene.objects.link(obj)
        bpy.context.scene.update()
    else:
        bpy.context.collection.objects.link(obj)
        bpy.context.view_layer.update()
    return obj

def track_to_constraint(obj, target):
    constraint = obj.constraints.new('TRACK_TO')
    constraint.target = target
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'

def create_target(origin=(0,0,0)):
    tar = bpy.data.objects.new('Target', None)
    if bpy.app.version < (2, 80, 0):
        bpy.context.scene.objects.link(tar)
    else:
        bpy.context.collection.objects.link(tar)
    tar.location = origin

    return tar

def create_camera(origin=(0,0,0), target=None, lens=35, clip_start=0.1, clip_end=200, camera_type='PERSP', ortho_scale=6, animation=False):
    # Create object and camera
    camera = bpy.data.cameras.new("Camera")
    camera.lens = lens
    camera.clip_start = clip_start
    camera.clip_end = clip_end
    camera.type = camera_type # 'PERSP', 'ORTHO', 'PANO'
    if camera_type == 'ORTHO':
        camera.ortho_scale = ortho_scale

    # Link object to scene
    obj = bpy.data.objects.new("CameraObj", camera)
    obj.location = origin
    if bpy.app.version < (2, 80, 0):
        bpy.context.scene.objects.link(obj)
    else:
        bpy.context.collection.objects.link(obj)
    bpy.context.scene.camera = obj # Make this the current camera

    # Anchor camera pointed to target
    if target: track_to_constraint(obj, target)

    # Orbit camera around rendering
    if animation:

        bpy.ops.curve.primitive_bezier_circle_add(radius=5)
        circle = bpy.context.object
        circle.rotation_euler = (0,0,pi)
        circle.location = (0,0,-6.5)
        circle.keyframe_insert('rotation_euler', frame=1)
        circle.keyframe_insert('location', frame=1)
        circle.rotation_euler = (0,0,2*pi)
        circle.location = (0,0,0)
        circle.keyframe_insert('rotation_euler', frame=240)
        circle.keyframe_insert('location', frame=240)

        # Follow Path Constraint
        fp_constraint = obj.constraints.new('FOLLOW_PATH')
        fp_constraint.target = circle

    return obj

def create_lamp(origin, type='POINT', energy=1, color=(1,1,1), target=None):
    # Lamp types: 'POINT', 'SUN', 'SPOT', 'HEMI', 'AREA'
    if bpy.app.version < (2, 80, 0):
        bpy.ops.object.add(type='LAMP', location=origin)
        obj = bpy.context.object
        obj.data.type = type
        obj.data.energy = energy
        obj.data.color = color
    else:
        light_data = bpy.data.lights.new(name='New light', type=type)
        obj = bpy.data.objects.new(name='New light', object_data=light_data)
        obj.location = origin
        light_data.energy = energy
        light_data.color = color
        bpy.context.collection.objects.link(obj)

    if target: track_to_constraint(obj, target)
    return obj

def create_text(text, position=(0,0,0.01), label_scale=1, rotation=(0,0,0)):

    text_curve = bpy.data.curves.new(type="FONT", name="Font Curve")
    text_curve.body = text
    text_curve.align_x = 'CENTER'

    obj = bpy.data.objects.new(name="Font Object", object_data=text_curve)
    obj.location = position
    obj.scale = (label_scale, label_scale, label_scale)
    obj.rotation_euler = rotation
    mat = simple_material((0,0,0))
    obj.data.materials.append(mat)

    bpy.context.scene.collection.objects.link(obj)
    return obj

def render_to_folder(render_folder='render', render_name='render', res_x=800, res_y=800, res_percentage=100, animation=False, frame_end=None, render_opengl=False):
    
    # Set the camera to the active view
    area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
    area.spaces[0].region_3d.view_perspective = 'CAMERA'

    scene = bpy.context.scene
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.resolution_percentage = res_percentage
    scene.render.engine = 'BLENDER_EEVEE'
    if frame_end:
        scene.frame_end = frame_end

    # Check if script is executed inside Blender
    if bpy.context.space_data or render_opengl:
        # Specify folder to save rendering and check if it exists
        render_folder = os.path.join(os.getcwd(), render_folder)
        if(not os.path.exists(render_folder)):
            os.mkdir(render_folder)
        print('Rendering...')
        if animation:
            # Render animation
            scene.render.filepath = os.path.join(render_folder, render_name)
            if render_opengl:
                bpy.ops.render.opengl(animation=True, view_context=False)
            else:
                bpy.ops.render.render(animation=True)
        else:
        # Render still frame
            scene.render.filepath = os.path.join(render_folder, render_name + '.png')
            if render_opengl:
                bpy.ops.render.opengl(write_still=True, view_context=False)
            else:
                bpy.ops.render.render(write_still=True)

def create_ground(color):

    # TODO 
    # Only create a plane for the area seen by the active camera
    # frame points currently fill the camera view
    # Nex step is to project those vectors onto the origin with z=0
    
    # frame_px, frame = view3d_camera_border(bpy.context.scene)
    # print("Camera frame:", frame_px)
    
    bm = bmesh.new()
    
    # for point in frame_px:
        #     print(point)
        #     bm.verts.new((point))

    s = 40
    bm.verts.new((s,s,0))
    bm.verts.new((s,-s,0))
    bm.verts.new((-s,s,0))
    bm.verts.new((-s,-s,0))

    bmesh.ops.contextual_create(bm, geom=bm.verts)

    obj = bmesh_to_object(bm, "Ground")
    mat = simple_material(color[:3])
    obj.data.materials.append(mat)

    return obj

# Currently unused
def view3d_find():
    # returns first 3d view, normally we get from context
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            v3d = area.spaces[0]
            rv3d = v3d.region_3d
            for region in area.regions:
                if region.type == 'WINDOW':
                    return region, rv3d
    return None, None

# Currently unused
def view3d_camera_border(scene):
    obj = scene.camera
    cam = obj.data

    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces[0].region_3d.view_perspective = 'CAMERA'

    frame = cam.view_frame(scene=scene)

    # move from object-space into world-space 
    frame = [obj.matrix_world @ v for v in frame]
    # print(frame)

    # move into pixelspace
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    region, rv3d = view3d_find()
    frame_px = [location_3d_to_region_2d(region, rv3d, v) for v in frame]
    return frame_px, frame