"""Blender 5.0: independent production-pack candidates, metres, Z-up, -Y front.

Export convention is glTF/Godot X-right, Y-up, +Z-front. All texture coordinates
are physical lengths divided by native texture dimensions at 80 texels/m, except
trim islands narrower than one texel. Door fronts share one exact W/H projection.
"""
from pathlib import Path
import json, math, sys
from mathutils import Vector
import bpy

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[4]; OUT=ROOT/'assets/art/cryo_building_review_v1/models'
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version=0
PX=80
SIZE={'M01':(728,232),'M02':(256,192),'M03':(192,256),'M04':(256,64),'M05-L':(256,256),'M05-D':(256,256),'M06':(256,256),'M07':(256,256),'M08':(4,184),'M09':(256,5),'M10':(192,16)}
COLORS={'M01':'d3d6c9','M02':'5a6c73','M03':'7c8380','M04':'737f81','M05-L':'a7b0aa','M05-D':'4d6065','M06':'b9bdb2','M07':'71858a','M08':'263b3e','M09':'8f9d99','M10':'4e5b5b'}
SIZE.update({'M01_STAIR':(256,256),'M03_STAIR':(256,256)})
COLORS.update({'M01_STAIR':'b9bdb2','M03_STAIR':'7c8380'})
def srgb(c): return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
def mat(n,c):
    m=bpy.data.materials.new(n);m.use_nodes=True; rgb=tuple(srgb(int(c[i:i+2],16)/255) for i in (0,2,4));m.diffuse_color=(*rgb,1)
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*rgb,1);bs.inputs['Roughness'].default_value=.88
    return m
M={n:mat(n,c) for n,c in COLORS.items()}
def group(n):
    c=bpy.data.collections.new(n);bpy.context.scene.collection.children.link(c);return c

def mesh(c,n,v,f,materials,face_ids=None,face_uv=None,properties=None):
    v=[Vector(p) for p in v]; data=bpy.data.meshes.new(n); data.from_pydata(v,[],f); data.update()
    for m in materials:data.materials.append(M[m])
    uv=data.uv_layers.new(name='UV0_80px_m')
    for poly in data.polygons:
        mi=face_ids.get(poly.index,0) if face_ids else 0;poly.material_index=mi
        name=materials[mi]; w,h=SIZE[name]; pts=[v[i] for i in poly.vertices]
        major=max(range(3),key=lambda i:abs(poly.normal[i])); u,vaxis={0:(1,2),1:(0,2),2:(0,1)}[major]
        origin_u=min(q[u] for q in pts); origin_v=min(q[vaxis] for q in pts)
        for i,li in enumerate(poly.loop_indices):
            q=pts[i]
            if face_uv and poly.index in face_uv: uv.data[li].uv=face_uv[poly.index](q)
            else: uv.data[li].uv=((q[u]-origin_u)*PX/w,(q[vaxis]-origin_v)*PX/h)
    obj=bpy.data.objects.new(n,data);c.objects.link(obj)
    for k,val in (properties or {}).items(): obj[k]=val
    return obj

def box(c,n,b,m,**kw):
    x,X,y,Y,z,Z=b
    return mesh(c,n,[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],[m],**kw)

def prism_xz(c,n,profile,y,Y,material,side_origin=None,**kw):
    # CCW profile in X/Z means the near end faces -Y.
    twice=sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(profile,profile[1:]+profile[:1]))
    if twice<0:profile=profile[::-1]
    N=len(profile);v=[(x,d,z) for d in (y,Y) for x,z in profile]
    faces=[tuple(range(N)),tuple(reversed(range(N,2*N)))]+[((i+1)%N,i,i+N,(i+1)%N+N) for i in range(N)]
    # Per-side run/cross dimensions avoid compressing pixels on sloped soffits.
    maps={}
    w,h=SIZE[material]
    for i,(a,b) in enumerate(zip(profile,profile[1:]+profile[:1])):
        p=Vector((a[0],0,a[1])); axis=(Vector((b[0],0,b[1]))-p).normalized()
        u0,v0=side_origin(a,b) if side_origin else (0,0)
        maps[i+2]=(lambda q,p=p,axis=axis,u0=u0,v0=v0:(((q-p).dot(axis)*PX+u0)/w,((q.y-y)*PX+v0)/h))
    return mesh(c,n,v,faces,[material],face_uv=maps,**kw)

