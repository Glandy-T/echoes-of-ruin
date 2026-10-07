"""Metre-based 2D floor topology. Shared walls counted once, separate flow graphs."""
import math,heapq
PARAMETERS={'RoomWidth':21.,'RoomDepth':9.5,'Wall':.2,'RoomDoor':1.4,
 'PersonnelCorridor':2.4,'MachineSpine':6.,'MachineCross':4.,'ServiceClear':4.,
 'ConnectorClear':2.4,'ControlDoor':1.8,'ElevatorCarWidth':2.1,'ElevatorCarDepth':2.4,'ElevatorDoor':1.4,
 'FreightCarWidth':3.2,'FreightCarDepth':3.8,'FreightDoor':2.4,
 'CarrierWidth':1.7,'CarrierLength':3.1,'TurnClearance':.1,
 'StoreyHeight':3.8,'FlightWidth':1.8,'StairGap':.2,'LandingLength':1.8,'Tread':.3,'PlanThickness':.001}
DERIVED={'ZoneWidth':'4*RoomWidth-3*Wall','RoomPitch':'RoomWidth-Wall',
 'ZoneDepth':'3*RoomDepth+2*PersonnelCorridor','RowPitch':'RoomDepth+PersonnelCorridor',
 'ServiceStart':'ZoneWidth+MachineSpine','EastZoneX':'ServiceStart+Wall+ServiceClear',
 'NorthZoneY':'ZoneDepth+MachineCross','MainWidth':'EastZoneX+ZoneWidth','MainDepth':'2*ZoneDepth+MachineCross',
 'CrossCenterY':'ZoneDepth+MachineCross/2','SpineCenterX':'ZoneWidth+MachineSpine/2',
 'Rise':'StoreyHeight/Risers','FlightRun':'(Risers/2-1)*Tread',
 'StairLength':'2*LandingLength+FlightRun+2*Wall','StairWidth':'2*FlightWidth+StairGap+2*Wall',
 'ExternalReach':'ConnectorClear+StairLength','MaxWidth':'MainWidth+2*ExternalReach',
 'ElevatorOuterWidth':'ElevatorCarWidth+2*Wall','ElevatorOuterDepth':'ElevatorCarDepth+2*Wall',
 'FreightOuterWidth':'FreightCarWidth+2*Wall','FreightOuterDepth':'FreightCarDepth+2*Wall'}

def merge_rectangles(rects):
 """Non-overlapping exact orthogonal union; preserves all opening voids."""
 ys=sorted({round(r[k],8) for r in rects for k in ['y1','y2']});out=[];previous={}
 for ya,yb in zip(ys,ys[1:]):
  ym=(ya+yb)/2;ranges=sorted((round(r['x1'],8),round(r['x2'],8)) for r in rects if r['y1']<ym<r['y2'])
  merged=[]
  for a,b in ranges:
   if merged and a<=merged[-1][1]+1e-8:merged[-1][1]=max(b,merged[-1][1])
   else:merged.append([a,b])
  current={}
  for a,b in merged:
   key=(a,b)
   if key in previous:
    item=previous[key];item['y2']=yb
   else:item=dict(x1=a,y1=ya,x2=b,y2=yb);out.append(item)
   current[key]=item
  previous=current
 return out

