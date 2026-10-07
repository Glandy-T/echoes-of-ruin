"""V2: integrated two-entry stairs, symmetric four-car freight core, metre units."""
import math,heapq
PARAMETERS={'RoomWidth':21.,'RoomDepth':9.5,'Wall':.2,'RoomDoor':1.4,'PersonnelCorridor':2.4,
 'MachineSpine':6.,'MachineCross':4.,'TransferClear':11.2,'PlenumClear':4.,'BypassClear':2.4,'BypassOffset':3.4,'WaitOffset':7.,
 'ConnectorClear':2.4,'ControlDoor':1.8,'ElevatorCarWidth':2.1,'ElevatorCarDepth':2.4,'ElevatorDoor':1.4,
 'FreightCarWidth':3.2,'FreightCarDepth':3.8,'FreightDoor':2.4,'CarrierWidth':1.7,'CarrierLength':3.1,'TurnClearance':.1,
 'StoreyHeight':3.8,'FlightWidth':1.8,'StairGap':.2,'LandingLength':1.8,'Tread':.3,'PlanThickness':.001}
DERIVED={'ZoneWidth':'4*RoomWidth-3*Wall','RoomPitch':'RoomWidth-Wall','ZoneDepth':'3*RoomDepth+2*PersonnelCorridor','RowPitch':'RoomDepth+PersonnelCorridor',
 'FreightOuterWidth':'FreightCarWidth+2*Wall','FreightOuterDepth':'FreightCarDepth+2*Wall','CoreWidth':'TransferClear+2*FreightOuterDepth',
 'EastZoneX':'ZoneWidth+CoreWidth','NorthZoneY':'ZoneDepth+CoreWidth','MainWidth':'2*ZoneWidth+CoreWidth','MainDepth':'2*ZoneDepth+CoreWidth','CenterX':'MainWidth/2','CenterY':'MainDepth/2',
 'Rise':'StoreyHeight/Risers','FlightRun':'(Risers/2-1)*Tread','StairLength':'2*LandingLength+FlightRun+2*Wall','StairWidth':'2*FlightWidth+StairGap+2*Wall',
 'StairEmbedded':'StairLength-ConnectorClear-Wall','StairProjection':'ConnectorClear+Wall','StairLandingXWest':'-ConnectorClear+LandingLength/2',
 'ElevatorOuterWidth':'ElevatorCarWidth+2*Wall','ElevatorOuterDepth':'ElevatorCarDepth+2*Wall','ExternalReach':'ConnectorClear+ElevatorOuterWidth','MaxWidth':'MainWidth+2*ExternalReach'}
def merge_rectangles(rects):
 ys=sorted({round(r[k],8) for r in rects for k in ['y1','y2']});out=[];previous={}
 for ya,yb in zip(ys,ys[1:]):
  ym=(ya+yb)/2;ranges=sorted((round(r['x1'],8),round(r['x2'],8)) for r in rects if r['y1']<ym<r['y2']);merged=[]
  for a,b in ranges:
   if merged and a<=merged[-1][1]+1e-8:merged[-1][1]=max(b,merged[-1][1])
   else:merged.append([a,b])
  current={}
  for a,b in merged:
   key=(a,b)
   if key in previous:item=previous[key];item['y2']=yb
   else:item=dict(x1=a,y1=ya,x2=b,y2=yb);out.append(item)
   current[key]=item
  previous=current
 return out