def tube(c,n,points,rx=.021,rz=None):
    rz=rx if rz is None else rz; sides=12;v=[]; lengths=[0.]
    P=[Vector(p) for p in points]
    for a,b in zip(P,P[1:]):lengths.append(lengths[-1]+(b-a).length)
    for i,p in enumerate(P):
        tangent=(P[min(i+1,len(P)-1)]-P[max(i-1,0)]).normalized()
        ref=Vector((0,0,1)) if abs(tangent.z)<.95 else Vector((0,1,0))
        u=tangent.cross(ref).normalized();w=tangent.cross(u).normalized()
        for j in range(sides):
            a=2*math.pi*j/sides;v.append(p+u*(rx*math.cos(a))+w*(rz*math.sin(a)))
    faces=[]; native=SIZE['M04']; perimeter=[0.]
    for j in range(sides):perimeter.append(perimeter[-1]+(v[(j+1)%sides]-v[j]).length)
    for i in range(len(P)-1):
        for j in range(sides):
            k=(j+1)%sides;faces.append((i*sides+j,i*sides+k,(i+1)*sides+k,(i+1)*sides+j))
    faces += [tuple(reversed(range(sides))),tuple(range((len(P)-1)*sides,len(P)*sides))]
    o=mesh(c,n,v,faces,['M04']); uv=o.data.uv_layers.active
    for poly in o.data.polygons[:-2]:
        i,j=divmod(poly.index,sides); r0=perimeter[j]*PX/native[1]; r1=perimeter[j+1]*PX/native[1]; u0=lengths[i]*PX/native[0];u1=lengths[i+1]*PX/native[0]
        for li,pair in zip(poly.loop_indices,[(u0,r0),(u0,r1),(u1,r1),(u1,r0)]):uv.data[li].uv=pair
    return o

def smooth_corners(p,r=.12):
    p=[Vector(q) for q in p];out=[p[0]]
    for a,b,c in zip(p,p[1:],p[2:]):
        left=(a-b).normalized();right=(c-b).normalized(); d=min(r,(a-b).length*.4,(c-b).length*.4)
        x=b+left*d;y=b+right*d
        for j in range(5):t=j/4;out.append((1-t)**2*x+2*(1-t)*t*b+t*t*y)
    out.append(p[-1]);return out

def export(c,n):
    bpy.ops.object.select_all(action='DESELECT')
    for o in c.all_objects:o.select_set(True)
    bpy.context.view_layer.objects.active=next(o for o in c.all_objects if o.type=='MESH')
    bpy.ops.export_scene.gltf(filepath=str(OUT/(n+'.glb')),export_format='GLB',use_selection=True,export_texcoords=True,export_extras=True)

RISE=1.9/12; X0=-1.65; X1=1.65
c=group('ST-01')
def stair_wall_foot(name,x,X,y,z,facing):
    # Use the authored lower protection strip only where the deck meets the wall.
    # One band is five native pixels high. The rest of the wall uses fine mineral grain.
    ya,yb=sorted((y,y+.004*facing))
    width,height=SIZE['M01']
    def foot_uv(q):
        return ((q.x+3.45)*PX/width,1-(224-(q.z-z)*PX)/height)
    def top_uv(q):
        return ((q.x+3.45)*PX/width,1-(219+abs(q.y-y)*PX)/height)
    wall_face=4 if facing==1 else 2
    return box(c,name,(x,X,ya,yb,z,z+5/PX),'M01',face_uv={wall_face:foot_uv,1:top_uv})

