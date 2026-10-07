"""A2 publication pages from exactly the native 2D floor data, dimensions in metres."""
import math,xml.etree.ElementTree as ET
BLUE='#25618a'; ORANGE='#aa6126'; MACHINE='#6b757b'
def text(p,x,y,s,size=3.2,anchor='start',color='#222'):
 p['items'].append(dict(k='text',x=x,y=y,s=str(s),size=size,anchor=anchor,color=color))
def line(p,x1,y1,x2,y2,lw=.15,color='#222',dash=False):
 p['items'].append(dict(k='line',x1=x1,y1=y1,x2=x2,y2=y2,lw=lw,color=color,dash=dash))
def rect(p,x,y,w,h,lw=.15,fill='none',color='#222',dash=False):
 p['items'].append(dict(k='rect',x=x,y=y,w=w,h=h,lw=lw,fill=fill,color=color,dash=dash))
def circle(p,x,y,r,lw=.15,fill='none',color='#222',dash=False):
 p['items'].append(dict(k='circle',x=x,y=y,r=r,lw=lw,fill=fill,color=color,dash=dash))
def arrow(p,pts,color=BLUE,dash=False,lw=.3):
 for a,b in zip(pts,pts[1:]):line(p,*a,*b,lw,color,dash)
 a,b=pts[-2:];ang=math.atan2(b[1]-a[1],b[0]-a[0])
 for off in [-.5,.5]:line(p,*b,b[0]-2.3*math.cos(ang+off),b[1]-2.3*math.sin(ang+off),lw,color)
def dimh(p,x1,x2,y,s,fy=None,size=2.8):
 line(p,x1,y,x2,y,.12)
 for x in [x1,x2]:
  line(p,x-.9,y+.9,x+.9,y-.9,.2)
  if fy is not None:line(p,x,fy,x,y+1.8 if y<fy else y-1.8,.1,'#888')
 text(p,(x1+x2)/2,y-1.8,s,size,'middle')
def dimv(p,y1,y2,x,s,fx=None,size=2.8):
 line(p,x,y1,x,y2,.12)
 for y in [y1,y2]:
  line(p,x-.9,y+.9,x+.9,y-.9,.2)
  if fx is not None:line(p,fx,y,x,y,.1,'#888')
 text(p,x-2,(y1+y2)/2+1,s,size,'end')
def page(code,title,scale):
 p=dict(code=code,title=title,scale=scale,items=[])
 rect(p,12,12,570,396,.3);text(p,22,27,title,5);text(p,572,27,code,5,'end')
 line(p,12,34,582,34,.25);line(p,12,388,582,388,.25)
 text(p,22,399,'Echoes of Ruin | 标准休眠层 v3 | P = 暂定 / 仅二维工程验证',3)
 text(p,572,399,scale+' | A2原尺寸 | 2026-10-07',3,'end');return p
def mapper(px,py,scale,bounds):
 q=1000/scale;return lambda x,y:(px+(x-bounds[0])*q,py+(bounds[3]-y)*q),q
