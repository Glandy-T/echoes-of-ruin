"""Transfer existing linear irradiance to continuous world-plane UV2 charts.

No albedo painting, smoothing, or new illumination: geometry/UV0 are preserved.
Original renderer outputs and original UV source remain versioned alongside result.
"""
from pathlib import Path
import bpy,numpy as np,json,math,hashlib,shutil,runpy
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];EXP=HERE.parent;OUT=ROOT/'assets/art/cryo_4f_complete_v3';N=4096;DENSITY=16
assert not json.loads((OUT/'manifest.json').read_text()).get('continuous_UV2_transfer'), 'Already transferred; rebuild source bake before re-running.'
layout=json.loads((OUT/'layout.json').read_text());old_records=json.loads(json.dumps(layout['receivers']))
shutil.copy2(EXP/'cryo_4f_complete_v3.blend',EXP/'cryo_4f_original_uv.blend')
shutil.copy2(OUT/'cryo_4f_complete_v3.glb',OUT/'source_geometry.glb')
(EXP/'original_uv_records.json').write_text(json.dumps(old_records,indent=2))
for name in ['strip_irradiance.exr','strip_irradiance_denoised.exr']:shutil.copy2(OUT/name,OUT/('source_'+name))
bpy.ops.wm.open_mainfile(filepath=str(EXP/'cryo_4f_complete_v3.blend'))
receivers=[bpy.data.objects[name] for name in old_records]
def state(ob):return {'vertices':[list(v.co) for v in ob.data.vertices],'UV0':[list(v.uv) for v in ob.data.uv_layers['UVMap'].data]}
frozen={o.name:state(o) for o in receivers};groups={}
for ob in receivers:
 points=np.array([v.co[:] for v in ob.data.vertices]);normal=ob.data.polygons[0].normal;fixed=int(np.argmax(np.abs(normal)));axes=[i for i in range(3) if i!=fixed]
 kind=old_records[ob.name]['kind'];key=(kind,fixed,round(float(points[0,fixed]),5),1 if normal[fixed]>0 else -1)
 if kind=='door':key=key+(ob.name,)
 g=groups.setdefault(key,{'objects':[],'axes':axes,'min':np.array([np.inf,np.inf]),'max':np.array([-np.inf,-np.inf])})
 g['objects'].append(ob);g['min']=np.minimum(g['min'],points[:,axes].min(axis=0));g['max']=np.maximum(g['max'],points[:,axes].max(axis=0))
print('CONTINUOUS_GROUPS',len(groups),'rectangle_area',sum((math.ceil((g['max'][0]-g['min'][0])*DENSITY)+16)*(math.ceil((g['max'][1]-g['min'][1])*DENSITY)+16) for g in groups.values()),flush=True)
free=[(0,0,N,N)]
for index,g in enumerate(sorted(groups.values(),key=lambda g:-float(np.prod(g['max']-g['min'])))):
 span=g['max']-g['min'];pw,ph=[max(2,math.ceil(s*DENSITY)) for s in span]
 choices=[]
 for r in free:
  for rotated in [False,True]:
   w,h=(ph+16,pw+16) if rotated else (pw+16,ph+16)
   if w<=r[2] and h<=r[3]:choices.append((min(r[2]-w,r[3]-h),max(r[2]-w,r[3]-h),r,rotated,w,h))
 assert choices,'Continuous atlas overflow'
 _,_,r,rotated,rw,rh=min(choices,key=lambda c:(c[0],c[1]))
 px,py=r[:2];cx,cy=px+8,py+8
 if rotated:
  pw,ph=ph,pw;g['axes']=list(reversed(g['axes']));g['min']=g['min'][::-1];g['max']=g['max'][::-1];span=g['max']-g['min']
 next_free=[]
 for x,y,w,h in free:
  if px>=x+w or px+rw<=x or py>=y+h or py+rh<=y:next_free.append((x,y,w,h));continue
  if x<px:next_free.append((x,y,px-x,h))
  if px+rw<x+w:next_free.append((px+rw,y,x+w-px-rw,h))
  if y<py:next_free.append((x,y,w,py-y))
  if py+rh<y+h:next_free.append((x,py+rh,w,y+h-py-rh))
 free=[]
 for j,a in enumerate(next_free):
  if any(i!=j and b[0]<=a[0] and b[1]<=a[1] and b[0]+b[2]>=a[0]+a[2] and b[1]+b[3]>=a[1]+a[3] and (a!=b or i<j) for i,b in enumerate(next_free)):continue
  free.append(a)
 g.update({'index':index,'rect':[cx,cy,cx+pw,cy+ph],'width':pw,'height':ph})
 for ob in g['objects']:
  values=[]
  for i,vertex in enumerate(ob.data.vertices):
   p=np.array(vertex.co[:])[g['axes']];uv=np.array([cx,cy])+(p-g['min'])/span*np.array([pw,ph]);ob.data.uv_layers['LightmapUV'].data[i].uv=uv/N;values.append(uv)
  a=np.array(values);layout['receivers'][ob.name]['chart']=[float(a[:,0].min()),float(a[:,1].min()),float(a[:,0].max()),float(a[:,1].max())];layout['receivers'][ob.name]['chart_group']=index
audit=runpy.run_path(str(ROOT/'scripts/dev/room1_uv2_audit.py'))['audit_uv2_layout'](receivers)
assert audit['positive_area_overlap_count']==audit['uv_degenerate_triangle_count']==audit['out_of_atlas_vertex_count']==0
# Shared-plane affine coordinates guarantee continuity, including T-junctions at lintels.
edge_points={};shared=0
for g in groups.values():
 for ob in g['objects']:
  for vertex,uv in zip(ob.data.vertices,ob.data.uv_layers['LightmapUV'].data):
   key=(g['index'],tuple(round(v,5) for v in vertex.co));value=np.array(uv.uv[:])
   if key in edge_points:assert np.max(abs(value-edge_points[key]))<1e-6;shared+=1
   edge_points[key]=value
