"""Original, separated static protagonist candidate. Blender 5.0+, no add-ons.

Run: blender --background --factory-startup --python-exit-code 1 --python build_character.py
-- --quick renders at half resolution. --skip-render only rebuilds source/export.
All model coordinates: metres, +Z up, face toward -Y, origin between feet.
"""
import bpy
import bmesh
import math
import json
import sys
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from texture_authoring import make_textures

for folder in ('textures', 'uv_guides', 'evidence'):
    (ROOT / folder).mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0
QUICK = '--quick' in sys.argv
SCENE = bpy.context.scene
SCENE.name = '01_Character_Review'
ASSET = bpy.data.collections.new('PLAYER_165cm_SEPARATED_STATIC_CANDIDATE')
SCENE.collection.children.link(ASSET)
PARTS = []
IMAGES = make_textures(ROOT)
BOXES = {
    'gown': ('cloth', (4, 4, 124, 148)),
    'sleeve_L': ('cloth', (4, 156, 60, 232)),
    'sleeve_R': ('cloth', (68, 156, 124, 232)),
    'collar': ('cloth', (4, 238, 60, 252)),
    'cap': ('hair', (4, 4, 60, 40)),
    'back': ('hair', (4, 48, 92, 116)),
    'fringe': ('hair', (68, 4, 124, 36)),
    'lock_L': ('hair', (98, 44, 108, 116)),
    'lock_R': ('hair', (114, 44, 124, 116)),
    'head': ('skin', (4, 4, 68, 38)),
    'torso': ('skin', (4, 44, 60, 90)),
    'arm': ('skin', (66, 44, 82, 100)),
    'leg': ('skin', (86, 44, 108, 120)),
    'hand': ('skin', (4, 98, 20, 124)),
    'foot': ('skin', (24, 98, 52, 124)),
    'neck': ('skin', (74, 4, 98, 24)),
}