def draw_plan(p,d,xy,q,bounds,labels=True,flow=False,omit_core=False):
 x1,y1,x2,y2=bounds;v=d['parameters']
 def fill(r,col,stroke='#aaa',lw=.08):
  a,b=max(x1,r['x1']),max(y1,r['y1']);c,f=min(x2,r['x2']),min(y2,r['y2'])
  if c>a and f>b:
   xx,yy=xy(a,f);rect(p,xx,yy,(c-a)*q,(f-b)*q,lw,col,stroke)
 for r in d.get('floor_cells',[]):fill(r,'#ffffff','#ffffff',0)
 for r in d.get('floor_cells',[]):fill(r,'#ffffff','#ffffff',0)
 for r in d['corridors']:fill(r,'#eaf1f6',BLUE)
 for r in d['elevator_nodes']:fill(r,'#f1f6f9',BLUE)
 if not omit_core:
  for r in d['plenums']+[d['transfer']]:fill(r,'#f3f5f2',MACHINE)
 for r in d['references']:
  if not omit_core or r['tag'] not in ['freight_car']:fill(r,'#ededeb','#777',.12)
 for r in d['waiting_bays']:
  fill(r,'#dae6d6','#829379',.15)
  if x1<r['x1']<x2 and y1<r['y1']<y2:text(p,*xy((r['x1']+r['x2'])/2,(r['y1']+r['y2'])/2),'Q',2.2 if q<3 else 3,'middle','#50604a')
 for w in d['walls']:
  if omit_core and w['x1']>=v['ZoneWidth']-1e-8 and w['y2']>v['ZoneDepth']-v['PlenumClear']-v['Wall']+1e-8:continue
  fill(w,'#333','#333')
 for door in d['doors']:
  x,y,a=door['x'],door['y'],door['width']/2
  if not (x1<=x<=x2 and y1<=y<=y2):continue
  if door['kind']=='machine_portal':continue
  col=BLUE if door['kind'] in ['room','elevator'] else '#b12828' if door['kind']=='personnel_exclusion' else '#b12828' if door['kind']=='personnel_exclusion' else ORANGE if door['kind'] in ['emergency','stair'] else MACHINE
  ends=[xy(x-a,y),xy(x+a,y)] if door['orientation']=='H' else [xy(x,y-a),xy(x,y+a)]
  line(p,*ends[0],*ends[1],.16,col,True)
  if door['kind']=='stair':
   # Open double leaves point into the landing, away from exterior approach.
   towards=1 if door['tag'].startswith('North_') else -1 if door['tag'].startswith('South_') else 1 if y<v['CenterY'] else -1
   for xx in [x-a,x+a]:line(p,*xy(xx,y),*xy(xx,y+towards*a),.10,ORANGE)
 for r in d['freight_shafts']:
  if omit_core:continue
  if x1<=r['x1']<=x2 and y1<=r['y1']<=y2:text(p,*xy((r['x1']+r['x2'])/2,(r['y1']+r['y2'])/2),r['id'],2.2 if q<3 else 3.3,'middle',MACHINE)
 if labels:
  for r in d['rooms']:
   if r['x1']<x2 and r['x2']>x1 and r['y1']<y2 and r['y2']>y1:
    xx,yy=xy((r['x1']+r['x2'])/2,(r['y1']+r['y2'])/2);text(p,xx,yy-1,r['id'],2.8 if q<3 else 3.6,'middle');text(p,xx,yy+3,'20人',2.4 if q<3 else 2.8,'middle','#666')
 if flow:
  for e in d['routes']['edges']:
   a=d['routes']['nodes'][e['a']];b=d['routes']['nodes'][e['b']]
   if a['role']=='room' or b['role']=='room' or e['length']<1e-8:continue
   if not all(x1<=pt['x']<=x2 and y1<=pt['y']<=y2 for pt in [a,b]):continue
   col=BLUE if e['kind']=='daily' else ORANGE if e['kind'] in ['emergency','evacuation_outward'] else MACHINE
   line(p,*xy(a['x'],a['y']),*xy(b['x'],b['y']),.22 if q<3 else .28,col,e['kind']!='daily')
def legend(p,x,y):
 for i,(col,dash,s) in enumerate([(BLUE,False,'日常人员 / 本区外侧电梯'),(ORANGE,True,'应急人员 / 四向楼梯、核心禁入'),(MACHINE,True,'机器物流 / 四向绕行入中央核心')]):
  line(p,x,y+i*8,x+16,y+i*8,.35,col,dash);text(p,x+21,y+1+i*8,s,3)
def background(p,xy,q,bounds):
 xx,yy=xy(bounds[0],bounds[3]);rect(p,xx,yy,(bounds[2]-bounds[0])*q,(bounds[3]-bounds[1])*q,0,'#f1f1f1','#f1f1f1')

def treads(p,d,xy,q,side):
 for r in d['references']:
  if r['tag']!='stair_flight' or r.get('side')!=side:continue
  for i in range(1,11):
   if r['axis']=='Y':line(p,*xy(r['x1'],r['y1']+i*.3),*xy(r['x2'],r['y1']+i*.3),.13,'#666')
   else:line(p,*xy(r['x1']+i*.3,r['y1']),*xy(r['x1']+i*.3,r['y2']),.13,'#666')

def background(p,xy,q,bounds):
 xx,yy=xy(bounds[0],bounds[3]);rect(p,xx,yy,(bounds[2]-bounds[0])*q,(bounds[3]-bounds[1])*q,0,'#f1f1f1','#f1f1f1')