def build_layout(overrides=None):
 v=dict(PARAMETERS);v['Risers']=24;v.update(overrides or {})
 for k,e in DERIVED.items():v[k]=eval(e,{'__builtins__':{}},v)
 walls=[];doors=[];rooms=[];corridors=[];cores=[];stairs=[];references=[]
 registry={'x':{},'y':{}}
 def val(e):return float(eval(str(e),{'__builtins__':{}},v))
 def coord(e,axis):
  n=val(e);registry[axis].setdefault(round(n,8),str(e));return n
 def rect(x,y,w,d,tag):
  a,b=coord(x,'x'),coord(y,'y');c,f=coord(f'({x})+({w})','x'),coord(f'({y})+({d})','y')
  assert c>a+1e-8 and f>b+1e-8,(tag,x,y,w,d)
  return dict(x1=a,y1=b,x2=c,y2=f,tag=tag,expressions=dict(x=str(x),y=str(y),w=str(w),d=str(d)))
 def wall(x,y,w,d,tag):walls.append(rect(x,y,w,d,tag))
 def portal(orientation,x,y,width,kind,zone=None,name=None):
  doors.append(dict(id=name or f'D{len(doors)+1:03}',orientation=orientation,x=val(x),y=val(y),width=val(width),kind=kind,zone=zone))
 def hwall(x,y,length,opening,tag,kind,zone=None):
  if opening:
   wall(x,y,f'(({length})-({opening}))/2','Wall',tag)
   wall(f'({x})+(({length})+({opening}))/2',y,f'(({length})-({opening}))/2','Wall',tag)
   portal('H',f'({x})+({length})/2',f'({y})+Wall/2',opening,kind,zone)
  else:wall(x,y,length,'Wall',tag)
 def vwall(x,y,length,opening,tag,kind,zone=None):
  if opening:
   wall(x,y,'Wall',f'(({length})-({opening}))/2',tag)
   wall(x,f'({y})+(({length})+({opening}))/2','Wall',f'(({length})-({opening}))/2',tag)
   portal('V',f'({x})+Wall/2',f'({y})+({length})/2',opening,kind,zone)
  else:wall(x,y,'Wall',length,tag)
 zones=[('SW','0','0',False),('SE','EastZoneX','0',True),('NW','0','NorthZoneY',False),('NE','EastZoneX','NorthZoneY',True)]
 for zone,zx,zy,right in zones:
  for row in range(3):
   for col in range(4):
    x=f'({zx})+{col}*RoomPitch';y=f'({zy})+{row}*RowPitch'
    south=row==1 or (row==2) or (row==0 and zone.startswith('N') is False and False)
    # Outer rows open only toward the adjacent personnel corridor, never toward machine cross.
    south=row in [1,2];north=row in [0,1]
    room=rect(x,y,'RoomWidth','RoomDepth',zone+'_Room');room.update(id=f'{zone}-{row*4+col+1:02}',zone=zone,row=row,col=col,capacity=20,south_door=south,north_door=north);rooms.append(room)
    hwall(x,y,'RoomWidth','RoomDoor' if south else None,room['id'],'room',zone)
    hwall(x,f'({y})+RoomDepth-Wall','RoomWidth','RoomDoor' if north else None,room['id'],'room',zone)
    wall(x,f'({y})+Wall','Wall','RoomDepth-2*Wall',room['id'])
    wall(f'({x})+RoomWidth-Wall',f'({y})+Wall','Wall','RoomDepth-2*Wall',room['id'])
  for ci in range(2):
   cy=f'({zy})+{ci}*RowPitch+RoomDepth'
   corridor=rect(f'({zx})+Wall',cy,'ZoneWidth-2*Wall','PersonnelCorridor',zone+'_Corridor');corridor.update(id=f'{zone}-C{ci+1}',zone=zone,center_y=val(cy)+v['PersonnelCorridor']/2);corridors.append(corridor)
   # Inner ends are controlled emergency doors; outer ends connect directly to the node.
   inside_x=zx if right else f'({zx})+ZoneWidth-Wall'
   vwall(inside_x,cy,'PersonnelCorridor','ControlDoor',zone+'_ControlledInner','emergency',zone)
  # Two corridor ends connect to one enclosed exterior vertical foyer, independently of rooms.
  # Left geometry is mirrored about the building width for right-side nodes.
  def mx(x,w='0'):return f'MainWidth-({x})-({w})' if right else x
  core_y=f'({zy})+RoomDepth-Wall';core_d='RoomDepth+2*PersonnelCorridor+2*Wall'
  core=rect(mx('-ConnectorClear-ElevatorOuterWidth','ConnectorClear+ElevatorOuterWidth+Wall'),core_y,'ConnectorClear+ElevatorOuterWidth+Wall',core_d,zone+'_ElevatorNode')
  core.update(id=zone+'_ElevatorNode',zone=zone,car_clear_m=[v['ElevatorCarWidth'],v['ElevatorCarDepth']],connector_clear_m=v['ConnectorClear'],shaft_outer_m=[v['ElevatorOuterWidth'],v['ElevatorOuterDepth']]);cores.append(core)
  lift_cy=f'({zy})+RoomDepth+PersonnelCorridor+RoomDepth/2'
  lift_y=f'({lift_cy})-ElevatorOuterDepth/2'
  # Shared shaft/foyer wall at x=-ConnectorClear-Wall..-ConnectorClear.
  hwall(mx('-ConnectorClear-ElevatorOuterWidth','ElevatorOuterWidth'),lift_y,'ElevatorOuterWidth',None,zone+'_LiftShaft','none')
  hwall(mx('-ConnectorClear-ElevatorOuterWidth','ElevatorOuterWidth'),f'({lift_y})+ElevatorOuterDepth-Wall','ElevatorOuterWidth',None,zone+'_LiftShaft','none')
  wall(mx('-ConnectorClear-ElevatorOuterWidth','Wall'),f'({lift_y})+Wall','Wall','ElevatorCarDepth',zone+'_LiftShaft')
  vwall(mx('-ConnectorClear-Wall','Wall'),f'({lift_y})+Wall','ElevatorCarDepth','ElevatorDoor',zone+'_LiftDoor','elevator',zone)
  car=rect(mx('-ConnectorClear-ElevatorOuterWidth+Wall','ElevatorCarWidth'),f'({lift_y})+Wall','ElevatorCarWidth','ElevatorCarDepth','passenger_car');car.update(zone=zone);references.append(car)
  # Foyer upper/lower controlled barriers keep the four nodes separate in daily use.
  hwall(mx('-ConnectorClear-Wall','ConnectorClear+2*Wall'),core_y,'ConnectorClear+2*Wall','ControlDoor',zone+'_OuterGate','emergency',zone)
  hwall(mx('-ConnectorClear-Wall','ConnectorClear+2*Wall'),f'({zy})+2*RowPitch+Wall','ConnectorClear+2*Wall','ControlDoor',zone+'_OuterGate','emergency',zone)
  # Exterior connector boundary; remove the part shared with the lift shaft.
  wall(mx('-ConnectorClear-Wall','Wall'),f'({zy})+RoomDepth','Wall',f'({lift_y})-(({zy})+RoomDepth)',zone+'_ConnectorWall')
  wall(mx('-ConnectorClear-Wall','Wall'),f'({lift_y})+ElevatorOuterDepth','Wall',f'(({zy})+2*RowPitch)-(({lift_y})+ElevatorOuterDepth)',zone+'_ConnectorWall')
 # Outer closed emergency links and four-door stair airlocks.
 for side,right in [('West',False),('East',True)]:
  def mx(x,w='0'):return f'MainWidth-({x})-({w})' if right else x
  # Continuous side gallery from the two outer corridor nodes to the emergency stair.
  for y,d in [('RoomDepth+2*PersonnelCorridor+RoomDepth+Wall','ZoneDepth-(RoomDepth+2*PersonnelCorridor+RoomDepth+Wall)'),('NorthZoneY','RoomDepth-Wall')]:
   wall(mx('-ConnectorClear-Wall','Wall'),y,'Wall',d,side+'_EmergencyLinkBoundary')
  hwall(mx('-ConnectorClear-Wall','ConnectorClear+2*Wall'),'ZoneDepth-Wall','ConnectorClear+2*Wall','ControlDoor',side+'_StairAirlockSouth','emergency')
  hwall(mx('-ConnectorClear-Wall','ConnectorClear+2*Wall'),'NorthZoneY','ConnectorClear+2*Wall','ControlDoor',side+'_StairAirlockNorth','emergency')
  # Foyer west boundary is the shared east wall of the stair enclosure.
  sy='CrossCenterY-StairWidth/2';sx='-ConnectorClear-StairLength'
  stair=rect(mx(sx,'StairLength'),sy,'StairLength','StairWidth',side+'_Stair');stair.update(id=side+'_Stair',side=side,flight_width_m=v['FlightWidth'],riser_count=24,rise_m=v['Rise'],tread_m=v['Tread'],flight_run_m=v['FlightRun'],landing_length_m=v['LandingLength'],well_outer_m=[v['StairLength'],v['StairWidth']]);stairs.append(stair)
  hwall(mx(sx,'StairLength'),sy,'StairLength',None,side+'_StairWall','none')
  hwall(mx(sx,'StairLength'),f'({sy})+StairWidth-Wall','StairLength',None,side+'_StairWall','none')
  wall(mx(sx,'Wall'),f'({sy})+Wall','Wall','StairWidth-2*Wall',side+'_StairWall')
  vwall(mx('-ConnectorClear-Wall','Wall'),f'({sy})+Wall','StairWidth-2*Wall','ControlDoor',side+'_StairDoor','emergency')
  # Close small gallery/stair junctions outside the controlled doorway.
  for yy,dd in [('ZoneDepth','(CrossCenterY-ControlDoor/2)-ZoneDepth'),('CrossCenterY+ControlDoor/2','NorthZoneY-(CrossCenterY+ControlDoor/2)')]:
   wall(mx('-ConnectorClear-Wall','Wall'),yy,'Wall',dd,side+'_AirlockBoundary')
  for flight in range(2):
   ref=rect(mx('-ConnectorClear-Wall-LandingLength-FlightRun','FlightRun'),f'({sy})+Wall+{flight}*(FlightWidth+StairGap)','FlightRun','FlightWidth','stair_flight');ref.update(side=side,flight=flight);references.append(ref)
 # Top/bottom spine/service closure, and outer machine-cross ends with controlled fire doors.
 wall('ZoneWidth','0','EastZoneX-ZoneWidth','Wall','CentralSouthBoundary')
 wall('ZoneWidth','MainDepth-Wall','EastZoneX-ZoneWidth','Wall','CentralNorthBoundary')
 vwall('0','ZoneDepth','MachineCross','ControlDoor','WestMachineFireDoor','emergency')
 vwall('MainWidth-Wall','ZoneDepth','MachineCross','ControlDoor','EastMachineFireDoor','emergency')
 # 4m clear service strip east of 6m spine; emergency bridges do not become daily corridors.
 cuts=[]
 for corridor in corridors:
  if corridor['zone'] in ['SE','NE']:
   yc=corridor['center_y'];cuts.append((yc-v['ControlDoor']/2,yc+v['ControlDoor']/2,'emergency'))
   for yy in [corridor['y1']-v['Wall'],corridor['y2']]:wall('ServiceStart',str(yy),'Wall+ServiceClear','Wall','ControlledServiceBridge')
 # Freight bay immediately north-east of the 6x4 intersection.
 lobby_y='NorthZoneY+Wall';lobby_cy='NorthZoneY+Wall+ServiceClear/2'
 cuts.append((val(lobby_cy)-v['FreightDoor']/2,val(lobby_cy)+v['FreightDoor']/2,'freight'))
 for lo,hi in [('0','ZoneDepth'),('NorthZoneY','MainDepth')]:
  cursor=val(lo)
  for a,b,kind in sorted(cuts):
   if a<val(lo) or b>val(hi):continue
   if a>cursor:wall('ServiceStart',str(cursor),'Wall',str(a-cursor),'ServiceSpinePartition')
   portal('V','ServiceStart+Wall/2',str((a+b)/2),str(b-a),kind)
   cursor=b
  if cursor<val(hi):wall('ServiceStart',str(cursor),'Wall',str(val(hi)-cursor),'ServiceSpinePartition')
 # Registry for piecewise partition ends must retain parameter expressions, not constants.
 for corridor in corridors:
  if corridor['zone'] in ['SE','NE']:
   cy=f'{"NorthZoneY+" if corridor["zone"]=="NE" else ""}{0 if corridor["id"].endswith("1") else 1}*RowPitch+RoomDepth+PersonnelCorridor/2'
   for sign in [-1,1]:registry['y'][round(corridor['center_y']+sign*v['ControlDoor']/2,8)]=f'({cy})+({sign})*ControlDoor/2'
 for sign in [-1,1]:registry['y'][round(val(lobby_cy)+sign*v['FreightDoor']/2,8)]=f'({lobby_cy})+({sign})*FreightDoor/2'
 hwall('ServiceStart', 'NorthZoneY','Wall+ServiceClear',None,'FreightLobbySouthWall','none')
 fx='ServiceStart+Wall+(ServiceClear-FreightOuterWidth)/2';fy='NorthZoneY+Wall+ServiceClear'
 hwall(fx,fy,'FreightOuterWidth','FreightDoor','FreightShaftFront','freight')
 hwall(fx,f'({fy})+FreightOuterDepth-Wall','FreightOuterWidth',None,'FreightShaftRear','none')
 wall(fx,f'({fy})+Wall','Wall','FreightCarDepth','FreightShaftSide')
 wall(f'({fx})+FreightOuterWidth-Wall',f'({fy})+Wall','Wall','FreightCarDepth','FreightShaftSide')
 freight=rect(fx,fy,'FreightOuterWidth','FreightOuterDepth','freight_shaft')
 freight['car_clear_m']=[v['FreightCarWidth'],v['FreightCarDepth']]
 lobby=rect('ServiceStart+Wall',lobby_y,'ServiceClear','ServiceClear','freight_lobby')
 car=rect(f'({fx})+Wall',f'({fy})+Wall','FreightCarWidth','FreightCarDepth','freight_car');references.append(car)
 # Exterior east/west room/corridor boundary gaps are deliberately portals to the four elevator foyers.
 merged=merge_rectangles(walls)
 for i,r in enumerate(merged):
  r['id']=f'W{i+1:03}';r['expressions']=dict(x=registry['x'][round(r['x1'],8)],y=registry['y'][round(r['y1'],8)],
   w=f'({registry["x"][round(r["x2"],8)]})-({registry["x"][round(r["x1"],8)]})',
   d=f'({registry["y"][round(r["y2"],8)]})-({registry["y"][round(r["y1"],8)]})')
 data=dict(parameters=v,rooms=rooms,corridors=corridors,elevator_nodes=cores,stairs=stairs,doors=doors,walls=merged,raw_wall_count=len(walls),
  references=references,freight_shaft=freight,freight_lobby=lobby,service_strip_clear=dict(x1=v['ServiceStart']+v['Wall'],x2=v['EastZoneX'],y1=v['Wall'],y2=v['MainDepth']-v['Wall']),
  main_envelope_m=[v['MainWidth'],v['MainDepth']],maximum_envelope_m=[v['MaxWidth'],v['MainDepth']],bounds=dict(x1=-v['ExternalReach'],y1=0,x2=v['MainWidth']+v['ExternalReach'],y2=v['MainDepth']))
 data['routes']=make_routes(data)
 return data