def configure(scene, width, height):
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 50 if QUICK else 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.film_transparent = False
    scene.render.image_settings.color_depth = '8'
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    world = bpy.data.worlds.new(scene.name + '_World')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (.105, .135, .15, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = .45
    scene.world = world

def material(kind, export=False):
    m = bpy.data.materials.new(('EXPORT_' if export else 'REVIEW_') + kind + '_replaceable_pixel_basecolor')
    m.use_nodes = True
    m.diffuse_color = {'cloth': (.65, .72, .71, 1), 'skin': (.55, .39, .30, 1), 'hair': (.025, .045, .063, 1)}[kind]
    n = m.node_tree.nodes
    n.clear()
    link = m.node_tree.links
    tex = n.new('ShaderNodeTexImage')
    tex.name = 'REPLACE_THIS_BASE_COLOR'
    tex.label = 'Replaceable draft / explicit UV / nearest sampling'
    tex.image = IMAGES[kind]
    tex.interpolation = 'Closest'
    tex.extension = 'EXTEND'
    tex.location = (-600, 160)
    output = n.new('ShaderNodeOutputMaterial')
    if export:
        shader = n.new('ShaderNodeBsdfPrincipled')
        shader.inputs['Roughness'].default_value = 1
        shader.inputs['Specular IOR Level'].default_value = 0
        link.new(tex.outputs['Color'], shader.inputs['Base Color'])
    else:
        diffuse = n.new('ShaderNodeBsdfDiffuse')
        diffuse.inputs['Color'].default_value = (1, 1, 1, 1)
        diffuse.inputs['Roughness'].default_value = 1
        diffuse.location = (-600, -140)
        rgb = n.new('ShaderNodeShaderToRGB')
        rgb.location = (-400, -140)
        link.new(diffuse.outputs[0], rgb.inputs[0])
        ramp = n.new('ShaderNodeValToRGB')
        ramp.location = (-210, -140)
        ramp.color_ramp.interpolation = 'CONSTANT'
        ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
        for i, (pos, value) in enumerate([(0, .66), (.2, .84), (.52, 1)]):
            e = ramp.color_ramp.elements[0] if i == 0 else ramp.color_ramp.elements.new(pos)
            e.position = pos
            e.color = (value, value, value, 1)
        link.new(rgb.outputs['Color'], ramp.inputs[0])
        multiply = n.new('ShaderNodeMixRGB')
        multiply.blend_type = 'MULTIPLY'
        multiply.inputs[0].default_value = 1
        multiply.location = (40, 100)
        link.new(tex.outputs['Color'], multiply.inputs[1])
        link.new(ramp.outputs['Color'], multiply.inputs[2])
        shader = n.new('ShaderNodeEmission')
        link.new(multiply.outputs[0], shader.inputs[0])
        m['preview_only'] = 'EEVEE three-step light; GLB uses rough diffuse baseline. No Godot shader equivalence claimed.'
    shader.location = (250, 100)
    output.location = (480, 100)
    link.new(shader.outputs[0], output.inputs['Surface'])
    return m

REVIEW_MATS = {k: material(k) for k in IMAGES}
EXPORT_MATS = {k: material(k, True) for k in IMAGES}

def mesh(name, verts, faces, face_uvs, uv_key, smooth=True, category='body'):
    data = bpy.data.meshes.new(name + '_QUADS')
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    ASSET.objects.link(obj)
    kind, box = BOXES[uv_key]
    data.materials.append(REVIEW_MATS[kind])
    uv = data.uv_layers.new(name='UV_REPLACEABLE_' + kind.upper())
    uv.active_render = True
    w, h = IMAGES[kind].size
    a, b, c, d = box
    for p, coords in zip(data.polygons, face_uvs):
        for li, (u, v) in zip(p.loop_indices, coords):
            uv.data[li].uv = ((a + u * (c-a))/w, (b + v * (d-b))/h)
        p.use_smooth = smooth
    # Recompute orientation, preserving UVs. No voxel/remesh/union applied.
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    obj['category'] = category
    obj['texture_family'] = kind
    obj['uv_region'] = uv_key
    obj['uv_pixels'] = list(box)
    obj['status'] = 'static candidate; no rig or deformation validation'
    obj['construction'] = 'separate editable low-poly quad mesh; not welded to other parts'
    PARTS.append(obj)
    return obj

def loft(name, rings, n, uv_key, cap_bottom=True, cap_top=True, adjust=None, skip=None, smooth=True, category='body'):
    # Each ring: centre x,y,z; half width x; half depth y.
    vs, fs, uv = [], [], []
    z0, z1 = rings[0][2], rings[-1][2]
    for j, (cx, cy, z, rx, ry) in enumerate(rings):
        for i in range(n):
            theta = -math.pi + math.tau * i/n
            point = (cx + rx*math.sin(theta), cy-ry*math.cos(theta), z)
            vs.append(adjust(j, i, theta, point) if adjust else point)
    # Use physical centre-line length rather than equal spacing between rings.
    length = [0.0]
    for j in range(1, len(rings)):
        length.append(length[-1] + (Vector(rings[j][:3])-Vector(rings[j-1][:3])).length)
    length = [v / length[-1] for v in length]
    for j in range(len(rings)-1):
        for i in range(n):
            if skip and skip(j, i):
                continue
            k = (i+1) % n
            fs.append((j*n+i, j*n+k, (j+1)*n+k, (j+1)*n+i))
            uv.append([(i/n,length[j]),((i+1)/n,length[j]),((i+1)/n,length[j+1]),(i/n,length[j+1])])
    for j, enabled, rev, v in [(0, cap_bottom, True, 0), (len(rings)-1, cap_top, False, 1)]:
        if enabled:
            ids = list(range(j*n,(j+1)*n))
            if rev:
                ids.reverse()
            fs.append(ids)
            uv.append([(.5 + .025*math.sin(math.tau*(i%n)/n), max(.002,min(.998,v + .002*math.cos(math.tau*(i%n)/n)))) for i in ids])
    return mesh(name, vs, fs, uv, uv_key, smooth, category)

# Natural approximately 7.2-head silhouette. Crown 1.650 m; sole Z=0.
def face_shape(j, i, t, p):
    x, y, z = p
    # Broad cheek / extremely shallow central facial plane, no eyes/mouth geometry.
    y -= .007 * max(0, math.cos(t))**10 * math.exp(-((z-1.509)/.030)**2)
    return (x, y, z)

loft('BODY_Head_faceless_volume', [
    (0,-.018,1.419,.035,.037), (0,-.009,1.432,.048,.052),
    (0,0,1.465,.064,.067), (0,.004,1.504,.073,.078),
    (0,.008,1.550,.073,.081), (0,.012,1.589,.065,.073),
    (0,.014,1.620,.041,.050), (0,.014,1.632,.009,.013),
], 20, 'head', adjust=face_shape)
loft('BODY_Neck', [(0,.012,1.336,.043,.040),(0,.012,1.384,.039,.038),(0,.008,1.444,.041,.040)],12,'neck')
loft('BODY_Torso_under_garment', [
    (0,.017,.814,.117,.076),(0,.023,.91,.161,.094),(0,.013,1.03,.127,.075),
    (0,.008,1.15,.144,.085),(0,.012,1.26,.158,.09),(0,.014,1.322,.165,.067),
    (0,.013,1.356,.076,.048),
],16,'torso')

for sign, side in [(-1,'L'),(1,'R')]:
    loft('BODY_Arm_'+side, [
        (sign*.274,-.005,.824,.027,.025),(sign*.267,-.002,.900,.031,.030),
        (sign*.248,.008,1.038,.043,.041),(sign*.234,.020,1.08,.040,.039),
        (sign*.204,.013,1.237,.051,.052),(sign*.177,.010,1.328,.052,.053),
    ],10,'arm')
    # Hands: joined fingers represented as a quiet tapered palm, thumb silhouette included.
    def hand_shape(j, i, t, p, s=sign):
        x,y,z=p
        if j in (2,3) and ((s<0 and math.sin(t)>.6) or (s>0 and math.sin(t)<-.6)):
            x-=s*.012
            y-=.011
        return x,y,z
    loft('BODY_Hand_'+side+'_simplified', [
        (sign*.283,-.016,.689,.012,.013),(sign*.283,-.018,.704,.027,.020),
        (sign*.280,-.013,.754,.032,.022),(sign*.277,-.008,.790,.031,.021),
        (sign*.274,-.005,.834,.024,.022),
    ],12,'hand',adjust=hand_shape)
    loft('BODY_Leg_'+side, [
        (sign*.075,.013,.065,.031,.033),(sign*.075,.018,.17,.034,.035),
        (sign*.077,.027,.315,.050,.055),(sign*.079,-.004,.455,.043,.048),
        (sign*.081,.006,.502,.046,.049),(sign*.084,.019,.67,.069,.068),
        (sign*.085,.019,.841,.078,.078),(sign*.079,.019,.90,.070,.069),
    ],12,'leg')
    # Foot rings along height. Low toe box and distinct arch/heel, no individual toes needed.
    loft('BODY_Foot_'+side+'_bare', [
        (sign*.075,-.056,.000,.038,.109),(sign*.075,-.056,.020,.043,.111),
        (sign*.075,-.050,.045,.042,.104),(sign*.075,-.017,.071,.035,.066),
        (sign*.075,.009,.102,.030,.038),(sign*.075,.014,.127,.030,.031),
    ],12,'foot')

# Clothing is an independent shell; long body, sleeves and neck binding are separate.
gown_rings=[
    (0,.018,.105,.212,.126),(0,.018,.128,.212,.126),
    (0,.018,.37,.207,.124),(0,.018,.60,.199,.120),
    (0,.017,.80,.185,.111),(0,.017,.94,.180,.106),
    (0,.011,1.043,.160,.094),(0,.006,1.14,.160,.096),
    (0,.011,1.24,.178,.099),(0,.012,1.307,.185,.088),
    (0,.012,1.347,.173,.069),(0,.012,1.374,.063,.052),
]
def garment_shape(j,i,t,p):
    x,y,z=p
    # Shallow, designed folds vary around the hem, not a rotationally perfect cone.
    strength=max(0,1-(z-.145)/.83)
    ripple=.0065*strength*math.cos(7*t+.45)
    x+=ripple*math.sin(t)
    y-=ripple*math.cos(t)
    if j<=1:
        z+=.005*(.5+.5*math.cos(5*t+.4))
    # Gentle scoop at the front neck, less drop at the nape.
    if j==11:
        z-=.035*max(0,math.cos(t))**2
    return x,y,z
def armholes(j,i):
    return False
gown=loft('CLOTH_Long_gown_open_hem',gown_rings,24,'gown',False,False,garment_shape,armholes,category='clothing')
solid=gown.modifiers.new('Editable_3mm_cloth_thickness','SOLIDIFY')
solid.thickness=.003
solid.offset=-1
solid.use_even_offset=True
for sign,side in [(-1,'L'),(1,'R')]:
    sleeve=loft('CLOTH_Sleeve_'+side+'_open_cuff',[
        (sign*.273,-.005,.825,.039,.035),(sign*.272,-.004,.855,.040,.036),
        (sign*.267,0,.920,.044,.040),(sign*.245,.007,1.04,.051,.047),
        (sign*.232,.015,1.09,.052,.049),(sign*.209,.016,1.222,.063,.059),
        (sign*.179,.012,1.309,.076,.067),(sign*.157,.012,1.338,.060,.058),
    ],12,'sleeve_'+side,False,False,category='clothing')
    mod=sleeve.modifiers.new('Editable_3mm_cloth_thickness','SOLIDIFY')
    mod.thickness=.003
    mod.offset=-1
collar=loft('CLOTH_Neck_binding',[(0,.012,1.370,.063,.053),(0,.012,1.384,.059,.049)],24,'collar',False,False,
    lambda j,i,t,p:(p[0],p[1],p[2]-.035*max(0,math.cos(t))**2),category='clothing')

# Hair crown follows the skull; it is a solid silhouette piece separate from the curtain.
verts=[]
n=24
ts=[0,.13,.28,.45,.65,.83,1]
# Explicit outer skull profile, sampled at each actual height. A hemisphere
# parameterized by a varying hairline had incorrectly exposed the scalp.
cap_profile=[(1.47,.077,.087),(1.51,.083,.096),(1.55,.085,.098),
             (1.59,.079,.089),(1.62,.058,.068),(1.633,.043,.051),
             (1.643,.028,.033),(1.65,.004,.004)]
def cap_radius(z):
    for a,b in zip(cap_profile,cap_profile[1:]):
        if a[0]<=z<=b[0]:
            f=(z-a[0])/(b[0]-a[0])
            return a[1]+(b[1]-a[1])*f,a[2]+(b[2]-a[2])*f
    return cap_profile[-1][1:]
for t in ts:
    for i in range(n):
        a=-math.pi+math.tau*i/n
        front=max(0,math.cos(a))
        bottom=1.485+.087*front**1.8+.026*(1-abs(math.cos(a)))
        z=1.650-t*(1.650-bottom)
        rx,ry=cap_radius(z)
        verts.append((rx*math.sin(a),.013-ry*math.cos(a),z))
faces=[]; uvs=[]
for j in range(len(ts)-1):
    for i in range(n):
        k=(i+1)%n
        faces.append((j*n+i,j*n+k,(j+1)*n+k,(j+1)*n+i))
        uvs.append([(i/n,1-ts[j]),((i+1)/n,1-ts[j]),((i+1)/n,1-ts[j+1]),(i/n,1-ts[j+1])])
faces.append(tuple(reversed(range(n))))
uvs.append([(.5,.995)]*n)
mesh('HAIR_Crown',verts,faces,uvs,'cap',True,'hair')

def ribbon(name,rows,n,uv_key,category='hair'):
    """Closed-volume lock/curtain: row(cx,cy,z,halfwidth,depth,arch).
    Flat width follows X; fore/aft curvature arch follows its own surface.
    """
    vs=[]
    for surface in range(2):
        for j,(cx,cy,z,w,d,arch) in enumerate(rows):
            for i in range(n+1):
                t=-1+2*i/n
                zz=z
                if j==0:
                    zz += .009*math.cos(i*2.1)+.028*abs(t)
                yy=cy+arch*(1-t*t)+(d/2 if surface else -d/2)
                vs.append((cx+w*t,yy,zz))
    count=len(rows)*(n+1)
    fs=[]; uv=[]
    lengths=[0]
    for a,b in zip(rows,rows[1:]):
        lengths.append(lengths[-1]+(Vector(a[:3])-Vector(b[:3])).length)
    lengths=[v/lengths[-1] for v in lengths]
    for side in range(2):
        off=side*count
        for j in range(len(rows)-1):
            for i in range(n):
                fs.append((off+j*(n+1)+i,off+j*(n+1)+i+1,off+(j+1)*(n+1)+i+1,off+(j+1)*(n+1)+i))
                uv.append([(i/n,lengths[j]),((i+1)/n,lengths[j]),((i+1)/n,lengths[j+1]),(i/n,lengths[j+1])])
    for i in (0,n):
        for j in range(len(rows)-1):
            a=j*(n+1)+i;b=(j+1)*(n+1)+i
            fs.append((a,b,b+count,a+count));uv.append([(i/n,lengths[j]),(i/n,lengths[j+1]),(i/n,lengths[j+1]),(i/n,lengths[j])])
    for j in (0,len(rows)-1):
        for i in range(n):
            a=j*(n+1)+i
            fs.append((a,a+1,a+1+count,a+count));uv.append([(i/n,lengths[j]),((i+1)/n,lengths[j]),((i+1)/n,lengths[j]),(i/n,lengths[j])])
    return mesh(name,vs,fs,uv,uv_key,True,category)

ribbon('HAIR_Back_long_mass',[
    (-.012,.112,.939,.061,.012,.014),(-.006,.119,1.002,.103,.025,.023),
    (-.004,.115,1.13,.119,.032,.030),(0,.086,1.275,.115,.033,.047),
    (0,.053,1.395,.090,.027,.047),(0,.066,1.515,.073,.021,.037),
    (0,.066,1.586,.049,.018,.029),
],12,'back')
for sign,side in [(-1,'L'),(1,'R')]:
    ribbon('HAIR_Side_lock_'+side,[
        (sign*.100,.012,1.231 if sign<0 else 1.268,.007,.010,.001),
        (sign*.107,.004,1.290 if sign<0 else 1.315,.017,.016,.003),
        (sign*.098,-.008,1.37,.022,.018,.004),
        (sign*.083,-.031,1.47,.024,.020,.006),
        (sign*.078,-.042,1.535,.022,.017,.002),
        (sign*.060,-.051,1.59,.022,.014,.002),
    ],4,'lock_'+side)
# Four broad fringe sections in one independent mesh, joined only as an object for editing.
fringe_parts=[]
for idx,(cx,width,bottom,lean) in enumerate([(-.055,.020,1.546,-.008),(-.024,.023,1.569,.004),(.013,.024,1.559,-.006),(.050,.022,1.550,-.008)]):
    obj=ribbon('HAIR_Fringe_piece_'+str(idx+1),[
        (cx+lean,-.084,bottom,.006,.010,0),
        (cx+lean*.6,-.086,bottom+.023,width*.84,.012,.003),
        (cx,-.078,1.598,width,.014,.003),
        (cx*.80,-.053,1.624,width*.77,.010,.001),
    ],4,'fringe')
    fringe_parts.append(obj)

# Review stage and cameras are outside the asset collection/export.
def plain(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    s=m.node_tree.nodes.get('Principled BSDF');s.inputs['Base Color'].default_value=(*color,1)
    s.inputs['Roughness'].default_value=1;s.inputs['Specular IOR Level'].default_value=0
    return m

def camera(scene,name,loc,target,scale):
    d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=scale;d.lens=50
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o)
    o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    scene.camera=o
    return o

def light(scene,name,loc,power,size,target=(0,0,.8)):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()

def ground(scene):
    d=bpy.data.meshes.new('Review_floor_only')
    d.from_pydata([(-200,-200,-.004),(200,-200,-.004),(200,200,-.004),(-200,200,-.004)],[],[(0,1,2,3)])
    o=bpy.data.objects.new('REVIEW_ONLY_ground',d);scene.collection.objects.link(o)
    d.materials.append(plain('REVIEW_ONLY_matte_ground',(.105,.143,.160)))

def stage(scene,w,h):
    configure(scene,w,h);ground(scene)
    light(scene,'Review_key',(-3,-4,6),480,5)
    light(scene,'Review_fill',(3,-1,3),130,4)
    light(scene,'Review_rim',(1,3,4),260,3)

stage(SCENE,1000,1200)
camera(SCENE,'Camera_Hero_3quarter',(3,-6,2.70),(0,0,.845),2.04)
SCENE['asset_status']='FIRST STATIC CANDIDATE / user review required'
SCENE['height_m']=1.65
SCENE['user_direction']='Natural proportions; long dark hair; long pale gown; bare feet; featureless face with volume; separate editable components.'

def instance(scene,name,location,rotation=0):
    o=bpy.data.objects.new(name,None);o.instance_type='COLLECTION';o.instance_collection=ASSET
    scene.collection.objects.link(o);o.location=location;o.rotation_euler.z=rotation
    return o

turn=bpy.data.scenes.new('02_Front_Side_Back')
stage(turn,1680,1000)
instance(turn,'View_FRONT',(-.9,0,0))
instance(turn,'View_SIDE',(0,0,0),math.pi/2)
instance(turn,'View_BACK',(.9,0,0),math.pi)
camera(turn,'Camera_Orthographic_Turnaround',(0,-8,.92),(0,0,.86),3.30)

# Append only existing local Room 1 art into a separate review scene, never edit its source.
env=ROOT.parents[3]/'docs'/'art'/'experiments'/'room1_lowpoly_v2'/'room1_lowpoly_sample_v2.blend'
fit=None
if env.exists():
    fit=bpy.data.scenes.new('03_Room1_Scale_and_Material_Fit')
    configure(fit,1600,1000)
    with bpy.data.libraries.load(str(env),link=False) as (source,target):
        target.collections=[n for n in source.collections if n.startswith(('01_ART_FLOOR','02_ART_WALL','03_ENGINEERING'))]
    for c in target.collections:
        fit.collection.children.link(c)
    instance(fit,'Player_165cm_material_fit',(3.14,6.72,0),math.radians(16))
    camera(fit,'Camera_Room1_existing_candidate',(6.95,-1.5,6.5),(2.45,7.5,1.35),6.2)
    light(fit,'Room_key',(0,3,8),650,5,(2,7.5,1))
    light(fit,'Room_fill',(6,4,5),250,4,(2,7.5,1))
    fit['scope']='Existing Room1 v2 art appended for scale/material review. Original environment source not modified.'

# Export independently editable meshes + external atlas files (no stage / no armature).
bpy.context.window.scene=SCENE
bpy.ops.object.select_all(action='DESELECT')
for obj in PARTS:
    obj.select_set(True)
    obj.data.materials[0]=EXPORT_MATS[obj['texture_family']]
bpy.context.view_layer.objects.active=PARTS[0]
bpy.ops.export_scene.gltf(filepath=str(ROOT/'player_lowpoly_v1.glb'),export_format='GLB',use_selection=True,
    use_active_scene=True,collection=ASSET.name,export_apply=True,export_animations=False,export_cameras=False,export_lights=False,export_yup=True)
for obj in PARTS:
    obj.data.materials[0]=REVIEW_MATS[obj['texture_family']]
    obj.select_set(False)
bpy.context.view_layer.objects.active=None

# Real UV wire guides; each part can be repainted against its existing UV.
for kind,img in IMAGES.items():
    w,h=img.size
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w*4}" height="{h*4}" viewBox="0 0 {w} {h}">',f'<rect width="{w}" height="{h}" fill="#313c49"/>']
    for obj in PARTS:
        if obj['texture_family']!=kind:continue
        uv=obj.data.uv_layers.active
        for face in obj.data.polygons:
            pts=' '.join(f'{uv.data[i].uv.x*w:.3f},{(1-uv.data[i].uv.y)*h:.3f}' for i in face.loop_indices)
            svg.append(f'<polygon points="{pts}" fill="none" stroke="#dae9da" stroke-width=".13"/>')
    svg.append('</svg>')
    (ROOT/'uv_guides'/f'{kind}_actual_uv.svg').write_text('\n'.join(svg),encoding='utf-8')