def treads(p,d,xy,q,side):
 for r in d['references']:
  if r['tag']!='stair_flight' or r.get('side')!=side:continue
  for i in range(1,11):
   if r['axis']=='Y':line(p,*xy(r['x1'],r['y1']+i*.3),*xy(r['x2'],r['y1']+i*.3),.13,'#666')
   else:line(p,*xy(r['x1']+i*.3,r['y1']),*xy(r['x1']+i*.3,r['y2']),.13,'#666')

def make_pages(d,c):
 v=d['parameters'];cx,cy=v['CenterX'],v['CenterY'];pages=[]
 p=page('A401','标准休眠层 v3 / 四向楼梯、局部物流核心与房间错台','1:500');pages.append(p)
 bounds=tuple(d['bounds'][k] for k in ['x1','y1','x2','y2']);xy,q=mapper(50,96,500,bounds);background(p,xy,q,bounds);draw_plan(p,d,xy,q,bounds,True,True)
 dimh(p,xy(bounds[0],0)[0],xy(bounds[2],0)[0],49,f'含外置节点最大宽 {v["MaxWidth"]:.2f} m',96)
 dimh(p,xy(0,0)[0],xy(v['MainWidth'],0)[0],68,f'主体阶梯轮廓包络宽 {v["MainWidth"]:.2f} m',96)
 for a,b,s in [(0,v['ZoneWidth'],'86.00 / 房组+真实连接廊'),(v['ZoneWidth'],v['EastZoneX'],'净6.00'),(v['EastZoneX'],v['MainWidth'],'86.00 / 镜像')]:dimh(p,xy(a,0)[0],xy(b,0)[0],83,s,96,2.5)
 dimv(p,96,96+v['MaxDepth']*q,32,f'{v["MaxDepth"]:.2f}',50)
 dimv(p,xy(0,v['FloorNorth'])[1],xy(0,v['FloorSouth'])[1],46,f'主体{v["MainDepth"]:.2f}',xy(0,0)[0],2.5)
 for side in ['West','East','North','South']:
  r=next(r for r in d['stairs'] if r['side']==side);x,y=xy((r['x1']+r['x2'])/2,(r['y1']+r['y2'])/2);text(p,x,y,dict(West='西S',East='东S',North='北S',South='南S')[side],3,'middle',ORANGE)
 for zone in ['SW','SE','NW','NE']:
  x=v['MainWidth']+3.65 if zone.endswith('E') else -3.65;y=(v['NorthZoneY'] if zone.startswith('N') else 0)+16.65;text(p,*xy(x,y),'L',2.7,'middle',BLUE)
 for sign in [-1,1]:
  y0=v['NorthZoneY']+v['RoomDepth']+v['PersonnelCorridor']/2+v['NotchDepth'] if sign==1 else v['RoomDepth']+v['PersonnelCorridor']/2+v['RowPitch']-v['NotchDepth']
  y1=v['NorthStairInner']+.1 if sign==1 else v['SouthStairInner']-.1
  arrow(p,[xy(cx-.6,y0),xy(cx-.6,y1)],ORANGE,True,.4)
 for yy in [v['SouthIsolation']+.1,v['NorthIsolation']-.1]:line(p,*xy(cx-3,yy),*xy(cx+3,yy),.6,'#b12828')
 text(p,*xy(cx,cy),'人员禁入',2.8,'middle','#b12828')
 for x in [69,v['MainWidth']-69]:
  for y in [27,v['BaseDepth']-27]:text(p,*xy(x,y),'室外凹口',2.3,'middle','#777')
 text(p,444,111,'v3 / 验证与反算',3.8)
 info=['48室 / 960舱保持','每区3排×4室保持','每区一台人员电梯：接受','外三列共享外包62.60','内一列外包21.00','真实人员连接廊净2.40','内列局部纵向错台11.80','普通机器段：纵6 / 横4','核心19.60仅在中央','转运净11.20×11.20','西/东各2门；北/南各1门','紧急：北段向北/南段向南','纵向段停机；核心对人封闭','浅灰为建筑轮廓外，不是空白带']
 for i,s in enumerate(info):text(p,444,125+i*9.5,s,2.8)
 legend(p,50,312);text(p,270,313,'宽：62.60+2.40+21.00+6.00+镜像 =178.00',2.9)
 text(p,270,326,'深：33.30+4.00+33.30+2×11.80 =94.20',2.9)
 rect(p,50,343,507,34,.18,'#fff8ed',ORANGE)
 text(p,58,352,'最远中心 → 最近楼梯72.25 m；舱侧保守83.00 m；较v2均减少40.50 m（中心35.92%）。',3.1,color=ORANGE)
 text(p,58,362,'最远房SW-11（镜像同值）；经本区外侧人员廊到西梯。48室均有外端/内端两种疏散方向。',2.9)
 text(p,58,372,'容量/时间与防火细节仍待验证；人员电梯按未来高速可靠、分批进入假设接受，不阻止本轮推进。',2.8)
 p=page('A402','典型SW分区 v3 / 房间错台与受控向南疏散','1:200');pages.append(p)
 bounds=(-5.1,v['FloorSouth'],cx+3,33.3);xy,q=mapper(55,105,200,bounds);background(p,xy,q,bounds);draw_plan(p,d,xy,q,bounds,True,False)
 dimh(p,xy(0,0)[0],xy(86,0)[0],52,'86.00 = 外三列62.60 + 真实连接廊2.40 + 内列21.00',105)
 for a,b,t in [(0,62.6,'62.60 / 3列共享墙'),(62.6,65,'净2.40'),(65,86,'21.00 / 内列')]:dimh(p,xy(a,0)[0],xy(b,0)[0],71,t,105,2.7)
 text(p,55,88,'内列SW-04/08/12整体向南错台11.80；所有房间仍21×9.5、人员门净1.40。灰色为室外退台。',3)
 for yy in [10.7,22.6]:arrow(p,[xy(60,yy),xy(-1.2,yy),xy(-1.2,16.65)],BLUE,False,.3)
 arrow(p,[xy(53,22.6),xy(63.8,22.6),xy(63.8,10.8),xy(89,10.8),xy(89,-7.2)],ORANGE,True,.35)
 text(p,*xy(87.8,-4.5),'向南梯',2.9,'end',ORANGE)
 text(p,*xy(78,10),'受控门1.80',2.6,'middle',ORANGE)
 text(p,*xy(49,10),'日常 → 本区L',2.8,'middle',BLUE)
 text(p,*xy(69.2,30),'局部物流核心/A403',2.8,'middle',MACHINE)
 text(p,*xy(70,27),'室外凹口',2.8,'middle','#777')
 text(p,*xy(-3.65,16.65),'L',3.4,'middle',BLUE)
 r=next(r for r in d['rooms'] if r['id']=='SW-06')
 for row in range(2):
  for side in range(2):
   for col in range(5):
    x=r['x1']+1.25+side*10.45+col*1.75;y=r['y1']+.7+row*5.8;xx,yy=xy(x,y+2.3);rect(p,xx,yy,1.05*q,2.3*q,.15,'#d4dadd','#666')
 xx,yy=xy(r['x1']+10.5,r['y1']+4.75);rect(p,xx-29,yy-4.5,58,10,0,'#fff','#fff');text(p,xx,yy-1,'Room1 v2 / 20舱保持',3,'middle');text(p,xx,yy+3,'纵2.40 / 横3.50 / 舱间0.70',2.5,'middle')
 dimv(p,xy(0,33.3)[1],xy(0,-11.8)[1],40,'45.10 / 阶梯房组',55,2.6)
 text(p,55,346,'两条外段人员廊通过真实2.40m竖向连接廊接入错台内列；全程不穿休眠室。',3)
 text(p,55,358,'紧急门平时关闭；应急开启后进入南半纵向通道，只向南。核心前人员隔断关闭，机器人停运。',3)
 text(p,55,370,'区内电梯位置/轿厢/井道尺度保持相对外三列；其他分区按纵向、横向镜像，容量不变。',3)
 p=page('A403','v3交通核心 / 北南单门楼梯、受控向外疏散与机器专用四货梯','局部1:100');pages.append(p)
 text(p,27,48,'01 北段/北楼梯（南侧镜像）',3.5)
 bounds=(cx-3.2,v['NorthIsolation']-.1,cx+3.2,v['MaxNorth']);xy,q=mapper(40,55,100,bounds);background(p,xy,q,bounds);draw_plan(p,d,xy,q,bounds,False,False);treads(p,d,xy,q,'North')
 arrow(p,[xy(cx-.7,v['NorthZoneY']+10.7+11.8),xy(cx-.7,v['NorthStairInner']+.6)],ORANGE,True,.4)
 arrow(p,[xy(cx+1,v['NorthStairInner']-3),xy(cx+1,v['NorthIsolation']+2)],MACHINE,True,.3)
 line(p,*xy(cx-3,v['NorthIsolation']-.1),*xy(cx+3,v['NorthIsolation']-.1),.65,'#b12828')
 for yy in [59.8,71.7]:
  arrow(p,[xy(cx-3,yy),xy(cx-.7,yy),xy(cx-.7,yy+2)],ORANGE,True,.25)
 text(p,119,70,'单门净1.80直入，无前室',3.0,color=ORANGE)
 for i,t in enumerate(['北梯外包4.20×7.30 P','净梯段1.80 / 平台1.80','内嵌4.70 / 外伸2.60','24级 / 级高158.33 mm','机器正常：往返物流','紧急：本段机器人停运','人员门开，只向外楼梯','核心边界关闭，禁止向内','南梯与南段关系镜像']):text(p,119,86+i*13,t,2.8)
 text(p,119,224,'02 西/东楼梯：保持两门直入',2.9)
 bb=(-2.6,cy-3,4.7,cy+3);xx,qq=mapper(125,239,100,bb);draw_plan(p,d,xx,qq,bb,False,False);treads(p,d,xx,qq,'West')
 text(p,119,312,'西/东井道7.30×4.20；右侧镜像。',2.6)
 text(p,119,325,'上/下各1门，无额外前室或第三门。',2.6)
 text(p,119,342,'红线：应急时对人关闭；',2.8,color='#b12828')
 text(p,119,355,'常态机器门可用，人不得穿核心。',2.6)
 text(p,119,370,'门扇扫掠/消防等级仍待详细设计。',2.6)
 text(p,278,48,'03 几何中央四货梯 / 净转运11.20×11.20',3.5)
 bounds=(v['CoreWest']-4.2,v['CoreSouth']-4.2,v['CoreEast']+4.2,v['CoreNorth']+4.2);xy,q=mapper(278,78,100,bounds);background(p,xy,q,bounds);draw_plan(p,d,xy,q,bounds,False,True)
 dimh(p,xy(v['CoreWest'],0)[0],xy(v['CoreEast'],0)[0],65,'19.60 / 仅中央节点局部膨大',78)
 rr=c['turn_circle_diameter_m']/2
 for x,y in [(cx,cy),(cx-3.4,cy),(cx+3.4,cy),(cx,cy-3.4),(cx,cy+3.4)]:circle(p,*xy(x,y),rr*q,.16,'none',MACHINE,True)
 for sign in [-1,1]:
  for x,y in [(cx+sign*3.4,v['CoreNorth']+2),(cx+sign*3.4,v['CoreSouth']-2),(v['CoreWest']-2,cy+sign*3.4),(v['CoreEast']+2,cy+sign*3.4)]:circle(p,*xy(x,y),rr*q,.13,'none','#9aa39a',True)
 text(p,*xy(cx,cy),'机器专用 / 人员禁入',3.0,'middle','#b12828')
 text(p,278,366,'外接窄段净6/4；四梯净3.20×3.80、门2.40、八个绕行口净2.40。',2.8)
 text(p,278,377,'Q四个整车等待位；回转圆Ø3.736；逐台停梯后其余三梯可达。',2.8)
 return pages

def to_svg(p):
 root=ET.Element('svg',xmlns='http://www.w3.org/2000/svg',width='594mm',height='420mm',viewBox='0 0 594 420')
 for a in p['items']:
  k=a['k']
  if k=='text':
   e=ET.SubElement(root,'text',{'x':str(a['x']),'y':str(a['y']),'font-size':str(a['size']),'font-family':'SimSun,serif','text-anchor':a['anchor'],'fill':a['color']});e.text=a['s'];continue
  attr={'stroke':a['color'],'stroke-width':str(a['lw']),'fill':a.get('fill','none')}
  if a.get('dash'):attr['stroke-dasharray']='1.5,1'
  if k=='line':attr.update({key:str(a[key]) for key in ['x1','y1','x2','y2']});ET.SubElement(root,'line',attr)
  elif k=='rect':attr.update(x=str(a['x']),y=str(a['y']),width=str(a['w']),height=str(a['h']));ET.SubElement(root,'rect',attr)
  elif k=='circle':attr.update(cx=str(a['x']),cy=str(a['y']),r=str(a['r']));ET.SubElement(root,'circle',attr)
 return ET.tostring(root,encoding='unicode')