def make_routes(data):
 v=data['parameters'];nodes={};edges=[]
 def node(name,x,y,role,zone=None):nodes[name]=dict(x=x,y=y,role=role,zone=zone);return name
 def edge(a,b,kind):edges.append(dict(a=a,b=b,kind=kind,length=abs(nodes[a]['x']-nodes[b]['x'])+abs(nodes[a]['y']-nodes[b]['y'])))
 for zone in ['SW','SE','NW','NE']:
  right=zone.endswith('E');zx=v['EastZoneX'] if right else 0;zy=v['NorthZoneY'] if zone.startswith('N') else 0
  outer_x=v['MainWidth']+v['ConnectorClear']/2 if right else -v['ConnectorClear']/2
  elev_y=zy+v['RoomDepth']+v['PersonnelCorridor']+v['RoomDepth']/2
  outer_mid=node(zone+'_Foyer',outer_x,elev_y,'foyer',zone)
  elev_x=v['MainWidth']+v['ConnectorClear']+v['Wall']+v['ElevatorCarWidth']/2 if right else -(v['ConnectorClear']+v['Wall']+v['ElevatorCarWidth']/2)
  elevator=node(zone+'_Lift',elev_x,elev_y,'lift',zone);edge(outer_mid,elevator,'daily')
  for ci in range(2):
   cy=zy+ci*v['RowPitch']+v['RoomDepth']+v['PersonnelCorridor']/2
   points=[]
   for col in range(4):points.append(node(f'{zone}_C{ci}_{col}',zx+col*v['RoomPitch']+v['RoomWidth']/2,cy,'personnel',zone))
   inner_x=zx+v['Wall']/2 if right else zx+v['ZoneWidth']-v['Wall']/2
   inner=node(f'{zone}_C{ci}_Inner',inner_x,cy,'controlled',zone)
   outer=node(f'{zone}_C{ci}_Outer',outer_x,cy,'foyer',zone)
   ordered=sorted(points+[inner,outer],key=lambda n:nodes[n]['x'])
   for a,b in zip(ordered,ordered[1:]):edge(a,b,'daily')
   edge(outer,outer_mid,'daily')
   machine=node(f'{zone}_C{ci}_Spine',v['SpineCenterX'],cy,'machine')
   edge(inner,machine,'emergency')
   airlock=node(('East' if right else 'West')+'_Airlock',outer_x,v['CrossCenterY'],'airlock')
   edge(outer,airlock,'emergency')
  for room in [r for r in data['rooms'] if r['zone']==zone]:
   rn=node(room['id'],(room['x1']+room['x2'])/2,(room['y1']+room['y2'])/2,'room',zone)
   if room['south_door']:edge(rn,f'{zone}_C{room["row"]-1}_{room["col"]}','daily')
   if room['north_door']:edge(rn,f'{zone}_C{room["row"]}_{room["col"]}','daily')
 # Continuous 6m spine connects the controlled emergency links and the freight bay.
 center=node('MachineCrossCenter',v['SpineCenterX'],v['CrossCenterY'],'machine')
 freight_y=v['NorthZoneY']+v['Wall']+v['ServiceClear']/2
 gate=node('FreightSpineJunction',v['SpineCenterX'],freight_y,'machine')
 spine_points=[name for name,p in nodes.items() if p['role']=='machine' and abs(p['x']-v['SpineCenterX'])<1e-7]
 spine_points.sort(key=lambda n:nodes[n]['y'])
 for a,b in zip(spine_points,spine_points[1:]):edge(a,b,'machine')
 for side,right in [('West',False),('East',True)]:
  foyer=side+'_Airlock';edge(center,foyer,'machine')
  stair_x=v['MainWidth']+v['ConnectorClear']+v['Wall']+v['LandingLength']/2 if right else -(v['ConnectorClear']+v['Wall']+v['LandingLength']/2)
  stair=node(side+'_StairLanding',stair_x,v['CrossCenterY'],'stair');edge(foyer,stair,'emergency')
 lobby=data['freight_lobby'];fc=data['freight_shaft']
 lobby_center=node('FreightLobby',(lobby['x1']+lobby['x2'])/2,(lobby['y1']+lobby['y2'])/2,'freight')
 shaft_center=node('FreightCar',(fc['x1']+fc['x2'])/2,(fc['y1']+fc['y2'])/2,'freight')
 edge(gate,lobby_center,'freight');edge(lobby_center,shaft_center,'freight')
 return dict(nodes=nodes,edges=edges)