def build_layout(overrides=None):
 v=dict(PARAMETERS);v['Risers']=24;v.update(overrides or {})
 for k,e in DERIVED.items():v[k]=eval(e,{'__builtins__':{}},v)
 raw=[];doors=[];rooms=[];corridors=[];cores=[];stairs=[];references=[];freight=[];waits=[];registry={'x':{},'y':{}}
 def val(e):return float(eval(str(e),{'__builtins__':{}},v))
 def coord(e,axis):n=val(e);registry[axis].setdefault(round(n,8),str(e));return n
 def rect(x,y,w,d,tag):
  a,b=coord(x,'x'),coord(y,'y');c,f=coord(f'({x})+({w})','x'),coord(f'({y})+({d})','y');assert c>a+1e-8 and f>b+1e-8,(tag,x,y,w,d)
  return dict(x1=a,y1=b,x2=c,y2=f,tag=tag,expressions=dict(x=str(x),y=str(y),w=str(w),d=str(d)))
 def wall(x,y,w,d,tag):raw.append(rect(x,y,w,d,tag))
 def hw(x,y,length,holes,tag):
  cursor=x
  for cx,width,kind in sorted(holes,key=lambda h:val(h[0])):
   a=f'({cx})-({width})/2';b=f'({cx})+({width})/2'
   if val(a)>val(cursor)+1e-8:wall(cursor,y,f'({a})-({cursor})','Wall',tag)
   doors.append(dict(id=f'D{len(doors)+1:03}',x=val(cx),y=val(y)+v['Wall']/2,width=val(width),orientation='H',kind=kind,tag=tag))
   coord(a,'x');coord(b,'x');cursor=b
  end=f'({x})+({length})'
  if val(end)>val(cursor)+1e-8:wall(cursor,y,f'({end})-({cursor})','Wall',tag)
 def vw(x,y,length,holes,tag):
  cursor=y
  for cy,width,kind in sorted(holes,key=lambda h:val(h[0])):
   a=f'({cy})-({width})/2';b=f'({cy})+({width})/2'
   if val(a)>val(cursor)+1e-8:wall(x,cursor,'Wall',f'({a})-({cursor})',tag)
   doors.append(dict(id=f'D{len(doors)+1:03}',x=val(x)+v['Wall']/2,y=val(cy),width=val(width),orientation='V',kind=kind,tag=tag))
   coord(a,'y');coord(b,'y');cursor=b
  end=f'({y})+({length})'
  if val(end)>val(cursor)+1e-8:wall(x,cursor,'Wall',f'({end})-({cursor})',tag)
 zones=[('SW','0','0',False),('SE','EastZoneX','0',True),('NW','0','NorthZoneY',False),('NE','EastZoneX','NorthZoneY',True)]
 for zone,zx,zy,right in zones:
  for row in range(3):
   for col in range(4):
    x=f'({zx})+{col}*RoomPitch';y=f'({zy})+{row}*RowPitch';south=row in [1,2];north=row in [0,1]
    r=rect(x,y,'RoomWidth','RoomDepth',zone+'_Room');r.update(id=f'{zone}-{row*4+col+1:02}',zone=zone,row=row,col=col,capacity=20,south_door=south,north_door=north);rooms.append(r)
    holes=[(f'({x})+RoomWidth/2','RoomDoor','room')] if south else []
    hw(x,y,'RoomWidth',holes,r['id']);holes=[(f'({x})+RoomWidth/2','RoomDoor','room')] if north else []
    hw(x,f'({y})+RoomDepth-Wall','RoomWidth',holes,r['id']);wall(x,f'({y})+Wall','Wall','RoomDepth-2*Wall',r['id']);wall(f'({x})+RoomWidth-Wall',f'({y})+Wall','Wall','RoomDepth-2*Wall',r['id'])
  for ci in range(2):
   cy=f'({zy})+{ci}*RowPitch+RoomDepth';mid=f'({cy})+PersonnelCorridor/2'
   c=rect(f'({zx})+Wall',cy,'ZoneWidth-2*Wall','PersonnelCorridor',zone+'_Corridor');c.update(id=f'{zone}-C{ci+1}',zone=zone,center_y=val(mid));corridors.append(c)
   inner='EastZoneX' if right else 'ZoneWidth-Wall';vw(inner,cy,'PersonnelCorridor',[(mid,'ControlDoor','emergency')],zone+'_InnerGate')
   bx='CenterX+MachineSpine/2' if right else 'ZoneWidth';bw='EastZoneX-CenterX-MachineSpine/2' if right else 'CenterX-MachineSpine/2-ZoneWidth'
   for by in [f'({cy})-Wall',f'({cy})+PersonnelCorridor']:wall(bx,by,bw,'Wall',zone+'_EmergencyBridge')
  def mx(x,w='0'):return f'MainWidth-({x})-({w})' if right else x
  core_y=f'({zy})+RoomDepth-Wall';core_d='RoomDepth+2*PersonnelCorridor+2*Wall'
  core=rect(mx('-ConnectorClear-ElevatorOuterWidth','ConnectorClear+ElevatorOuterWidth+Wall'),core_y,'ConnectorClear+ElevatorOuterWidth+Wall',core_d,zone+'_ElevatorNode');core.update(id=zone+'_ElevatorNode',zone=zone);cores.append(core)
  lift_y=f'({zy})+RoomDepth+PersonnelCorridor+RoomDepth/2-ElevatorOuterDepth/2'
  hw(mx('-ConnectorClear-ElevatorOuterWidth','ElevatorOuterWidth'),lift_y,'ElevatorOuterWidth',[],zone+'_LiftShaft');hw(mx('-ConnectorClear-ElevatorOuterWidth','ElevatorOuterWidth'),f'({lift_y})+ElevatorOuterDepth-Wall','ElevatorOuterWidth',[],zone+'_LiftShaft')
  wall(mx('-ConnectorClear-ElevatorOuterWidth','Wall'),f'({lift_y})+Wall','Wall','ElevatorCarDepth',zone+'_LiftShaft')
  vw(mx('-ConnectorClear-Wall','Wall'),f'({lift_y})+Wall','ElevatorCarDepth',[(f'({lift_y})+ElevatorOuterDepth/2','ElevatorDoor','elevator')],zone+'_LiftDoor')
  r=rect(mx('-ConnectorClear-ElevatorOuterWidth+Wall','ElevatorCarWidth'),f'({lift_y})+Wall','ElevatorCarWidth','ElevatorCarDepth','passenger_car');r.update(zone=zone);references.append(r)
  for yy,dd in [(f'({zy})+RoomDepth',f'({lift_y})-(({zy})+RoomDepth)'),(f'({lift_y})+ElevatorOuterDepth',f'(({zy})+2*RowPitch)-(({lift_y})+ElevatorOuterDepth)')]:wall(mx('-ConnectorClear-Wall','Wall'),yy,'Wall',dd,zone+'_FoyerBoundary')
  # Only close the remote ends. The emergency link to the stair has NO extra gate or airlock.
  if zone.startswith('S'):hw(mx('-ConnectorClear-Wall','ConnectorClear+2*Wall'),core_y,'ConnectorClear+2*Wall',[],zone+'_FoyerEnd')
  else:hw(mx('-ConnectorClear-Wall','ConnectorClear+2*Wall'),f'({zy})+2*RowPitch','ConnectorClear+2*Wall',[],zone+'_FoyerEnd')
 # Integrated stairs: 4.70m embedded, 2.60m external; N/S directly enter the SAME landing.
 for side,right in [('West',False),('East',True)]:
  def mx(x,w='0'):return f'MainWidth-({x})-({w})' if right else x
  sx='-ConnectorClear-Wall';sy='CenterY-StairWidth/2';door_x=mx('StairLandingXWest')
  s=rect(mx(sx,'StairLength'),sy,'StairLength','StairWidth',side+'_Stair');s.update(id=side+'_Stair',side=side);stairs.append(s)
  for yy in [sy,f'({sy})+StairWidth-Wall']:hw(mx(sx,'StairLength'),yy,'StairLength',[(door_x,'ControlDoor','stair')],side+'_StairDirectEntry')
  for xx in [sx,f'({sx})+StairLength-Wall']:wall(mx(xx,'Wall'),f'({sy})+Wall','Wall','StairWidth-2*Wall',side+'_StairSide')
  for i in range(2):
   r=rect(mx('-ConnectorClear+LandingLength','FlightRun'),f'({sy})+Wall+{i}*(FlightWidth+StairGap)','FlightRun','FlightWidth','stair_flight');r.update(side=side,flight=i);references.append(r)
  for xx in ['-ConnectorClear','-ConnectorClear+LandingLength+FlightRun']:
   r=rect(mx(xx,'LandingLength'),f'({sy})+Wall','LandingLength','StairWidth-2*Wall','stair_landing');r.update(side=side);references.append(r)
  # Continuous protected gallery, split by only the two stair entrance doors.
  for yy,dd in [('2*RowPitch+Wall','CenterY-StairWidth/2-(2*RowPitch+Wall)'),('CenterY+StairWidth/2','NorthZoneY+RoomDepth-(CenterY+StairWidth/2)')]:wall(mx('-ConnectorClear-Wall','Wall'),yy,'Wall',dd,side+'_ProtectedGallery')
  for yy,dd in [('ZoneDepth','CenterY-StairWidth/2-ZoneDepth'),('CenterY+StairWidth/2','NorthZoneY-(CenterY+StairWidth/2)')]:wall(mx('0','Wall'),yy,'Wall',dd,side+'_GalleryInnerBoundary')
 # Ordinary machine corridors and reserved margins are separate. Inner room links are emergency-only.
 for east in [False,True]:
  sx='CenterX+MachineSpine/2' if east else 'CenterX-MachineSpine/2-Wall'
  for yy,dd,north in [('0','ZoneDepth-PlenumClear-Wall',False),('NorthZoneY+PlenumClear+Wall','MainDepth-(NorthZoneY+PlenumClear+Wall)',True)]:
   holes=[(f'{"NorthZoneY+" if north else ""}{ci}*RowPitch+RoomDepth+PersonnelCorridor/2','ControlDoor','emergency') for ci in range(2)]
   vw(sx,yy,dd,holes,'SpineControlledBridge')
 for y in ['0','MainDepth-Wall']:hw('ZoneWidth',y,'CoreWidth',[],'CentralOuterClosure')
 xw='StairEmbedded';xe='ZoneWidth-PlenumClear-Wall';xr='EastZoneX+PlenumClear+Wall'
 for yy in ['CenterY-MachineCross/2-Wall','CenterY+MachineCross/2']:
  wall(xw,yy,f'({xe})-({xw})','Wall','WestMachineCross');wall(xr,yy,f'MainWidth-StairEmbedded-Wall-({xr})','Wall','EastMachineCross')
 # Four-compass freight shafts. Their rear walls share the core perimeter.
 for direction in ['N','S','W','E']:
  if direction in ['N','S']:
   fx='CenterX-FreightOuterWidth/2';fy='NorthZoneY-FreightOuterDepth' if direction=='N' else 'ZoneDepth';fw='FreightOuterWidth';fd='FreightOuterDepth'
   front=fy if direction=='N' else f'({fy})+FreightOuterDepth-Wall';back=f'({fy})+FreightOuterDepth-Wall' if direction=='N' else fy
   hw(fx,front,fw,[('CenterX','FreightDoor','freight')],'F'+direction+'_Door');hw(fx,back,fw,[],'F'+direction+'_Back')
   for xx in [fx,f'({fx})+FreightOuterWidth-Wall']:wall(xx,f'({fy})+Wall','Wall','FreightCarDepth','F'+direction+'_Side')
  else:
   fx='ZoneWidth' if direction=='W' else 'EastZoneX-FreightOuterDepth';fy='CenterY-FreightOuterWidth/2';fw='FreightOuterDepth';fd='FreightOuterWidth'
   front=f'({fx})+FreightOuterDepth-Wall' if direction=='W' else fx;back=fx if direction=='W' else f'({fx})+FreightOuterDepth-Wall'
   vw(front,fy,fd,[('CenterY','FreightDoor','freight')],'F'+direction+'_Door');vw(back,fy,fd,[],'F'+direction+'_Back')
   for yy in [fy,f'({fy})+FreightOuterWidth-Wall']:wall(f'({fx})+Wall',yy,'FreightCarDepth','Wall','F'+direction+'_Side')
  r=rect(fx,fy,fw,fd,'freight_shaft');r.update(id='F'+direction,direction=direction);freight.append(r)
  r=rect(f'({fx})+Wall',f'({fy})+Wall','FreightCarWidth' if direction in ['N','S'] else 'FreightCarDepth','FreightCarDepth' if direction in ['N','S'] else 'FreightCarWidth','freight_car');r.update(id='F'+direction,direction=direction);references.append(r)
 # Eight 2.4m bypass openings flank the four lift backs, allowing all axes to enter.
 holesx=[(f'CenterX+({s})*BypassOffset','BypassClear','machine_portal') for s in [-1,1]]
 holesy=[(f'CenterY+({s})*BypassOffset','BypassClear','machine_portal') for s in [-1,1]]
 for yy in ['ZoneDepth','NorthZoneY-Wall']:hw('ZoneWidth',yy,'CoreWidth',holesx,'CoreBypass')
 for xx in ['ZoneWidth','EastZoneX-Wall']:vw(xx,'ZoneDepth','CoreWidth',holesy,'CoreBypass')
 # Four 4m-deep entry plenums: turn before bypass; do not invade the personnel quadrants.
 plenums=[]
 for north in [False,True]:
  yy='NorthZoneY' if north else 'ZoneDepth-PlenumClear';xx='CenterX-TransferClear/2'
  r=rect(xx,yy,'TransferClear','PlenumClear','machine_plenum');r.update(id='PN' if north else 'PS');plenums.append(r)
  wall(f'({xx})-Wall',yy,'Wall','PlenumClear','SpinePlenumSide');wall(f'({xx})+TransferClear',yy,'Wall','PlenumClear','SpinePlenumSide')
  cap='NorthZoneY+PlenumClear' if north else 'ZoneDepth-PlenumClear-Wall';hw(f'({xx})-Wall',cap,'TransferClear+2*Wall',[('CenterX','MachineSpine','machine_portal')],'SpinePlenumEntry')
 for east in [False,True]:
  xx='EastZoneX' if east else 'ZoneWidth-PlenumClear';yy='CenterY-TransferClear/2'
  r=rect(xx,yy,'PlenumClear','TransferClear','machine_plenum');r.update(id='PE' if east else 'PW');plenums.append(r)
  for ya in [f'({yy})-Wall',f'({yy})+TransferClear']:wall(xx,ya,'PlenumClear','Wall','CrossPlenumSide')
  cap='EastZoneX+PlenumClear' if east else 'ZoneWidth-PlenumClear-Wall';vw(cap,f'({yy})-Wall','TransferClear+2*Wall',[('CenterY','MachineCross','machine_portal')],'CrossPlenumEntry')
 transfer=rect('CenterX-TransferClear/2','CenterY-TransferClear/2','TransferClear','TransferClear','transfer_clear')
 for sx in [-1,1]:
  for sy in [-1,1]:
   r=rect(f'CenterX+({sx})*WaitOffset-CarrierWidth/2',f'CenterY+({sy})*WaitOffset-CarrierLength/2','CarrierWidth','CarrierLength','waiting_bay');r.update(id=f'Q{sx}_{sy}',sx=sx,sy=sy);waits.append(r)
 merged=merge_rectangles(raw)
 for i,r in enumerate(merged):
  r['id']=f'W{i+1:03}';r['expressions']=dict(x=registry['x'][round(r['x1'],8)],y=registry['y'][round(r['y1'],8)],w=f'({registry["x"][round(r["x2"],8)]})-({registry["x"][round(r["x1"],8)]})',d=f'({registry["y"][round(r["y2"],8)]})-({registry["y"][round(r["y1"],8)]})')
 data=dict(parameters=v,walls=merged,raw_wall_count=len(raw),rooms=rooms,corridors=corridors,elevator_nodes=cores,stairs=stairs,doors=doors,references=references,freight_shafts=freight,waiting_bays=waits,transfer=transfer,plenums=plenums,main_envelope_m=[v['MainWidth'],v['MainDepth']],maximum_envelope_m=[v['MaxWidth'],v['MainDepth']],bounds=dict(x1=-v['ExternalReach'],y1=0,x2=v['MainWidth']+v['ExternalReach'],y2=v['MainDepth']))
 data['routes']=make_routes(data);return data