def flight(name,y,Y,z0,direction):
    x0,x1=(X0,X1) if direction==1 else (X1,X0)
    p=[(x0,z0-.22),(x0,z0)]
    for i in range(11):
        x=x0+i*.3*direction; Z=z0+(i+1)*RISE;p.extend([(x,Z),(x+.3*direction,Z)])
        # Follow the long axis of the strip across the flight. The 16 px
        # dimension covers the depth and fold, not the 1.8 m stair width.
        strip_start=(9+11*i+(0 if direction==1 else 19))%49
        strip_width,strip_height=SIZE['M10']
        def top_uv(q,strip_start=strip_start,x=x):
            return ((strip_start+(q.y-y)*PX)/strip_width,1-(2+abs(q.x-x)*PX)/strip_height)
        def fold_uv(q,strip_start=strip_start,Z=Z):
            return ((strip_start+(q.y-y)*PX)/strip_width,1-(11+(Z-q.z)*PX)/strip_height)
        u,U=sorted((x,x+.045*direction));box(c,f'{name}_NosingTop_{i+1:02}',(u,U,y,Y,Z-.001,Z+.0007),'M10',face_uv={1:top_uv})
        u,U=sorted((x-.0015*direction,x));box(c,f'{name}_NosingFold_{i+1:02}',(u,U,y,Y,Z-.010,Z+.0007),'M10',face_uv={1:top_uv,(5 if direction==1 else 3):fold_uv})
        x_left,x_right=sorted((x,x+.30*direction))
        wall_name='L01_ZONE_LOWER' if direction==1 else 'L01_ZONE_UPPER'
        stair_wall_foot(f'{wall_name}_Foot_{i+1:02}',x_left,x_right,y if direction==1 else Y,Z,direction)
    p += [(x1,z0+1.9-.22)]
    def step_origin(a,b):
        if max(a[1],b[1])<=z0 or (abs(a[1]-b[1])>.001 and abs(a[0]-b[0])>.001):
            return 0,0
        tread_index=round((max(a[1],b[1])-z0)/RISE)-1
        return (24*tread_index,53 if direction==1 else 125) if 0<=tread_index<11 else (0,0)
    prism_xz(c,name+'_ClosedFlight',p,y,Y,'M03_STAIR',side_origin=step_origin,properties={'rises':12,'visible_treads':11,'tread_depth_m':.3,'slab_underface':'solid sloped closed profile'})
flight('Lower',-.9,.9,0,1);flight('Upper',1.1,2.9,1.9,-1)
for name,b in [('EntryLanding',(-3.45,X0,-.9,.9,-.2,0)),('TurnLanding',(X1,3.45,-.9,2.9,1.70,1.90)),('FloorLanding',(-3.45,X0,1.1,2.9,3.60,3.80))]:box(c,name,b,'M03_STAIR')

def lighting_segment(name,x,X,y,z,Z,facing):
    # 40mm slot on sloped face. 20mm groove depth and 15mm cap lip.
    sign=1 if facing==1 else -1; back=y-.020*sign; outer=y-.19*sign; a,b=sorted((outer,back));c0,c1=sorted((back,y))
    box(c,name+'_Backing',(x,X,a,b,min(z,Z)-1.4,max(z,Z)+2.2),'M01_STAIR')
    prism_xz(c,name+'_WallLower',[(x,min(z,Z)-1.4),(X,min(z,Z)-1.4),(X,Z-.020),(x,z-.020)],c0,c1,'M01_STAIR')
    prism_xz(c,name+'_WallUpper',[(x,z+.020),(X,Z+.020),(X,max(z,Z)+2.2),(x,max(z,Z)+2.2)],c0,c1,'M01_STAIR')
    ya,yb=sorted((y-.017*sign,y-.012*sign))
    glass=prism_xz(c,name,[(x,z-.020),(X,Z-.020),(X,Z+.020),(x,z+.020)],ya,yb,'M09',properties={'width_m':.04,'groove_depth_m':.02,'diffuser_aim_down_degrees':15})
    for vert in glass.data.vertices:
        mid=z+(Z-z)*(vert.co.x-x)/(X-x)
        vert.co.y+=sign*math.tan(math.radians(15))*(vert.co.z-mid)
    ya,yb=sorted((y-.020*sign,y+.015*sign))
    prism_xz(c,name+'_Lip',[(x,z+.018),(X,Z+.018),(X,Z+.026),(x,z+.026)],ya,yb,'M05-D')

# Upper and lower run strips lie on their real outer walls, not the same wall.
lighting_segment('L01_ZONE_LOWER',X0,X1,-.90,1.10,1.10+1.9,1)
lighting_segment('L01_ZONE_TURN',X1,3.45,-.90,3.00,3.00,1)
stair_wall_foot('L01_ZONE_TURN_Foot',X1,3.45,-.90,1.9,1)
back_start=set(c.objects)
lighting_segment('L01_TURN_BACK',-.90,2.90,0.,3.00,3.00,1)
stair_wall_foot('L01_TURN_BACK_Foot',-.90,2.90,0.,1.9,1)
for o in set(c.objects)-back_start:
    for vert in o.data.vertices:
        x,y,z=vert.co;vert.co=(3.45-y,x,z)
