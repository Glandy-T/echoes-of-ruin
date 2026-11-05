"""Local Blender repair of the legitimately downloaded H2.5 gray model.
The source GLB stays untouched. No cloud calls and no painted textures.
"""
from pathlib import Path
import bpy,bmesh,math,json,hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree

EXP=Path(__file__).resolve().parents[1]
RAW=EXP.parent/'protagonist_tripo_h25_v1/model/protagonist_tripo_h25_v1_raw.glb'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(RAW))
raw=next(o for o in bpy.context.scene.objects if o.type=='MESH')
bpy.context.view_layer.objects.active=raw;raw.select_set(True)
bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
raw.name='REFERENCE_H25_UNMODIFIED'
reference=bpy.data.collections.new('00_ORIGINAL_REFERENCE');bpy.context.scene.collection.children.link(reference)
for c in list(raw.users_collection):c.objects.unlink(raw)
reference.objects.link(raw)
edited=bpy.data.collections.new('01_LOCAL_CLEANUP_CANDIDATE');bpy.context.scene.collection.children.link(edited)
base=raw.copy();base.data=raw.data.copy();base.name='Working_Base';edited.objects.link(base)
bm=bmesh.new();bm.from_mesh(base.data)
unseen=set(bm.verts);components=[]
while unseen:
 seed=unseen.pop();stack=[seed];group={seed}
 while stack:
  v=stack.pop()
  for e in v.link_edges:
   w=e.other_vert(v)
   if w in unseen:unseen.remove(w);group.add(w);stack.append(w)
 components.append(group)
main=max(components,key=len)
bmesh.ops.delete(bm,geom=[v for group in components if group is not main for v in group],context='VERTS')
bm.to_mesh(base.data);bm.free()
removed_fragments=sum(len(g) for g in components if g is not main)

# Explicit face surgery is used instead of Boolean inside/outside classification:
# the source has non-manifold vertex connections despite zero boundary edges.
bm=bmesh.new();bm.from_mesh(base.data)
for co,no in [((0,-.018,0),(0,1,0)),((0,.025,0),(0,1,0)),((0,.06,0),(0,1,0)),((0,0,.66),(0,0,1)),((0,0,.795),(0,0,1)),((0,0,.835),(0,0,1)),((0,0,1.015),(0,0,1)),((-.105,0,0),(1,0,0)),((.105,0,0),(1,0,0)),((-.14,0,0),(1,0,0)),((.14,0,0),(1,0,0))]:
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=co,plane_no=no,dist=1e-7)
def damaged_region(p):
 return p.z>.835+1e-7 or (p.z>.795+1e-7 and p.y>-.018+1e-7 and abs(p.x)<.14-1e-7) or (.66+1e-7<p.z<1.015 and p.y>.025+1e-7 and abs(p.x)<.14-1e-7)
bad=[f for f in bm.faces if damaged_region(f.calc_center_median())]
bmesh.ops.delete(bm,geom=bad,context='FACES')
boundary=[e for e in bm.edges if e.is_boundary]
filled=bmesh.ops.holes_fill(bm,edges=boundary,sides=0)['faces']
# Add support to new hidden back caps while retaining the exact source border.
if filled:
 tris=bmesh.ops.triangulate(bm,faces=filled)['faces']
 poke=bmesh.ops.poke(bm,faces=tris,offset=0,use_relative_offset=False,center_mode='MEAN_WEIGHTED')
bm.to_mesh(base.data);bm.free();base.data.update()

# Slice along real body/garment boundaries for independently editable parts.
bm=bmesh.new();bm.from_mesh(base.data)
planes=[((0,0,.835),(0,0,1)),((0,0,.165),(0,0,1))]
for sign in [-1,1]:
 planes.extend([((sign*.16,0,0),(1,0,0)),((sign*.20,0,.518),(sign*.3,0,-1))])