def make_routes(d):
 v=d['parameters'];nodes={};edges=[]
 def node(n,x,y,role,zone=None):nodes[n]=dict(x=x,y=y,role=role,zone=zone);return n
 def edge(a,b,kind):
  dx,dy=nodes[a]['x']-nodes[b]['x'],nodes[a]['y']-nodes[b]['y'];distance=math.hypot(dx,dy) if kind=='waiting' else abs(dx)+abs(dy)
  edges.append(dict(a=a,b=b,kind=kind,length=distance))
 for zone in ['SW','SE','NW','NE']:
  right=zone.endswith('E');north=zone.startswith('N');zx=v['EastZoneX'] if right else 0;zy=v['NorthZoneY'] if north else 0;ox=v['MainWidth']+1.2 if right else -1.2
  fy=zy+v['RoomDepth']+v['PersonnelCorridor']+v['RoomDepth']/2;foyer=node(zone+'_Foyer',ox,fy,'foyer',zone);lift=node(zone+'_Lift',v['MainWidth']+3.65 if right else -3.65,fy,'lift',zone);edge(foyer,lift,'daily')
  sy=v['CenterY']+(1 if north else -1)*(v['StairWidth']/2-v['Wall']/2);sx=v['MainWidth']-v['StairLandingXWest'] if right else v['StairLandingXWest']
  approach=node(zone+'_StairApproach',ox,sy,'stair_entry',zone);landing=node(('East' if right else 'West')+'_StairLanding',sx,v['CenterY'],'stair')
  corner=node(zone+'_StairLandingCorner',sx,sy,'stair_entry',zone);edge(approach,corner,'emergency');edge(corner,landing,'emergency')
  for ci in range(2):
   cy=zy+ci*v['RowPitch']+v['RoomDepth']+v['PersonnelCorridor']/2
   points=[node(f'{zone}_C{ci}_{col}',zx+col*v['RoomPitch']+v['RoomWidth']/2,cy,'personnel',zone) for col in range(4)]
   inner=node(f'{zone}_C{ci}_Inner',zx+v['Wall']/2 if right else zx+v['ZoneWidth']-v['Wall']/2,cy,'controlled',zone);outer=node(f'{zone}_C{ci}_Outer',ox,cy,'foyer',zone)
   ordered=sorted(points+[inner,outer],key=lambda n:nodes[n]['x'])
   for a,b in zip(ordered,ordered[1:]):edge(a,b,'daily')
   edge(outer,foyer,'daily');edge(outer,approach,'emergency')
   m=node(f'{zone}_C{ci}_Spine',v['CenterX'],cy,'machine');edge(inner,m,'emergency')
  for r in [r for r in d['rooms'] if r['zone']==zone]:
   rn=node(r['id'],(r['x1']+r['x2'])/2,(r['y1']+r['y2'])/2,'room',zone)
   if r['south_door']:edge(rn,f'{zone}_C{r["row"]-1}_{r["col"]}','daily')
   if r['north_door']:edge(rn,f'{zone}_C{r["row"]}_{r["col"]}','daily')
 cx,cy=v['CenterX'],v['CenterY'];bo=v['BypassOffset'];core_half=v['CoreWidth']/2
 center=node('TransferCenter',cx,cy,'machine')
 for direction in ['N','S','W','E']:
  dx,dy={'N':(0,1),'S':(0,-1),'W':(-1,0),'E':(1,0)}[direction]
  px=cx+dx*(core_half+v['PlenumClear']/2);py=cy+dy*(core_half+v['PlenumClear']/2)
  pn=node(direction+'_PlenumCenter',px,py,'machine')
  for sign in [-1,1]:
   a=node(direction+'_BypassOuter_'+str(sign),px+(sign*bo if not dx else 0),py+(sign*bo if dx else 0),'machine')
   b=node(direction+'_BypassInner_'+str(sign),cx+(sign*bo if not dx else 0),cy+(sign*bo if dx else 0),'machine')
   edge(pn,a,'machine');edge(a,b,'machine');edge(b,center,'machine')
  approach=node('F'+direction+'_Approach',cx+dx*bo,cy+dy*bo,'machine')
  car=node('F'+direction,cx+dx*(v['TransferClear']/2+v['FreightOuterDepth']/2),cy+dy*(v['TransferClear']/2+v['FreightOuterDepth']/2),'freight');edge(center,approach,'machine');edge(approach,car,'freight')
 # Spine entry links preserve full 6m outside the locally enlarged core.
 node('NorthSpineEnd',cx,v['MainDepth']-3,'machine');node('SouthSpineEnd',cx,3,'machine')
 for north,pn in [(False,'S_PlenumCenter'),(True,'N_PlenumCenter')]:
  points=[n for n,p in nodes.items() if p['role']=='machine' and abs(p['x']-cx)<1e-8 and ((p['y']<v['ZoneDepth']) if not north else (p['y']>v['NorthZoneY']))]
  if pn not in points:points.append(pn)
  points.sort(key=lambda n:nodes[n]['y'])
  for a,b in zip(points,points[1:]):edge(a,b,'machine')
 for direction,right in [('W',False),('E',True)]:
  n=node(direction+'_CrossEnd',v['MainWidth']-v['StairEmbedded']-v['Wall']-3 if right else v['StairEmbedded']+v['Wall']+3,cy,'machine');edge(n,direction+'_PlenumCenter','machine')
 for r in d['waiting_bays']:
  sx,sy=r['sx'],r['sy'];a=node(r['id']+'_Turn',cx+sx*bo,cy+sy*bo,'waiting_access');b=node(r['id'],cx+sx*v['WaitOffset'],cy+sy*v['WaitOffset'],'waiting')
  edge(center,a,'waiting');edge(a,b,'waiting')
 return dict(nodes=nodes,edges=edges)