lighting_segment('L01_TURN_UPPER_RETURN',X1,3.45,2.90,3.00,3.00,-1)
stair_wall_foot('L01_TURN_UPPER_RETURN_Foot',X1,3.45,2.90,1.9,-1)
lighting_segment('L01_ZONE_UPPER',X0,X1,2.90,4.90,3.00,-1)
lighting_segment('L01_ZONE_FLOOR',-3.45,X0,2.90,4.90,4.90,-1)
stair_wall_foot('L01_ZONE_FLOOR_Foot',-3.45,X0,2.90,3.8,-1)
box(c,'EntryWall',(-3.45,X0,-1.09,-.90,-.2,3.0),'M01_STAIR')
stair_wall_foot('EntryWall_Foot',-3.45,X0,-.90,0,1)
export(c,'ST-01_stair_sample')

def run_pickets(c,name,x,X,y,z,Z,kind):
    length=X-x
    ascending=Z>z
    def slope(u):
        return z+(Z-z)*(u-x)/length
    def tread(u):
        run=(u-x) if ascending else (X-u)
        index=min(10,max(0,math.floor((run+1e-6)/.30)))
        return min(z,Z)+(index+1)*RISE

    # Put structural posts at tread centers. A lower tube carries the smaller
    # pickets, so their ends meet real hardware rather than the abstract slope.
    material='M04' if kind=='A' else 'M05-D'
    inside_y=y+(-.071 if ascending else .071)
    for i,step in enumerate((0,3,6,9,10)):
        u=x+(step+.5)*.30
        base=tread(u)
        top=slope(u)+1.10
        post_y=y if kind=='A' else y+(.012 if ascending else -.012)
        box(c,f'{name}_Post_{i:02}',(u-.0175,u+.0175,post_y-.0175,post_y+.0175,base,top),material)
        box(c,f'{name}_Foot_{i:02}',(u-.031,u+.031,post_y-.028,post_y+.028,base-.002,base+.009),material)
        bracket_y=sorted((post_y,inside_y))
        grip_z=slope(u)+.90
        box(c,f'{name}_GripBracket_{i:02}',(u-.013,u+.013,*bracket_y,grip_z-.013,grip_z+.004),'M04')
    if kind=='A':
        tube(c,f'{name}_LowerRail',[(x,y,z+.195),(X,y,Z+.195)],.014)
        for i in range(1,round(length/.10)):
            u=x+i*.10
            v=slope(u)
            tube(c,f'{name}_Picket_{i:02}',[(u,y,v+.195),(u,y,v+1.10)],.006)
    else:
        cuts=[x+j*.30 for j in range(1,11)]
        for i in range(3):
            xa=x+i*length/3
            xb=x+(i+1)*length/3
            edges=[xa,*(cut for cut in cuts if xa<cut<xb),xb]
            bottom=[]
            for a,b in zip(edges,edges[1:]):
                level=tread((a+b)/2)+.020
                bottom.extend(((a,level),(b,level)))
            za,zb=slope(xa),slope(xb)
            profile=bottom+[(xb,zb+1.10),(xa,za+1.10)]
            prism_xz(c,f'{name}_FoldedGuard_{i:02}',profile,y-.0015,y+.0015,'M05-D')
            prism_xz(c,f'{name}_Return_{i:02}',[(xa,za+1.097),(xb,zb+1.097),(xb,zb+1.10),(xa,za+1.10)],y-.015,y+.015,'M05-D')

for variant in ('A','B'):
    c=group('HR-'+variant)
    # Both shared wall grips extend along full flights; ends return to walls.
    exterior=[(-3.10,-.90,.90),(-3.10,-.829,.90),(X0,-.829,.90),(X1,-.829,2.80),(3.37,-.829,2.8),(3.37,2.829,2.8),(X1,2.829,2.8),(X0,2.829,4.7),(-3.1,2.829,4.7),(-3.1,2.90,4.7)]
    tube(c,f'HR-{variant}_WallGrip',smooth_corners(exterior))
    for i,u in enumerate((-1.35,-.45,.45,1.35)):
        rise=(u-X0)/(X1-X0)*1.9
        for side,wall_y,grip_y,h in [('Lower',-.90,-.829,.90+rise),('Upper',2.90,2.829,4.70-rise)]:
            a,b=sorted((wall_y,grip_y))
            box(c,f'HR-{variant}_{side}_WallBracket_{i:02}',(u-.014,u+.014,a,b,h-.017,h+.003),'M04')
    inside=[(X0,.829,.9),(X1,.829,2.8),(X1+.14,.9,2.8),(X1+.14,1.1,2.8),(X1,1.171,2.8),(X0,1.171,4.7)]
    tube(c,f'HR-{variant}_InnerGrip',smooth_corners(inside,.055),.021 if variant=='A' else .020,.021 if variant=='A' else .016)
    for side,y,z,Z in [('Lower',.90,0,1.9),('Upper',1.10,3.8,1.9)]:
        run_pickets(c,'HR-'+variant+'_'+side,X0,X1,y,z,Z,variant)
    if variant=='A':tube(c,'HR-A_GuardTop',smooth_corners([(X0,.9,1.1),(X1,.9,3.0),(X1+.1,1.,3.0),(X1,1.1,3.0),(X0,1.1,4.9)],.06),.018)
    export(c,'HR-'+variant)