for co,no in planes:
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=co,plane_no=no,dist=1e-7)
bm.to_mesh(base.data);bm.free();base.data.update()
group_faces={'Gown_Continuous':[],'Head_and_FrontHair_Source':[],'Hands_Source':[],'Feet_Source':[]}
for f in base.data.polygons:
 p=f.center;x,y,z=p
 if z>.835:group='Head_and_FrontHair_Source'
 elif z<.165:group='Feet_Source'
 elif abs(x)>.16 and z<.518+.3*(abs(x)-.20):group='Hands_Source'
 else:group='Gown_Continuous'
 group_faces[group].append(f)
parts=[]
for name,faces in group_faces.items():
 if name=='Head_and_FrontHair_Source' or not faces:continue
 ids=sorted({v for f in faces for v in f.vertices});mapping={v:i for i,v in enumerate(ids)}
 mesh=bpy.data.meshes.new(name);mesh.from_pydata([base.data.vertices[i].co for i in ids],[],[[mapping[i] for i in f.vertices] for f in faces]);mesh.update()
 obj=bpy.data.objects.new(name,mesh);edited.objects.link(obj);parts.append(obj)
 bm=bmesh.new();bm.from_mesh(mesh)
 edges=[e for e in bm.edges if e.is_boundary]
 if edges:bmesh.ops.holes_fill(bm,edges=edges,sides=0)
 bm.to_mesh(mesh);bm.free()
bpy.data.objects.remove(base,do_unlink=True)

def make_mesh(name,vertices,faces):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
 obj=bpy.data.objects.new(name,mesh);edited.objects.link(obj);parts.append(obj)
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
 return obj

# The clean head is an intentionally low-information human volume. A tiny nasal
# projection retains orientation without eyes, expression or portrait detail.
head_rows=[(.852,.014,.018,-.013),(.867,.032,.028,-.012),(.888,.047,.036,-.012),(.915,.055,.044,-.011),(.943,.058,.045,-.008),(.966,.05,.04,-.004),(.985,.035,.028,0),(.996,.013,.012,0)]
hn=24;hv=[];hf=[]
for z,rx,ry,cy in head_rows:
 for i in range(hn):
  a=2*math.pi*i/hn;x=rx*math.cos(a);y=cy+ry*math.sin(a)
  if math.sin(a)<-.7:y-=.007*max(0,1-abs(x)/.018)*max(0,1-abs(z-.925)/.025)
  hv.append((x,y,z))
for r in range(len(head_rows)-1):
 for i in range(hn):hf.append((r*hn+i,r*hn+(i+1)%hn,(r+1)*hn+(i+1)%hn,(r+1)*hn+i))
hf.extend([tuple(reversed(range(hn))),tuple((len(head_rows)-1)*hn+i for i in range(hn))])
head=make_mesh('Head_Clean_WeakFeatures',hv,hf)
nv=[];nf=[]
for z,rx,ry in [(.805,.027,.027),(.84,.023,.026),(.874,.024,.025)]:
 for i in range(12):a=2*math.pi*i/12;nv.append((rx*math.cos(a),ry*math.sin(a)-.002,z))
for r in range(2):
 for i in range(12):nf.append((r*12+i,r*12+(i+1)%12,(r+1)*12+(i+1)%12,(r+1)*12+i))
nf.extend([tuple(reversed(range(12))),tuple(24+i for i in range(12))])
neck=make_mesh('Neck_Clean',nv,nf)

# One continuous scalp-to-back mass: no separate crown plate or hair rods.
# The boundary rises toward the temples and opens high across the forehead.
profiles=[(.65,.09,.095,.008),(.72,.107,.10,.006),(.81,.109,.095,.002),(.88,.084,.075,0),(.915,.073,.063,-.001),(.943,.071,.061,-.004),(.966,.06,.052,-.002),(.985,.043,.035,0),(.997,.025,.022,0),(1.003,.012,.01,0),(1.006,0,0,0)]
def profile(z):
 for j in range(len(profiles)-1):
  a,b=profiles[j:j+2]
  if a[0]<=z<=b[0]:
   t=(z-a[0])/(b[0]-a[0]);return tuple(a[k]*(1-t)+b[k]*t for k in range(1,4))
 return profiles[0][1:]