def sample(image,u,v):
 x=np.clip(u,0,N-1);y=np.clip(v,0,N-1);x0=np.floor(x).astype(int);y0=np.floor(y).astype(int);x1=np.minimum(x0+1,N-1);y1=np.minimum(y0+1,N-1);fx=(x-x0)[...,None];fy=(y-y0)[...,None]
 return image[y0,x0,:3]*(1-fx)*(1-fy)+image[y0,x1,:3]*fx*(1-fy)+image[y1,x0,:3]*(1-fx)*fy+image[y1,x1,:3]*fx*fy
sc=bpy.context.scene;sc.render.image_settings.file_format='OPEN_EXR';sc.render.image_settings.color_mode='RGB';sc.render.image_settings.color_depth='16';sc.render.image_settings.exr_codec='ZIP'
for filename in ['strip_irradiance.exr','strip_irradiance_denoised.exr']:
 im=bpy.data.images.load(str(OUT/('source_'+filename)),check_existing=False);pixels=np.empty(N*N*4,dtype=np.float32);im.pixels.foreach_get(pixels);pixels=pixels.reshape(N,N,4)
 result=np.zeros((N,N,4),dtype=np.float32);result[:,:,3]=1
 for g in groups.values():
  x0,y0,x1,y1=g['rect'];w,h=g['width'],g['height'];span=g['max']-g['min'];tile=np.zeros((h+8,w+8,3),dtype=np.float32);valid=np.zeros((h+8,w+8),dtype=bool)
  for ob in g['objects']:
   p=np.array([v.co[:] for v in ob.data.vertices])[:,g['axes']];lo=np.maximum(0,np.floor((p.min(axis=0)-g['min'])/span*[w,h]).astype(int));hi=np.minimum([w,h],np.ceil((p.max(axis=0)-g['min'])/span*[w,h]).astype(int))
   xx,yy=np.meshgrid(g['min'][0]+(np.arange(lo[0],hi[0])+.5)*span[0]/w,g['min'][1]+(np.arange(lo[1],hi[1])+.5)*span[1]/h)
   e1=p[1]-p[0];e2=p[3]-p[0];dx=xx-p[0,0];dy=yy-p[0,1];u=(dx*e1[0]+dy*e1[1])/np.dot(e1,e1);v=(dx*e2[0]+dy*e2[1])/np.dot(e2,e2);mask=(u>=-1e-5)&(u<=1+1e-5)&(v>=-1e-5)&(v<=1+1e-5)
   a,b,c,d=old_records[ob.name]['chart'];values=sample(pixels,a+u*(c-a)-.5,b+v*(d-b)-.5)
   sl=(slice(lo[1]+4,hi[1]+4),slice(lo[0]+4,hi[0]+4));tile[sl][mask]=values[mask];valid[sl]|=mask
  # Technical expansion only, matching bake margin. No cross-chart averaging.
  for iteration in range(4):
   updated=tile.copy();new_valid=valid.copy()
   for dy,dx in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
    neighbor=np.roll(valid,(dy,dx),(0,1));pick=neighbor&~new_valid;shifted=np.roll(tile,(dy,dx),(0,1));updated[pick]=shifted[pick];new_valid|=pick
   tile=updated;valid=new_valid
  result[y0-4:y1+4,x0-4:x1+4,:3]=tile
 out=bpy.data.images.new('Continuous_'+filename,width=N,height=N,alpha=False,float_buffer=True);out.colorspace_settings.name='Non-Color';out.pixels.foreach_set(result.ravel());out.save_render(str(OUT/filename),scene=sc)
 bpy.data.images.remove(out);bpy.data.images.remove(im);del pixels,result
 print('CONTINUOUS_TRANSFER',filename,flush=True)
for ob in receivers:assert state(ob)==frozen[ob.name]
bpy.ops.object.select_all(action='DESELECT')
for ob in bpy.data.objects:
 if ob in receivers or ob.get('kind') in ['shell','locked_door']:ob.select_set(True)
bpy.context.view_layer.objects.active=receivers[0];bpy.ops.export_scene.gltf(filepath=str(OUT/'cryo_4f_complete_v3.glb'),export_format='GLB',use_selection=True,export_extras=True)
bpy.ops.file.make_paths_relative();bpy.ops.wm.save_as_mainfile(filepath=str(EXP/'cryo_4f_complete_v3.blend'),compress=True)
(OUT/'layout.json').write_text(json.dumps(layout,indent=2));audit.update({'continuous_plane_groups':len(groups),'shared_vertices_verified':shared,'geometry_UV0_unchanged':True,'atlas':N,'lightmap_density':DENSITY,'technical_transfer':'bilinear world-plane UV2 transfer, non-denoised remains non-denoised; original Cycles outputs retained as source_*.exr','margin':4,'chart_gap':16,'group_rectangles':[g['rect'] for g in groups.values()]});(EXP/'continuous_uv_validation.json').write_text(json.dumps(audit,indent=2))
m=json.loads((OUT/'manifest.json').read_text());m['continuous_UV2_transfer']=True;m['source_raw_preserved']=True;m['shared_plane_groups']=len(groups);m['files']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.suffix in ['.glb','.exr','.json'] and p.name!='manifest.json'};(OUT/'manifest.json').write_text(json.dumps(m,indent=2));print('CONTINUOUS_ATLAS_PASS',len(groups),'groups',shared,'shared vertices',flush=True)
