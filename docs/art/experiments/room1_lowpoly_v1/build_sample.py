"""Room 1 local material/geometry trial. Run with Blender --background --python.
Only creates files beside this script; starts a fresh scene; no external assets.
"""
import bpy
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
TEX = ROOT / 'textures'
OUT = ROOT / 'evidence'
for folder in (TEX, OUT):
    folder.mkdir(parents=True, exist_ok=True)
SOURCE = json.loads((ROOT / 'sources/room1_v2_parameters.json').read_text(encoding='utf-8'))
POD = next(p for p in SOURCE['pods'] if p['id'] == 'P11')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
scene.view_settings.exposure = -.6
scene.view_settings.gamma = 1
world = bpy.data.worlds.new('Neutral_review_world')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (.18,.20,.22,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = .35
scene.world = world

def group(name):
    result = bpy.data.collections.new(name)
    scene.collection.children.link(result)
    return result

shell = group('01_LOCAL_ROOM_SHELL')
podcol = group('02_P11_ENGINEERING_PLACEHOLDER')
reference = group('03_SCALE_REFERENCE_NOT_CHARACTER')
review = group('04_REVIEW_CAMERAS_AND_LIGHTS')

def relocate(obj, collection):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    collection.objects.link(obj)

def texture(name, w, h, kind):
    image = bpy.data.images.new(name, width=w, height=h, alpha=False)
    # Deterministic test color clusters; no noise or third-party reference data.
    colors = {
        'wall': [(180,184,179),(166,171,167),(195,197,192)],
        'floor': [(114,125,126),(99,111,113),(124,133,132)],
        'pod': [(202,205,198),(152,161,158),(218,220,211)],
        'label': [(202,205,198),(78,98,99),(218,220,211)],
    }[kind]
    pixels = []
    for y in range(h):
        for x in range(w):
            c = colors[0]
            if kind in ('wall','floor'):
                # 2 m test seam spacing at 32 texels/m. No geometric grooves.
                if x % 64 == 0 or y % 64 == 0:
                    c = colors[1]
                elif x % 64 == 1 or y % 64 == 1:
                    c = colors[2]
            if kind == 'pod':
                if y % 64 == 0:
                    c = colors[1]
                elif y % 64 == 1:
                    c = colors[2]
            pixels.extend([c[0]/255,c[1]/255,c[2]/255,1])
    if kind == 'label':
        # Hand-authored 5x7 test glyphs, 2 texels per glyph pixel.
        glyphs = {'P':['11110','10001','10001','11110','10000','10000','10000'],
                  '1':['00100','01100','00100','00100','00100','00100','01110']}
        for i, char in enumerate('P11'):
            for gy, row in enumerate(glyphs[char]):
                for gx, bit in enumerate(row):
                    if bit == '1':
                        for dy in range(2):
                            for dx in range(2):
                                x,y = 58+i*14+gx*2+dx, 6+(6-gy)*2+dy
                                offset=(y*w+x)*4
                                pixels[offset:offset+4]=[v/255 for v in colors[1]]+[1]
        # A stepped corner marking tests clusters rather than continuous noise.
        for y in range(4,16):
            for x in range(12,16 + ((y-4)//4)*4):
                offset=(y*w+x)*4
                pixels[offset:offset+4]=[v/255 for v in colors[1]]+[1]
    image.pixels.foreach_set(pixels)
    image.filepath_raw = str(TEX / (name+'.png'))
    image.file_format = 'PNG'
    image.save()
    return image

def material(name, color, image=None):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color,1)
    mat.use_nodes = True
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value=(*color,1)
    bsdf.inputs['Roughness'].default_value=.88
    bsdf.inputs['Metallic'].default_value=0
    bsdf.inputs['Specular IOR Level'].default_value=.18
    if image:
        node=mat.node_tree.nodes.new('ShaderNodeTexImage')
        node.image=image
        node.interpolation='Closest'
        node.extension='REPEAT'
        node.label='Neutral pixel TEST - not approved palette'
        mat.node_tree.links.new(node.outputs['Color'],bsdf.inputs['Base Color'])
    mat['status']='PROVISIONAL / neutral pipeline test'
    return mat

wallmat=material('TEST_wall_32texels_per_m',(.65,.67,.64),texture('wall_test_128',128,128,'wall'))
floormat=material('TEST_floor_32texels_per_m',(.40,.46,.46),texture('floor_test_128',128,128,'floor'))
bodymat=material('TEST_pod_surface_32texels_per_m',(.73,.76,.72),texture('pod_test_128',128,128,'pod'))
labelmat=material('TEST_P11_right_side_64texels_per_m',(.73,.76,.72),texture('P11_label_256x32',256,32,'label'))
basemat=material('TEST_base_matte',(.29,.35,.36))
lidmat=material('TEST_lid_matte',(.72,.76,.74))
windowmat=material('OBSERVATION_ZONE_OPAQUE_PLACEHOLDER',(.29,.43,.46))
scalemat=material('Scale_column_neutral',(.45,.47,.46))
clay=material('REVIEW_geometry_without_textures',(.54,.57,.56))

def uv_project(obj, density=32, image_size=(128,128), label_side=False):
    layer=obj.data.uv_layers.new(name='UV_TEST_PLANAR_TEXEL_DENSITY')
    vertices=obj.data.vertices
    mins=Vector((min(v.co.x for v in vertices),min(v.co.y for v in vertices),min(v.co.z for v in vertices)))
    for polygon in obj.data.polygons:
        axis=max(range(3),key=lambda i:abs(polygon.normal[i]))
        # X-facing faces use Y/Z, Y-facing X/Z; horizontal faces use X/Y.
        axes=((1,2),(0,2),(0,1))[axis]
        d,size=density,image_size
        if label_side and polygon.normal.x > .999:
            polygon.material_index=1
            d,size=64,(256,32)
        for loop_index in polygon.loop_indices:
            co=vertices[obj.data.loops[loop_index].vertex_index].co-mins
            layer.data[loop_index].uv=(co[axes[0]]*d/size[0],co[axes[1]]*d/size[1])
    obj['uv_method']='face planar projection, density in texels/metre; intentional surface reuse'

def prism(name,x,y,z,w,d,h,chamfer,mat,col):
    c=chamfer
    ring=[(c,0),(w-c,0),(w,c),(w,d-c),(w-c,d),(c,d),(0,d-c),(0,c)] if c else [(0,0),(w,0),(w,d),(0,d)]
    n=len(ring)
    verts=[(a,b,k) for k in (0,h) for a,b in ring]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    mesh=bpy.data.meshes.new(name+'_mesh')
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    col.objects.link(obj)
    obj.location=(x,y,z)
    mesh.materials.append(mat)
    obj['status']='PROVISIONAL / inherited engineering occupancy, not final industrial design'
    uv_project(obj)
    return obj

# Coordinates use the engineering convention: origin at outer front-left, +Y rear.
# Only crop shell segments. Nothing is moved to make the local composition.
floor=prism('Local_floor_crop',.2,5.5,-.10,4.5,3.8,.10,0,floormat,shell)
leftwall=prism('Local_left_wall_0p20m',0,5.5,0,.2,4.0,3.4,0,wallmat,shell)
rearwall=prism('Local_rear_wall_0p20m',.2,9.3,0,4.5,.2,3.4,0,wallmat,shell)
x,y,w,d=POD['x'],POD['y'],POD['w'],POD['d']
base=prism('P11_Base_inherited',x,y,0,w,d,.20,.12,basemat,podcol)
body=prism('P11_Body_inherited',x+.04,y+.04,.24,w-.08,d-.08,.40,.14,bodymat,podcol)
body.data.materials.append(labelmat)
body.data.uv_layers.remove(body.data.uv_layers.active)
uv_project(body,label_side=True)
lid=prism('P11_Lid_inherited',x+.06,y+.06,.68,w-.12,d-.12,.30,.16,lidmat,podcol)
window=prism('P11_Head_zone_inherited',x+.16,y+d-.18-.5,.98,w-.32,.50,.02,.07,windowmat,podcol)
for obj in (base,body,lid,window):
    obj['engineering_pod_id']='P11'
    obj['source_coordinate_system']='outer front-left origin / +Y toward rear door / metres'

# Simple size marker, not a person/rig/character asset. Inside the .70m side gap.
bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=.15,depth=1.68,location=(x+w+.35,y+1.15,.84))
scale=bpy.context.object
scale.name='Scale_column_1p68m_NOT_CHARACTER'
relocate(scale,reference)
scale.data.materials.append(scalemat)
uv_project(scale)
scale['status']='PROVISIONAL static scale marker; does not validate turning or boarding'

def camera(name,target,offset,ortho):
    data=bpy.data.cameras.new(name)
    data.type='ORTHO'
    data.ortho_scale=ortho
    data.clip_end=200
    obj=bpy.data.objects.new(name,data)
    review.objects.link(obj)
    target=Vector(target)
    obj.location=target+Vector(offset)
    obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
    obj['status']='review candidate; not final gameplay camera'
    return obj

cam=camera('Camera_A_local_near_side_candidate',(2.45,7.5,1.35),(4.5,-9,5.15),6.2)
close=camera('Camera_C_pixel_surface_close',(1.9,7.7,.58),(3.5,-4,2.3),3.1)
scene.camera=cam

def area(name,location,energy,size):
    data=bpy.data.lights.new(name,'AREA')
    data.energy=energy
    data.shape='DISK'
    data.size=size
    obj=bpy.data.objects.new(name,data)
    review.objects.link(obj)
    obj.location=location
    obj.rotation_euler=(Vector((2.0,7.5,.5))-obj.location).to_track_quat('-Z','Y').to_euler()
    obj['status']='neutral inspection light, not a room fixture or story lighting'

area('REVIEW_key_not_room_fixture',(5,4.5,6),400,5)
area('REVIEW_fill_not_room_fixture',(2,6,4),100,3)

# Outline export allows UV inspection without relying on an unavailable editor plugin.
lines=['<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">',
       '<rect width="1024" height="1024" fill="#e7e8e2"/>']
uv=body.data.uv_layers.active
for p in body.data.polygons:
    if p.material_index != 1:
        continue
    points=' '.join(f'{uv.data[i].uv.x*1024:.2f},{1024-uv.data[i].uv.y*1024:.2f}' for i in p.loop_indices)
    lines.append(f'<polygon points="{points}" fill="none" stroke="#263c40" stroke-width="3"/>')
lines.append('</svg>')
(TEX/'P11_right_side_UV.svg').write_text('\n'.join(lines),encoding='utf-8')

def capture(filename,active_camera,override=None):
    scene.camera=active_camera
    scene.view_layers[0].material_override=override
    scene.render.filepath=str(OUT/filename)
    bpy.ops.render.render(write_still=True)

capture('A_target_camera.png',cam)
capture('B_geometry_without_textures.png',cam,clay)
scale.hide_render=True
capture('C_pixel_texture_close.png',close)
scale.hide_render=False
scene.camera=cam
scene.view_layers[0].material_override=None
scene.render.filepath='//evidence/A_target_camera.png'

report={
    'status':'REVIEW_REQUIRED / technical sample only',
    'authority_commit':'766411e0926511fb77635e5307039927dc960874',
    'source_pod':POD,
    'room_envelope_m':[21,9.5],
    'local_floor_crop_m':[.2,5.5,4.5,3.8],
    'wall_height_m':3.4,
    'texel_density_provisional':{'wall_floor_body':32,'label_side':64},
    'texture_sizes':{im.name:list(im.size) for im in bpy.data.images if im.type=='IMAGE'},
    'camera':{'projection':'ORTHO','ortho_scale':cam.data.ortho_scale,
              'position':list(cam.location),'rotation_radians':list(cam.rotation_euler),
              'depression_degrees':math.degrees(math.atan2(5.15,math.hypot(4.5,9)))},
    'meshes':{o.name:{'world_location':list(o.location),'dimensions_m':list(o.dimensions),
                        'polygon_count':len(o.data.polygons),'uv_layers':len(o.data.uv_layers)}
              for o in scene.objects if o.type=='MESH'},
    'render_resolution':[1600,1000],
    'limitations':['not final pod design or palette','opaque observation-zone placeholder',
                  'static scale column only','no gameplay or Godot migration',
                  'no lid opening, boarding or collision sweep validation'],
}
scene['brief']='docs/art/ROOM1_LOW_POLY_PROTOTYPE_BRIEF.md'
scene['design_status']='REVIEW REQUIRED - neutral local pipeline sample'
scene['engineering_coordinate_origin']='front-left outer / +Y rear door / metres'
for area_ui in bpy.context.screen.areas if bpy.context.screen else []:
    if area_ui.type=='VIEW_3D':
        area_ui.spaces.active.region_3d.view_perspective='CAMERA'
        area_ui.spaces.active.shading.type='MATERIAL'
for image in bpy.data.images:
    if image.type=='IMAGE':
        image.pack()
        image.filepath='//textures/'+Path(image.filepath).name
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'room1_lowpoly_sample_v1.blend'))
(ROOT/'sample_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('ROOM1_SAMPLE_SAVED',ROOT)