n=32;ts=[i/16 for i in range(1,17)];verts=[];faces=[]
for layer in [0,1]:
 for t in ts:
  for i in range(n):
   a=2*math.pi*i/n;s=math.sin(a);c=math.cos(a)
   bottom=.82-.165*s if s>=0 else .82+.146*((-s)**1.5)
   if s<-.35:bottom+=.015*c
   z=1.006-(1.006-bottom)*t;rx,ry,cy=profile(z)
   inset=(.012 if z>.9 else .028) if layer else 0
   verts.append((max(.001,rx-inset)*c,cy+max(.001,ry-inset)*s,z-(.004 if layer else 0)))
surface=len(ts)*n
for layer in [0,1]:
 for r in range(len(ts)-1):
  for i in range(n):
   a=layer*surface+r*n+i;b=layer*surface+r*n+(i+1)%n
   q=(a,b,b+n,a+n);faces.append(q if not layer else tuple(reversed(q)))
for i in range(n):
 a=(len(ts)-1)*n+i;b=(len(ts)-1)*n+(i+1)%n
 faces.append((a,b,b+surface,a+surface))
for layer in [0,1]:
 top=len(verts);verts.append((0,0,1.006-(.004 if layer else 0)))
 for i in range(n):
  q=(top,layer*surface+(i+1)%n,layer*surface+i)
  faces.append(q if not layer else tuple(reversed(q)))
hair=make_mesh('Hair_Main_Clean',verts,faces)
# A broad side-swept fringe follows the approved side-part direction. It is a
# small closed mass sitting on the scalp, not individual floating hair strands.
path=[(.021,-.03,.984,.013),(.006,-.052,.975,.016),(-.018,-.064,.956,.018),(-.04,-.062,.938,.016),(-.061,-.045,.916,.003)]
fv=[];ff=[]
for layer in [0,1]:
 for k,(x,y,z,w) in enumerate(path):
  prev=Vector((path[max(0,k-1)][0],path[max(0,k-1)][2]));nxt=Vector((path[min(len(path)-1,k+1)][0],path[min(len(path)-1,k+1)][2]))
  direction=(nxt-prev).normalized();normal=Vector((-direction.y,direction.x))
  for sign in [-1,1]:fv.append((x+normal.x*w*sign,y+(.009 if layer else -.001),z+normal.y*w*sign))
sz=len(path)*2
for k in range(len(path)-1):
 a=k*2;ff.extend([(a,a+1,a+3,a+2),(sz+a+2,sz+a+3,sz+a+1,sz+a),(a,a+2,sz+a+2,sz+a),(a+1+sz,a+3+sz,a+3,a+1)])
ff.extend([(0,sz,sz+1,1),(sz-2,sz-1,2*sz-1,2*sz-2)])
fringe=make_mesh('Hair_Fringe_Clean',fv,ff)
for obj in parts:
 mat=bpy.data.materials.new('ID_'+obj.name)
 mat.diffuse_color=(.075,.08,.09,1) if obj.name.startswith('Hair_') else ((.60,.59,.56,1) if obj.name!='Gown_Continuous' else (.72,.74,.70,1))
 obj.data.materials.clear();obj.data.materials.append(mat)
for obj in parts:
 for p in obj.data.polygons:p.use_smooth=True
 obj['review_status']='Local cleanup candidate, not final topology or animation approval'

# Retained triangles from Tripo have intentional custom shading normals. Keep
# those on unchanged surfaces instead of introducing artificial faceting merely
# through object separation; new cut/support surfaces keep their own normals.
raw.data.calc_loop_triangles()
raw_tris=list(raw.data.loop_triangles)
bvh=BVHTree.FromPolygons([v.co for v in raw.data.vertices],[t.vertices for t in raw_tris],all_triangles=True)
corner_normals=[v.vector.copy() for v in raw.data.corner_normals]
for obj in parts:
 if obj.name not in ['Gown_Continuous','Hands_Source','Feet_Source']:continue
 mesh=obj.data;mesh.update();normals=[]
 for p in mesh.polygons:
  near=bvh.find_nearest(p.center);preserve=near[0] is not None and near[3]<1e-5
  for li in p.loop_indices:
   vertex=mesh.vertices[mesh.loops[li].vertex_index]
   if preserve:
    hit,_,idx,dist=bvh.find_nearest(vertex.co)
    t=raw_tris[idx];a,b,c=[raw.data.vertices[i].co for i in t.vertices]
    u=b-a;v=c-a;w=hit-a;uu=u.dot(u);uv=u.dot(v);vv=v.dot(v);wu=w.dot(u);wv=w.dot(v);den=uu*vv-uv*uv
    if abs(den)>1e-18:
     beta=(vv*wu-uv*wv)/den;gamma=(uu*wv-uv*wu)/den;alpha=1-beta-gamma
     nrm=(corner_normals[t.loops[0]]*alpha+corner_normals[t.loops[1]]*beta+corner_normals[t.loops[2]]*gamma).normalized()
    else:nrm=vertex.normal
   else:
    if .60<p.center.z<.835 and p.center.y>.018:
     nrm=Vector((vertex.co.x*2.0,1,.12)).normalized()
    else:nrm=vertex.normal
   normals.append(tuple(nrm))
 mesh.normals_split_custom_set(normals)
