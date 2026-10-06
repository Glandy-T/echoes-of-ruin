"""Extrude the completed native plan, without changing its XY geometry.

Run with installed FreeCAD Python; render with render_visual_blockout.FCMacro.
All new heights are visual-test PROVISIONAL values, not construction decisions.
"""
from pathlib import Path
import json, math, hashlib, re
import FreeCAD as App
import Part
from plan_layout import PARAMETERS, COUNTS, make_layout, check_layout

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'admin_facility_v2.FCStd'
TARGET=ROOT/'admin_facility_3d_blockout_v1.FCStd'
HEIGHTS={
 'WallHeight':(5.8,'All walls; visual test requested by brief'),
 'DoorHeight':(2.4,'Door opening clear height; visual test'),
 'FloorThickness':(.15,'Display slab below Z=0'),
 'RoofThickness':(.15,'Optional roof, hidden for interior review'),
 'GateHeight':(1.0,'Waist-height authentication block'),
 'DeskTopZ':(.72,'Desk underside'), 'DeskThickness':(.06,'Desk top slab'),
 'ChairSeatZ':(.43,'Chair seat underside'), 'ChairSeatThickness':(.06,'Seat'),
 'ChairBackHeight':(.62,'Chair back above seat'),
 'MonitorBottomZ':(.86,'Dual-screen lower edge'), 'MonitorHeight':(.36,'Screen'),
 'FixtureHeight':(.45,'WC fixture block'),
 'BasinBottomZ':(.78,'Wash basin underside'), 'BasinThickness':(.10,'Wash basin block'),
 'GuideBottomZ':(.70,'Map lower edge'), 'GuideHeight':(1.4,'Map panel height'),
 'HumanHeight':(1.7,'Pure reference cylinder'), 'HumanRadius':(.18,'Reference cylinder'),
}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def build():
 before=sha(SOURCE)
 doc=App.openDocument(str(SOURCE));doc.Label='管理设施 | 真实尺度3D Blockout v1'
 # Keep the original plan and its drawing pages inside this new document.
 for obj in doc.Objects:
  if obj.ViewObject:obj.Visibility=False
 values={k:getattr(doc.Parameters,k).Value/1000 for k in PARAMETERS}
 values.update({k:getattr(doc.Parameters,k) for k in COUNTS})
 values,features=make_layout(values);checks=check_layout(values,features)
 p=doc.addObject('App::FeaturePython','BlockParameters');p.Label='3D高度参数 | 全部PROVISIONAL'
 p.addProperty('App::PropertyString','Status');p.Status='PROVISIONAL; visual space test only'
 for key,(value,description) in HEIGHTS.items():
  p.addProperty('App::PropertyLength',key,'PROVISIONAL',description);setattr(p,key,value*1000)
 def exp(s):
  def repl(m):
   k=m.group(0)
   return '(Parameters.'+k+' / (1000 mm))' if k in PARAMETERS else 'Parameters.'+k if k in COUNTS else k
  return '('+re.sub(r'[A-Za-z_][A-Za-z_0-9]*',repl,str(s))+') * (1000 mm)'
 groups={}
 for key in ['Architecture','Equipment','Furniture','HingedDoors','SlidingDoors','Guides','References','Roof']:
  groups[key]=doc.addObject('App::DocumentObjectGroup','Block_'+key)
 palette={'wall':(.84,.85,.86),'gate':(.35,.41,.43),'table':(.49,.51,.53),'chair':(.28,.30,.32),'monitor':(.16,.18,.20),'fixture':(.91,.91,.91),'basin':(.76,.78,.79),'guide':(.38,.48,.53),'door':(.59,.61,.63)}
 registry=[]
 def style(o,role,owner,source=''):
  o.addProperty('App::PropertyString','PlanSource');o.PlanSource=source
  o.addProperty('App::PropertyString','PlanOwner');o.PlanOwner=owner
  o.addProperty('App::PropertyString','BlockRole');o.BlockRole=role
  if o.ViewObject:
   o.ViewObject.ShapeColor=palette.get(role,(.7,.7,.7));o.ViewObject.LineColor=(.20,.22,.24)
   o.ViewObject.DisplayMode='Flat Lines';o.ViewObject.LineWidth=1.;o.Visibility=True
  registry.append(o.Name);return o
 def box(name,x,y,w,d,z,h,role,owner,group):
  o=doc.addObject('Part::Box',name)
  for key,val in [('Length',w),('Width',d),('Height',h),('Placement.Base.x',x),('Placement.Base.y',y),('Placement.Base.z',z)]:o.setExpression(key,exp(val) if not str(val).startswith('BlockParameters.') else val)
  groups[group].addObject(o);return style(o,role,owner)
 def extrusion(f,z,h,group):
  o=doc.addObject('Part::Extrusion','B3_'+f['name']);o.Base=doc.getObject(f['name']);o.DirMode='Normal';o.Solid=True
  o.setExpression('LengthFwd','BlockParameters.'+h)
  if z:o.setExpression('Placement.Base.z','BlockParameters.'+z)
  groups[group].addObject(o);style(o,f['role'],f['owner'],f['name'])
  if doc.getObject(f['name']).ViewObject:doc.getObject(f['name']).Visibility=False
  return o
 floor=box('B3_Floor','0','0','EnvelopeWidth','EnvelopeDepth','-0.15','BlockParameters.FloorThickness','floor','Outer','Architecture')
 floor.setExpression('Placement.Base.z','-BlockParameters.FloorThickness')
 for f in features:
  k,r,n=f['kind'],f['role'],f['name']
  if k=='rect' and r in ['wall','gate','table','chair','monitor','fixture','basin','guide','door']:
   mapping={'wall':(None,'WallHeight','Architecture'),'gate':(None,'GateHeight','Equipment'),'table':('DeskTopZ','DeskThickness','Furniture'),'chair':('ChairSeatZ','ChairSeatThickness','Furniture'),'monitor':('MonitorBottomZ','MonitorHeight','Furniture'),'fixture':(None,'FixtureHeight','Furniture'),'basin':('BasinBottomZ','BasinThickness','Furniture'),'guide':('GuideBottomZ','GuideHeight','Guides'),'door':(None,'DoorHeight','SlidingDoors')}
   z,h,g=mapping[r];o=extrusion(f,z,h,g)
   if r=='chair':
    back=box('B3_'+n+'_Back',f['x'],f'({f["y"]})+({f["d"]})-0.06',f['w'],'.06','BlockParameters.ChairSeatZ','BlockParameters.ChairBackHeight','chair',f['owner'],'Furniture')
    back.setExpression('Placement.Base.z','BlockParameters.ChairSeatZ+BlockParameters.ChairSeatThickness')
   if r=='table':
    # One plain support below each top, kept inside the existing desk footprint.
    support=box('B3_'+n+'_Support',f'({f["x"]})+0.08',f'({f["y"]})+0.08',f'({f["w"]})-0.16',f'({f["d"]})-0.16','0','BlockParameters.DeskTopZ','table',f['owner'],'Furniture')
   if r=='guide':
    stem=box('B3_'+n+'_Stand',f'({f["x"]})+({f["w"]})/2-0.06',f['y'],'.12',f['d'],'0','BlockParameters.GuideBottomZ','guide',f['owner'],'Guides')
  elif k=='line' and n.endswith('_Leaf'):
   # Native plan records the open leaf at its approved 90-degree orientation.
   a=f['values'];length=math.hypot(a['x2']-a['x1'],a['y2']-a['y1'])
   leaf=doc.addObject('Part::Box','B3_'+n)
   delta='x' if abs(a['x2']-a['x1'])>1e-8 else 'y';sign=1 if a[delta+'2']>a[delta+'1'] else -1
   leaf.setExpression('Length',exp(f'(({f[delta+"2"]})-({f[delta+"1"]}))*{sign}'))
   leaf.setExpression('Width','Parameters.DoorLeaf');leaf.setExpression('Height','BlockParameters.DoorHeight')
   leaf.Placement.Rotation=App.Rotation(App.Vector(0,0,1),math.degrees(math.atan2(a['y2']-a['y1'],a['x2']-a['x1'])))
   leaf.setExpression('Placement.Base.x',exp(f['x1']));leaf.setExpression('Placement.Base.y',exp(f['y1']))
   groups['HingedDoors'].addObject(leaf);style(leaf,'door',f['owner'],n)
 # Restore real wall above every door/opening; no floor-to-roof fake slots.
 for f in [f for f in features if f['kind']=='rect' and f['role']=='door']:
  is_front=f['name'].startswith('Front');y='0' if is_front else 'EnvelopeDepth-OuterWall'
  lintel=box('B3_Lintel_'+f['name'],f['x'],y,f['w'],'OuterWall','BlockParameters.DoorHeight','1','wall','Outer','Architecture')
  lintel.setExpression('Height','BlockParameters.WallHeight-BlockParameters.DoorHeight')
 # Derive hinge door thresholds from the two plan approach rectangles.
 for i in range(0,len(checks['door_approach_reserved_rectangles_m']),2):
  a,b=checks['door_approach_reserved_rectangles_m'][i:i+2];f=next(f for f in features if f['name']==a['door'].replace('_Swing','_Leaf'))
  v=f['values'];alongx=abs(v['y2']-v['y1'])>1e-7
  x=min(a['x'],b['x']) if alongx else min(a['x']+a['w'],b['x']+b['w'])
  y=min(a['y']+a['d'],b['y']+b['d']) if alongx else min(a['y'],b['y'])
  w=a['w'] if alongx else values['Partition'];d=values['Partition'] if alongx else a['d']
  # Link position/width back to leaf's coordinate expressions, not a second plan.
  leaf=doc.getObject('B3_'+f['name']);lx=v['x1'];ly=v['y1']
  opening=next(g for g in features if g['name']==a['door'])['r']
  radius=next(g for g in features if g['name']==a['door'])['values']['r']
  def offset(delta):
   if abs(delta)<1e-8:return '0'
   if abs(abs(delta)-values['Partition'])<1e-8:return ('-' if delta<0 else '')+'Partition'
   if abs(abs(delta)-radius)<1e-8:return ('-' if delta<0 else '')+'('+opening+')'
   raise AssertionError(('Unexpected door threshold offset',f['name'],delta))
  lintel=box('B3_Lintel_'+f['name'],f'({f["x1"]})+({offset(x-lx)})',f'({f["y1"]})+({offset(y-ly)})',str(w) if alongx else 'Partition','Partition' if alongx else str(d),'BlockParameters.DoorHeight','1','wall',f['owner'],'Architecture')
  lintel.setExpression('Length' if alongx else 'Width',exp(opening));lintel.setExpression('Height','BlockParameters.WallHeight-BlockParameters.DoorHeight')
 roof=box('B3_Roof','0','0','EnvelopeWidth','EnvelopeDepth','BlockParameters.WallHeight','BlockParameters.RoofThickness','roof','Outer','Roof')
 if roof.ViewObject:roof.Visibility=False
 for i,(x,y) in enumerate([(15.,12.),(30.5,18.)]):
  human=doc.addObject('Part::Cylinder','B3_ScaleReference_'+str(i+1));human.setExpression('Radius','BlockParameters.HumanRadius');human.setExpression('Height','BlockParameters.HumanHeight');human.Placement.Base=App.Vector(x*1000,y*1000,0)
  groups['References'].addObject(human);style(human,'reference','ScaleOnly')
 doc.recompute()
 assert all(doc.getObject(n).Shape.isValid() for n in registry)
 # Validate every extruded XY footprint against the original native sketch.
 xy=[]
 for f in features:
  o=doc.getObject('B3_'+f['name'])
  if o and o.TypeId=='Part::Extrusion':
   s=doc.getObject(f['name']).Shape.BoundBox;b=o.Shape.BoundBox
   assert all(abs(getattr(s,k)-getattr(b,k))<1e-5 for k in ['XMin','XMax','YMin','YMax']),f['name'];xy.append(f['name'])
 doc.saveAs(str(TARGET));assert sha(SOURCE)==before
 result={'revision':'3d-blockout-v1','source_main':'83232b0ab064e730cc0b1beadb2a5d945373054a','source_plan_sha256':before,'source_plan_unchanged':True,'source_feature_count':len(features),'extruded_xy_footprints_verified':len(xy),'native_3d_objects':len(registry),'wall_height_m':5.8,'eye_height_m':1.6,'new_height_parameters':{k:{'value_m':v[0],'status':'PROVISIONAL','purpose':v[1]} for k,v in HEIGHTS.items()},'source_plan_checks':checks,'visual_review':'pending','acceptance':'PENDING VISUAL REVIEW','roof_default_hidden':True,'door_panels':'hinged leaves retain source open plan position; sliders hidden in open-entry screenshots','wall_openings':'real threshold void with parameter-linked lintel above DoorHeight; roof-level full-height enclosure','future_art_development_started':False}
 (ROOT/'visual_blockout_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 App.closeDocument(doc.Name);return result

if __name__=='__main__':print(json.dumps({k:v for k,v in build().items() if k not in ['source_plan_checks','new_height_parameters']}))