def shortest_path(data,start,goal,kinds):
 nodes=data['routes']['nodes'];adj={name:[] for name in nodes}
 for e in data['routes']['edges']:
  if e['kind'] in kinds:
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

def validate_layout(data):
 v=data['parameters'];assert len(data['rooms'])==48 and len(data['corridors'])==8 and len(data['elevator_nodes'])==4 and len(data['stairs'])==2
 roomdoors=[d for d in data['doors'] if d['kind']=='room'];assert len(roomdoors)==64
 assert sum(r['south_door'] and r['north_door'] for r in data['rooms'])==16
 assert all(abs(c['y2']-c['y1']-2.4)<1e-7 for c in data['corridors'])
 daily=[];egress=[]
 for r in data['rooms']:
  route=shortest_path(data,r['id'],r['zone']+'_Lift',{'daily'});assert route
  assert not any(data['routes']['nodes'][n]['role']=='machine' for n in route['nodes'])
  assert all(data['routes']['nodes'][n]['role']!='room' or n==r['id'] for n in route['nodes'])
  daily.append(dict(room=r['id'],**route))
  for side in ['West','East']:
   route=shortest_path(data,r['id'],side+'_StairLanding',{'daily','emergency','machine'});assert route
   egress.append(dict(room=r['id'],stair=side,**route))
  for other in ['SW','SE','NW','NE']:
   if other!=r['zone']:assert shortest_path(data,r['id'],other+'_Lift',{'daily'}) is None
 shortest_egress=[min((p for p in egress if p['room']==r['id']),key=lambda p:p['length_m']) for r in data['rooms']]
 for c in data['corridors']:
  zi=c['zone'];ci=0 if c['id'].endswith('1') else 1
  # Corridor-to-lift checks start at the corridor itself, not inside a two-door room.
  route=shortest_path(data,f'{zi}_C{ci}_Inner',zi+'_Lift',{'daily'});assert route
 payload_diagonal=math.hypot(v['CarrierWidth'],v['CarrierLength']);turn_diameter=payload_diagonal+2*v['TurnClearance']
 assert turn_diameter<v['MachineCross'] and turn_diameter<v['ServiceClear']
 machine=shortest_path(data,'MachineCrossCenter','FreightCar',{'machine','freight'});assert machine
 return dict(room_count=48,pod_capacity=960,rooms_per_zone=12,capacity_per_zone=240,room_personnel_doors=64,middle_double_door_rooms=16,
  ordinary_corridors=8,ordinary_corridor_clear_m=2.4,machine_spine_clear_m=6,machine_cross_clear_m=4,
  main_envelope_m=data['main_envelope_m'],maximum_envelope_m=data['maximum_envelope_m'],
  base_without_service_strip_m=[172.8,70.6],service_strip_added_width_m=v['ServiceClear']+v['Wall'],
  daily_routes=daily,emergency_routes=egress,shortest_emergency_route_per_room=shortest_egress,
  maximum_room_center_to_nearest_stair_m=max(p['length_m'] for p in shortest_egress),
  conservative_pod_operation_to_nearest_stair_m=max(p['length_m'] for p in shortest_egress)+10.75,
  travel_distance_reference='horizontal centerline route from room center to stair entrance landing; pod-operation value adds 2.90m to cross aisle +7.85m lateral approach, assumes exit through room cross aisle',
  four_daily_zone_components=True,both_corridors_reach_own_lift_without_room_transit=True,
  daily_personnel_separated_from_machine=True,all_rooms_reach_both_stairs_in_emergency_graph=True,
  carrier_envelope_m=[v['CarrierWidth'],v['CarrierLength']],payload_m=[1.1,2.3],carrier_assumption='0.30m width buffer each side; 0.80m total length allowance for transport equipment; PROVISIONAL',
  turn_circle_diameter_m=turn_diameter,turn_circle_margin_to_4m_each_side_m=(4-turn_diameter)/2,
  freight_car_clear_m=[v['FreightCarWidth'],v['FreightCarDepth']],freight_shaft_outer_m=[v['FreightOuterWidth'],v['FreightOuterDepth']],freight_lobby_clear_m=[4,4],machine_route_to_freight=machine,
  stair_risers=24,flight_risers=12,riser_m=v['Rise'],tread_m=v['Tread'],flight_run_m=v['FlightRun'],landing_m=v['LandingLength'],flight_clear_m=1.8,
  stair_well_outer_m=[v['StairLength'],v['StairWidth']],test_fire_door_width_m=1.8,fire_door_leaves_m=[.9,.9],
  passenger_car_clear_m=[v['ElevatorCarWidth'],v['ElevatorCarDepth']],passenger_shaft_outer_m=[v['ElevatorOuterWidth'],v['ElevatorOuterDepth']],elevator_node_envelope_m=[5.1,14.7],
  geometry_scope='2D floor topology and static clearance; emergency graph connectivity does not establish evacuation capacity or regulatory travel-distance acceptance',
  unresolved=['about 107m center-to-nearest-stair / about 118m conservative pod-operation route is long and requires dedicated evacuation design review','960 occupants / lift capacity / evacuation timing / accessibility / final fire separation not validated','room machine service and pod replacement interfaces TBD'])