obj=next(o for o in parts if o.name=='Hands_Source')
obj['remaining_work']='Fingers remain coarse. No invented detailed hand anatomy or binding claimed.'

scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE'
scene.display.shading.single_color=(.62,.65,.65);scene.display.shading.background_type='WORLD'
scene.world=bpy.data.worlds.new('Review Background');scene.world.color=(.045,.055,.06)
scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH'
scene.display.shading.show_specular_highlight=False
qa=bpy.data.collections.new('QA_CAMERAS_ONLY');scene.collection.children.link(qa)
center=Vector((0,0,.499));height=.998
directions=[('front',(0,-1,0)),('side',(1,0,0)),('back',(0,1,0)),('quarter',(.8,-1,.25)),('back_quarter',(.8,1,.2))]
for name,direction in directions:
 data=bpy.data.cameras.new('QA_'+name);cam=bpy.data.objects.new('QA_'+name,data);qa.objects.link(cam)
 cam.location=center+Vector(direction).normalized()*height*4;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
 data.type='ORTHO';data.ortho_scale=height*1.22*(1280/720);data.clip_end=40
 scene.camera=cam
 for variant in ['before','after']:
  raw.hide_render=variant!='before'
  for o in parts:o.hide_render=variant!='after'
  scene.render.filepath=str(EXP/'evidence'/f'{variant}_{name}.png');bpy.ops.render.render(write_still=True)
 if name in ['front','side','back','quarter']:
  scene.display.shading.color_type='MATERIAL'
  scene.render.filepath=str(EXP/'evidence'/f'part_ids_{name}.png');bpy.ops.render.render(write_still=True)
  scene.display.shading.color_type='SINGLE'
raw.hide_render=True;reference.hide_viewport=True
for o in parts:o.hide_render=False
scene.camera=bpy.data.objects['QA_quarter']
for o in scene.objects:o.select_set(False)
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=hair
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   s=area.spaces.active;s.region_3d.view_location=center;s.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion();s.region_3d.view_distance=1.6;s.region_3d.view_perspective='ORTHO'
   s.overlay.show_floor=False;s.overlay.show_axis_x=False;s.overlay.show_axis_y=False
   s.shading.type='SOLID';s.shading.color_type='MATERIAL';s.shading.single_color=(.62,.65,.65)
bpy.ops.wm.save_as_mainfile(filepath=str(EXP/'model/protagonist_cleanup_v1.blend'))
bpy.ops.export_scene.gltf(filepath=str(EXP/'model/protagonist_cleanup_v1.glb'),export_format='GLB',use_selection=True,export_texcoords=False)
report={'source_sha256':hashlib.sha256(RAW.read_bytes()).hexdigest(),'removed_disconnected_vertices':removed_fragments,'parts':[{'name':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons)} for o in parts],'geometry_modified':True,'UV_unwrapped':False,'cloud_calls':0,'paid_credits_used':0,'silhouette_approval':False,'remaining':['Hands and feet retain coarse source geometry','Gown still contains source triangulation and local support caps','No deformation-topology, UV or animation approval']}
(EXP/'source/build_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('LOCAL_H25_CLEANUP_CANDIDATE_SAVED')