for image in bpy.data.images:
    if image.source=='FILE':
        image.pack()
        if image in IMAGES.values():
            image.filepath='//textures/'+Path(image.filepath).name

manifest=[]
for obj in PARTS:
    obj.data.calc_loop_triangles()
    manifest.append({'name':obj.name,'category':obj['category'],'vertices':len(obj.data.vertices),
        'base_triangles':len(obj.data.loop_triangles),'texture':obj['texture_family'],'uv_region':obj['uv_region'],
        'uv_pixels':list(obj['uv_pixels']),'modifiers':[m.type for m in obj.modifiers]})
(ROOT/'asset_manifest.json').write_text(json.dumps({
    'status':'STATIC_CANDIDATE_NOT_APPROVED','blender_version':bpy.app.version_string,'height_m':1.65,
    'orientation':'+Z up; front -Y; ground at 0','parts':manifest,
    'texture_dimensions':{k:list(i.size) for k,i in IMAGES.items()},
    'triangles_before_cloth_thickness':sum(p['base_triangles'] for p in manifest),
    'render_method':'Native Blender EEVEE, full-resolution geometry edges, nearest surface textures; no AI image or postpaint',
    'limits':['no skeleton/weights/animation','no Godot import/runtime test','hair and cloth deformation not verified',
        'GLB contains portable rough diffuse baseline, not Blender-only stepped-light nodes'],
},indent=2),encoding='utf-8')

SCENE.camera=bpy.data.objects['Camera_Hero_3quarter']
SCENE.render.filepath='//evidence/A_character_hero.png'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'player_lowpoly_v1.blend'))

if '--skip-render' not in sys.argv:
    for scene,filename in [(SCENE,'A_character_hero.png'),(turn,'B_front_side_back.png'),(fit,'C_room1_fit.png')]:
        if scene is None:continue
        bpy.context.window.scene=scene
        scene.render.filepath=str(ROOT/'evidence'/filename)
        bpy.ops.render.render(write_still=True)
    bpy.context.window.scene=SCENE
print(json.dumps({'result':'BUILT','parts':len(PARTS),'base_triangles':sum(p['base_triangles'] for p in manifest),'room_fit':fit is not None}))