def shortest_path(d,start,goal,kinds,disabled=None):
 nodes=d['routes']['nodes'];adj={n:[] for n in nodes};disabled=set(disabled or [])
 for e in d['routes']['edges']:
  if e['kind'] in kinds and e['a'] not in disabled and e['b'] not in disabled:
   adj[e['a']].append((e['b'],e['length']));adj[e['b']].append((e['a'],e['length']))
 queue=[(0,start,[])];seen=set()
 while queue:
  distance,n,path=heapq.heappop(queue)
  if n in seen:continue
  seen.add(n);path=path+[n]
  if n==goal:return dict(length_m=distance,nodes=path)
  for b,length in adj[n]:
   if nodes[b]['role']=='room' and b!=start:continue
   heapq.heappush(queue,(distance+length,b,path))
 return None
def validate_layout(d):
 v=d['parameters'];assert len(d['rooms'])==48 and len(d['corridors'])==8 and len(d['elevator_nodes'])==4 and len(d['stairs'])==2 and len(d['freight_shafts'])==4
 assert len([p for p in d['doors'] if p['kind']=='room'])==64 and len([p for p in d['doors'] if p['kind']=='stair'])==4
 daily=[];egress=[]
 for r in d['rooms']:
  p=shortest_path(d,r['id'],r['zone']+'_Lift',{'daily'});assert p;assert all(d['routes']['nodes'][n]['role']!='room' or n==r['id'] for n in p['nodes']);assert not any(d['routes']['nodes'][n]['role']=='machine' for n in p['nodes']);daily.append(dict(room=r['id'],**p))
  for other in ['SW','SE','NW','NE']:
   if other!=r['zone']:assert shortest_path(d,r['id'],other+'_Lift',{'daily'}) is None
  for side in ['West','East']:
   p=shortest_path(d,r['id'],side+'_StairLanding',{'daily','emergency','machine'});assert p;egress.append(dict(room=r['id'],stair=side,**p))
 nearest=[min((p for p in egress if p['room']==r['id']),key=lambda p:p['length_m']) for r in d['rooms']]
 routes=[];faults=[]
 for entry in ['NorthSpineEnd','SouthSpineEnd','W_CrossEnd','E_CrossEnd']:
  for car in ['FN','FS','FW','FE']:
   p=shortest_path(d,entry,car,{'machine','freight'});assert p;routes.append(dict(entry=entry,car=car,**p))
 for failed in ['FN','FS','FW','FE']:
  remaining=[]
  for entry in ['NorthSpineEnd','SouthSpineEnd','W_CrossEnd','E_CrossEnd']:
   for car in ['FN','FS','FW','FE']:
    if car==failed:continue
    p=shortest_path(d,entry,car,{'machine','freight'},[failed]);assert p;remaining.append(dict(entry=entry,car=car,**p))
  faults.append(dict(disabled=failed,remaining_accessible_routes=remaining))
 radius=math.hypot(v['CarrierWidth'],v['CarrierLength'])/2+v['TurnClearance'];assert 2*radius<v['PlenumClear']
 # 10.0m trial cannot provide a full safety-circle sweep to corner waiting bays.
 # Required diagonal corner throat = shaft half-width + full turn diameter.
 needed=v['FreightOuterWidth']/2+2*radius
 assert v['TransferClear']/2>needed
 return dict(revision='v2',source_commit='c549e7e3cd1328ea1fee249e5d750827d764d823',brief_blob='de2e56eb49dca0c4dd3184c44cef93640affded6',stage='2D_TOPOLOGY_VERIFIED / EVACUATION_DESIGN_OPEN',room_count=48,pod_capacity=960,rooms_per_zone=12,capacity_per_zone=240,room_personnel_doors=64,middle_double_door_rooms=16,
  main_envelope_m=d['main_envelope_m'],maximum_envelope_m=d['maximum_envelope_m'],zone_envelope_m=[v['ZoneWidth'],v['ZoneDepth']],personnel_corridors=8,personnel_clear_m=2.4,machine_spine_clear_m=6,machine_cross_clear_m=4,
  core_outer_m=[v['CoreWidth'],v['CoreWidth']],transfer_clear_m=[v['TransferClear'],v['TransferClear']],freight_cars=4,freight_car_clear_m=[3.2,3.8],freight_shaft_outer_m=[3.6,4.2],freight_doors_m=2.4,core_bypass_openings=8,core_bypass_clear_m=2.4,entry_plenum_clear_depth_m=4,
  waiting_bays=4,waiting_vehicle_m=[1.7,3.1],carrier_envelope_m=[1.7,3.1],payload_m=[1.1,2.3],turn_circle_diameter_m=2*radius,
  trial_10m_corner_circle_margin_m=5-needed,final_corner_circle_margin_m=v['TransferClear']/2-needed,
  core_design_reason='10m trial fails conservative swept-turn-circle route to four corner waiting bays; 11.2m leaves 0.0645m beyond required corner throat, on top of 0.10m vehicle buffer',
  stair_count=2,stair_entries_per_side=2,stair_entry_clear_m=1.8,stair_extra_airlocks=0,stair_third_doors=0,stair_embedded_depth_m=v['StairEmbedded'],stair_external_projection_m=v['StairProjection'],stair_well_outer_m=[v['StairLength'],v['StairWidth']],flight_clear_m=1.8,landing_m=1.8,riser_count=24,risers_per_flight=12,riser_mm=v['Rise']*1000,tread_mm=300,flight_run_m=3.3,
  passenger_nodes=4,passenger_node_envelope_m=[5.1,14.7],passenger_car_clear_m=[2.1,2.4],passenger_shaft_outer_m=[2.5,2.8],passenger_relative_zone_positions_unchanged=True,
  daily_routes=daily,emergency_routes=egress,nearest_stair_routes=nearest,maximum_center_to_nearest_stair_m=max(p['length_m'] for p in nearest),conservative_pod_operation_to_nearest_stair_m=max(p['length_m'] for p in nearest)+10.75,
  all_corridors_reach_own_lift_without_room_transit=True,four_daily_zone_components=True,all_rooms_reach_both_stairs=True,freight_routes=routes,single_car_fault_tests=faults,
  limitations=['horizontal/static geometry only; no evacuation capacity or code approval','carrier model provisional, holonomic translation/rotation assumed; no mechanical wheel/steering design','fire-door sweep, pressurization, fire rating, accessibility, lift capacity and evacuation time unresolved','room-level machine servicing interface remains TBD'])