def door(id,W,H,ratios):
    typ=id[:2]; A=id[-1]=='A';c=group(id); name='FACE_'+id.replace('-','_');light='M05-L';dark='M05-D'
    coat=dark if typ=='EL' or id=='EN-B' else light
    M[name]=mat(name,COLORS[coat]);SIZE[name]=(round(W*PX),round(H*PX))
    frame=(.06,.06,.06) if id=='FD-A' else (.07,.07,.07) if typ=='FD' else (.08,.08,.16) if id=='EL-A' else (.06,.14,.12) if typ=='EL' else (.06,.06,.08)
    L,R,T=frame; depth=.13
    box(c,id+'_FrameL',(-W/2-L,-W/2,-.03,depth,0,H),dark if typ!='EL' else 'M04')
    box(c,id+'_FrameR',(W/2,W/2+R,-.03,depth,0,H),dark if typ!='EL' else 'M04')
    box(c,id+'_Head',(-W/2-L,W/2+R,-.03,depth,H,H+T),dark if typ!='EL' else 'M04')
    box(c,id+'_Threshold',(-W/2,W/2,-.055,.10,-.006,0),'M04')
    # Perimeter seals terminate at the actual opening. They never glow.
    for n,b in [('SealL',(-W/2,-W/2+.005,-.018,.012,0,H)),('SealR',(W/2-.005,W/2,-.018,.012,0,H)),('SealH',(-W/2,W/2,-.018,.012,H-.005,H))]:box(c,id+'_'+n,b,'M08')
    x=-W/2;spans=[]
    for i,ratio in enumerate(ratios):
        w=W*ratio;X=x+w;gap=.005 if id=='EL-A' else .004;left=x+(gap if i else .005);right=X-(gap if i<len(ratios)-1 else .005)
        y=.06 if typ=='EL' else .03 if typ=='FD' else .04
        if id=='EL-B':y+=i*.010
        crease=.012 if id=='EL-A' else 0
        section=[(left,y),(right,y)]
        if crease:section=[(left,y),(right-.08,y),(right,y+crease)] if i==0 else [(left,y+crease),(left+.08,y),(right,y)]
        profile=section+[(right,y+.05),(left,y+.05)]
        n=len(profile);verts=[(u,v,z) for z in (.004,H-.005) for u,v in profile]
        faces=[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
        front_uv=lambda q:((q.x+W/2)/W,q.z/H)
        o=mesh(c,f'{id}_Leaf_{i+1:02}',verts,[(tuple(f)) for f in faces],[light if typ=='EN' else coat,name],
            {j+2:1 for j in range(len(section)-1)}, {j+2:front_uv for j in range(len(section)-1)},
            {'role':'door_leaf','nominal_width_m':w,'opening_width_m':W,'opening_height_m':H,'depth_m':.05})
        if typ!='EL':
            px=x if i==0 else X; pivot=bpy.data.objects.new(f'{id}_Leaf_{i+1:02}_PIVOT',None);c.objects.link(pivot);pivot.location=(px,y+.025,0);pivot['role']='hinge';pivot['opening_degrees']=90
            parts=[o]; cx=(left+right)/2
            if A or typ=='EN':
                span=w*.65;parts.append(box(c,f'{id}_Release_{i+1:02}',(cx-span/2,cx+span/2,y+.050,y+.075,.979,1.021),'M04'))
            else:
                hx=right-.10 if i==0 else left+.08; height=.2 if i==0 else .12
                parts.append(box(c,f'{id}_Release_{i+1:02}',(hx-.0275,hx+.0275,y+.050,y+.074,1-height/2,1+height/2),'M04'))
            if typ=='FD' and (A or i==0):
                h=.22 if A else .30;parts.append(box(c,f'{id}_Kick_{i+1:02}',(left+.014,right-.014,y-.002,y+.001,.015,.015+h),'M04'))
            if id=='FD-B' and i==1:
                mid=(left+right)/2;parts.append(box(c,id+'_ServiceBand',(mid-.035,mid+.035,y-.012,y+.001,.36,H-.11),dark));parts.append(box(c,id+'_StateWindow',(mid-.018,mid+.018,y-.013,y-.011,1.52,1.56),'M08'))
            for p in parts:
                p.parent=pivot
                for vert in p.data.vertices:vert.co-=pivot.location
        spans.append(w);x=X
    if typ=='EL':
        tx=W/2+.075;box(c,id+'_DarkTouch',(tx-.045,tx+.045,-.034,-.030,1.07,1.23),'M08')
    if typ=='EN':
        if A:
            for side,b in [('L',(-W/2-.18,-W/2,-.10,.02,0,H+.22)),('R',(W/2,W/2+.18,-.10,.02,0,H+.22)),('T',(-W/2-.18,W/2+.18,-.10,.02,H,H+.22))]:box(c,id+'_Portal_'+side,b,'M06')
            box(c,id+'_DripReturn',(-W/2-.18,W/2+.18,-.115,-.10,H+.203,H+.22),'M06')
        else:
            for side,b in [('L',(-W/2-.10,-W/2,-.08,.05,0,H+.08)),('R',(W/2,W/2+.10,-.08,.05,0,H+.08))]:box(c,id+'_FoldedPortal_'+side,b,'M07')
            box(c,id+'_Canopy',(-W/2-.15,W/2+.15,-.60,.02,H,H+.08),'M07')
            box(c,id+'_DripFold',(-W/2-.15,W/2+.15,-.60,-.575,H-.025,H+.001),'M07')
            box(c,id+'_DirectionLight',(-.42,.42,-.215,-.185,H-.008,H),'M09')
        box(c,id+'_ExteriorTransition',(-W/2-.36,W/2+.36,-1.50,.02,-.08,-.005),'M06')
        box(c,id+'_DrainReturn',(-W/2-.36,W/2+.36,-1.5,-1.47,-.007,.001),'M07')
    export(c,id)
    return {'id':id,'W_m':W,'H_m':H,'panel_widths_m':spans,'front_texture_size':SIZE[name], 'front_axis_godot':'+Z','floor_center':[0,0,0], 'status':'ASSET_ONLY' if typ=='EN' else 'isolated_candidate'}

doors=[door('FD-A',1.8,2.4,[.5,.5]),door('FD-B',1.8,2.4,[.65,.35]),door('EL-A',1.4,2.4,[.5,.5]),door('EL-B',1.4,2.4,[1/3]*3),door('EN-A',1.8,2.4,[.5,.5]),door('EN-B',1.8,2.4,[.5,.5])]
c=group('K-01');box(c,'K01FloorSign',(-.15,.15,-.02,.02,1.4,1.58),'M05-D');box(c,'K01ExitSign',(-.18,.18,-.02,.02,1.92,2.04),'M05-D');box(c,'K01Coping',(-1,1,-.06,.06,3,3.06),'M07');box(c,'K01MaintenanceCover',(-.15,.15,-.02,.02,.5,1),'M05-D');export(c,'K-01_accessories')
record={'doors':doors,'stair_bounds_m':{'x':[-3.45,3.62],'y':[-1.09,3.09],'floor_z':[0,3.8]},'stair':{'steps_per_run':11,'risers_per_run':12,'rise_m':RISE,'run_m':3.30,'width_m':1.8,'top_nosing_width_m':.045,'front_fold_m':.01,'turn_landing_m':[1.8,3.8]},'nominal_walkable_flight_before_accessories_m':1.8,'measured_continuous_grip_inner_edges_clear_m':{'HR-A':1.616,'HR-B':1.617},'clearance_status':'Both isolated HR candidates encroach on frozen nominal 1.8m width. No walls or route changed. Not approved to install.', 'light_nodes':['L01_ZONE_LOWER','L01_ZONE_TURN','L01_ZONE_UPPER','L01_ZONE_FLOOR'],'godot_motion_waypoints':[[-3.6,0,0],[-1.65,0,0],[1.65,1.9,0],[2.62,1.9,0],[2.62,1.9,-2.0],[1.65,1.9,-2],[-1.65,3.8,-2],[-3.25,3.8,-2]],'limits':['EN ASSET_ONLY: no frozen 1F exterior exit anchor','No formal route installation, no fire certification','Independent realtime lighting; no lightmap data reused']}
(HERE/'interior_manifest.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
sys.path.insert(0,str(HERE))
from bind_preview_materials import bind
bind(OUT.parent/'textures')
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'interior_accessories.blend'))
