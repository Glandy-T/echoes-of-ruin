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
 text(p,22,399,'Echoes of Ruin | 标准休眠层 v3 trim / 0F 电梯外伸板裁除 / 空间冻结 | P = 暂定 / 仅二维工程验证',3)
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
 for r in d.get('machine_work_areas',[]):fill(r,'#edf2e8','#edf2e8',0)
 for r in d['corridors']:fill(r,'#eaf1f6',BLUE)
 from layout import subtract_rectangles
 for r in subtract_rectangles(d['personnel_structural_nodes'],d['passenger_shaft_voids']):fill(r,'#f1f6f9',BLUE)
 if not omit_core:
  for r in d['plenums']+[d['transfer']]:fill(r,'#f3f5f2',MACHINE)
 for r in d['references']:
  if r['tag']=='lane_marking':
   xa,ya=max(x1,r['x1']),max(y1,r['y1']);xb,yb=min(x2,r['x2']),min(y2,r['y2'])
   if xb>xa and yb>ya:
    a,b=xy(xa,yb);rect(p,a,b,(xb-xa)*q,(yb-ya)*q,.12,'none',MACHINE,True)
   continue
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
  ends=[xy(max(x1,x-a),y),xy(min(x2,x+a),y)] if door['orientation']=='H' else [xy(x,max(y1,y-a)),xy(x,min(y2,y+a))]
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
  if r['tag']=='lane_marking':
   a,b=xy(r['x1'],r['y2']);rect(p,a,b,(r['x2']-r['x1'])*q,(r['y2']-r['y1'])*q,.12,'none',MACHINE,True);continue
  if r['tag']!='stair_flight' or r.get('side')!=side:continue
  for i in range(1,11):
   if r['axis']=='Y':line(p,*xy(r['x1'],r['y1']+i*.3),*xy(r['x2'],r['y1']+i*.3),.13,'#666')
   else:line(p,*xy(r['x1']+i*.3,r['y1']),*xy(r['x1']+i*.3,r['y2']),.13,'#666')

def background(p,xy,q,bounds):
 xx,yy=xy(bounds[0],bounds[3]);rect(p,xx,yy,(bounds[2]-bounds[0])*q,(bounds[3]-bounds[1])*q,0,'#f1f1f1','#f1f1f1')

def treads(p,d,xy,q,side):
 for r in d['references']:
  if r['tag']=='lane_marking':
   a,b=xy(r['x1'],r['y2']);rect(p,a,b,(r['x2']-r['x1'])*q,(r['y2']-r['y1'])*q,.12,'none',MACHINE,True);continue
  if r['tag']!='stair_flight' or r.get('side')!=side:continue
  for i in range(1,11):
   if r['axis']=='Y':line(p,*xy(r['x1'],r['y1']+i*.3),*xy(r['x2'],r['y1']+i*.3),.13,'#666')
   else:line(p,*xy(r['x1']+i*.3,r['y1']),*xy(r['x1']+i*.3,r['y2']),.13,'#666')


def make_pages(d,c):
 v=d['parameters'];cx,cy=v['CenterX'],v['CenterY'];pages=[]
 p=page('A401','标准休眠层 v3 trim / 接受平面保持、北南楼梯完全内嵌','1:500');pages.append(p)
 bounds=tuple(d['bounds'][k] for k in ['x1','y1','x2','y2']);xy,q=mapper(45,96,500,bounds);draw_plan(p,d,xy,q,bounds,True,True)
 dimh(p,xy(bounds[0],0)[0],xy(bounds[2],0)[0],49,f'含节点最大宽 {v["MaxWidth"]:.2f} m',96)
 dimh(p,xy(0,0)[0],xy(v['MainWidth'],0)[0],67,f'主体宽 {v["MainWidth"]:.2f} m / X位置保持v2',96)
 for a,b,t in [(0,v['CoreWest'],'83.40 / 4列共享墙'),(v['CoreWest'],v['CoreEast'],'19.60 / 机器区'),(v['CoreEast'],v['MainWidth'],'83.40 / 镜像')]:dimh(p,xy(a,0)[0],xy(b,0)[0],83,t,96,2.5)
 dimv(p,xy(0,v['FloorNorth'])[1],xy(0,v['FloorSouth'])[1],38,'77.80',xy(0,0)[0],2.6)
 dimv(p,96,96+v['MaxDepth']*q,23,'77.80',45,2.6)
 for side in ['West','East','North','South']:
  r=next(r for r in d['stairs'] if r['side']==side);text(p,*xy((r['x1']+r['x2'])/2,(r['y1']+r['y2'])/2),dict(West='西S',East='东S',North='北S',South='南S')[side],2.8,'middle',ORANGE)
 for zone in ['SW','SE','NW','NE']:
  x=v['MainWidth']+3.65 if zone.endswith('E') else -3.65;y=(v['NorthZoneY'] if zone.startswith('N') else v['FloorSouth'])+16.65;text(p,*xy(x,y),'L',2.6,'middle',BLUE)
 for north in [False,True]:
  y0=(v['NorthZoneY']+10.7) if north else (v['FloorSouth']+22.6);y1=v['NorthStairInner']+.1 if north else v['SouthStairInner']-.1
  arrow(p,[xy(cx-.6,y0),xy(cx-.6,y1)],ORANGE,True,.4)
 for yy in [v['SouthIsolation']+.1,v['NorthIsolation']-.1]:line(p,*xy(v['CoreWest'],yy),*xy(v['CoreEast'],yy),.6,'#b12828')
 text(p,*xy(cx,cy),'人员禁入',2.8,'middle','#b12828')
 for xx in [44,v['MainWidth']-44]:
  text(p,*xy(xx,cy+3.8),'连续机器物流 / 作业区',2.7,'middle',MACHINE)
  text(p,*xy(xx,cy-3.8),'净78.70×11.20 / 主运输车道4.00',2.4,'middle',MACHINE)
 text(p,447,111,'0F / 电梯外伸板裁除',3.6)
 info=['48室 / 960舱 / 4区各240','每区83.40×33.30、3×4室','Room1 21×9.5；人员廊2.4','NW+NE整体下移4.20','SW+SE整体上移4.20','全部X坐标与v2一致','四台人员梯随本区平移','横向余量每侧7.80→3.60','剩余全部定义为机器作业','车道4 / 6为地面标线','侧带6.80为连续机器作业','核心四梯19.60 / 净11.20','Q四位、八绕行口2.40','北南梯全内嵌；西东不动']
 for i,t in enumerate(info):text(p,447,125+i*9.2,t,2.6)
 legend(p,45,294);text(p,269,295,'浅绿：连续机器作业地面 / 4m、6m为主车道',2.8)
 text(p,269,307,'人员：日常走外侧L；紧急可沿纵段向外S',2.8)
 text(p,269,319,'红线：整个19.60m纵段应急隔离，禁止绕入核心',2.8,color='#b12828')
 rect(p,45,337,512,40,.18,'#fff8ed',ORANGE)
 text(p,53,347,f'最远中心 → 最近楼梯 {c["maximum_center_to_nearest_stair_m"]:.2f} m；舱侧保守 {c["conservative_pod_operation_to_nearest_stair_m"]:.2f} m。',3.2,color=ORANGE)
 text(p,53,358,'最远房SW-02（另SE-03 / NW-10 / NE-11同值）；全部48室均有外侧及北/南两种疏散方向。',2.9)
 text(p,53,370,'已验几何与路线；960人疏散容量/时间、消防隔断构造、门扇扫掠仍待详设。另附整层3D Blockout。',2.8)
 p=page('A402','典型SW分区 / 完整3×4网格、人员走廊与整体平移验证','1:200');pages.append(p)
 bounds=(-5.1,v['FloorSouth'],cx+1,v['FloorSouth']+v['ZoneDepth']);xy,q=mapper(55,107,200,bounds);draw_plan(p,d,xy,q,bounds,True,False)
 dimh(p,xy(0,0)[0],xy(v['ZoneWidth'],0)[0],53,'83.40 = 4×21.00 − 3×0.20 / 共享墙',107)
 for col in range(4):dimh(p,xy(col*20.8,0)[0],xy(col*20.8+21,0)[0],73,'21.00',107,2.8)
 text(p,55,92,'整个SW分区从v2上移4.20m；房间、两条人员廊、外侧电梯相对位置保持。其他三区镜像平移。',2.9)
 dimv(p,107,107+33.3*q,39,'33.30',55,2.6)
 for ci in range(2):
  yy=v['FloorSouth']+10.7+ci*11.9;arrow(p,[xy(60,yy),xy(-1.2,yy),xy(-1.2,v['FloorSouth']+16.65)],BLUE,False,.3)
 arrow(p,[xy(72.9,26.8),xy(cx,26.8),xy(cx,11.4)],ORANGE,True,.35)
 text(p,*xy(cx-.8,13),'仅向南S',2.5,'end',ORANGE)
 text(p,*xy(-3.65,v['FloorSouth']+16.65),'L',3,'middle',BLUE)
 for x,y,t in [(40,14.9,'日常 → 本区L'),(53,26.8,'人员净廊2.40'),(84,26.8,'门1.80')]:text(p,*xy(x,y-.3),t,2.5,'middle',BLUE if x<60 else ORANGE)
 r=next(r for r in d['rooms'] if r['id']=='SW-06')
 for row in range(2):
  for side in range(2):
   for col in range(5):
    x=r['x1']+1.25+side*10.45+col*1.75;y=r['y1']+.7+row*5.8;xx,yy=xy(x,y+2.3);rect(p,xx,yy,1.05*q,2.3*q,.15,'#d4dadd','#666')
 xx,yy=xy(r['x1']+10.5,r['y1']+4.75);rect(p,xx-29,yy-4.5,58,10,0,'#fff','#fff');text(p,xx,yy-1,'Room1 v2 / 20舱保持',3,'middle');text(p,xx,yy+3,'纵2.40 / 横3.50 / 舱间0.70',2.5,'middle')
 text(p,55,297,'01 原点与平移：SW (0,0) → (0,4.20)；SE (103,0) → (103,4.20)。',3)
 text(p,55,309,'02 NW (0,52.90) → (0,48.70)；NE (103,52.90) → (103,48.70)。未移动任何单间。',3)
 text(p,55,323,'03 下区北边界37.50 / 上区南边界48.70；二者间净11.20成为连续机器作业地面。',3)
 text(p,55,337,'04 中央主车道4.00、边侧操作带各3.60；沿线没有额外墙把车道切成喇叭口。',3)
 text(p,55,351,'05 相邻舱室共墙0.20；所有房间内部净20.60×9.10。中排双门；外排单门，门净1.40。',3)
 text(p,55,366,'06 紧急开启内端门：机器停运，南段只向南楼梯；核心全宽隔离。日常不走中央机器区。',3)
 p=page('A403','四向楼梯 / 受控向外疏散与四货梯、Q、回转包络','局部1:100');pages.append(p)
 text(p,27,48,'01 北段 / 北楼梯（南侧镜像）',3.4)
 bounds=(cx-3.2,v['NorthIsolation']-.1,cx+3.2,v['MaxNorth']);xy,q=mapper(39,64,100,bounds);draw_plan(p,d,xy,q,bounds,False,False);treads(p,d,xy,q,'North')
 arrow(p,[xy(cx-.7,59.4),xy(cx-.7,v['NorthStairInner']+.6)],ORANGE,True,.4)
 for yy in [59.4,71.3]:arrow(p,[xy(cx-3,yy),xy(cx-.7,yy),xy(cx-.7,yy+2)],ORANGE,True,.25)
 line(p,*xy(cx-3.2,v['NorthIsolation']-.1),*xy(cx+3.2,v['NorthIsolation']-.1),.65,'#b12828')
 for i,t in enumerate(['单门1.80，直入平台','北梯4.20×7.30 P','净梯段1.80 / 平台1.80','完全内嵌7.30 / 外伸0.00','24级 / 158.33mm级高','南北主车道地面净6.00','两侧各6.80机器作业','紧急：纵段全区停机','隔离线横跨整个19.60','人员只向外，不进核心']):text(p,112,82+i*13,t,2.7,color=ORANGE if i==0 else '#222')
 text(p,112,224,'02 西/东楼梯：保持两门直入',2.8)
 bb=(-2.6,cy-3,4.7,cy+3);xx,qq=mapper(122,238,100,bb);draw_plan(p,d,xx,qq,bb,False,False);treads(p,d,xx,qq,'West')
 text(p,112,312,'7.30×4.20；上/下各门1.80。',2.6)
 text(p,112,325,'无第三门、无额外前室；东侧镜像。',2.6)
 text(p,112,342,'红线是应急对人隔离边界。',2.6,color='#b12828')
 text(p,112,355,'需落实消防隔断构造与停机联锁。',2.6)
 text(p,112,370,'图示门扇仅示意，扫掠仍待验证。',2.6)
 text(p,278,48,'03 原位保留四货梯与Q / 连续机器作业地面',3.4)
 bounds=(v['CoreWest']-4.2,v['CoreSouth']-4.2,v['CoreEast']+4.2,v['CoreNorth']+4.2);xy,q=mapper(278,78,100,bounds);draw_plan(p,d,xy,q,bounds,False,True)
 dimh(p,xy(v['CoreWest'],0)[0],xy(v['CoreEast'],0)[0],65,'19.60 / 原位四货梯工作核心',78)
 rr=c['turn_circle_diameter_m']/2
 for x,y in [(cx,cy),(cx-3.4,cy),(cx+3.4,cy),(cx,cy-3.4),(cx,cy+3.4)]:circle(p,*xy(x,y),rr*q,.16,'none',MACHINE,True)
 for sign in [-1,1]:
  for x,y in [(cx+sign*3.4,v['CoreNorth']+2),(cx+sign*3.4,v['CoreSouth']-2),(v['CoreWest']-2,cy+sign*3.4),(v['CoreEast']+2,cy+sign*3.4)]:circle(p,*xy(x,y),rr*q,.13,'none','#9aa39a',True)
 text(p,*xy(cx,cy),'机器专用 / 净11.20×11.20',2.8,'middle','#b12828')
 text(p,278,366,'四梯净3.20×3.80 / 门2.40；八绕行口2.40；Q四个1.70×3.10。',2.7)
 text(p,278,377,'回转圆Ø3.736；四Q满位通行、逐台停梯绕行均经实体复核。',2.7)
 pages.append(cleanup_page(d))
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


def cleanup_page(d):
 from pathlib import Path
 import json
 old=json.loads((Path(__file__).resolve().parent/'sources/before_cleanup_layout.snapshot.json').read_text(encoding='utf-8'))
 p=page('A405','人员电梯节点收尾 / 实际楼板裁切、井道与保护廊保持','1:200 / 1:50 / 1:10')
 def panel(data,px,py,scale,bounds):
  xy,q=mapper(px,py,scale,bounds);background(p,xy,q,bounds)
  for kind,rs in [('slab',data['floor_cells']),('wall',data['walls'])]:
   for r in rs:
    a,b=max(bounds[0],r['x1']),max(bounds[1],r['y1']);c,e=min(bounds[2],r['x2']),min(bounds[3],r['y2'])
    if c>a and e>b:rect(p,*xy(a,e),(c-a)*q,(e-b)*q,0,'#d8e6ef' if kind=='slab' else '#333','#d8e6ef' if kind=='slab' else '#333')
  return xy,q
 text(p,30,52,'西侧节点 / 0E裁切前',3.6);text(p,145,52,'西侧节点 / 0F裁切后',3.6)
 panel(old,35,65,200,(-5,13,6,48));panel(d,150,65,200,(-5,13,6,48))
 text(p,30,255,'蓝色为结构板平面；灰色为板外。',3)
 text(p,30,265,'仅去除井道上下外伸板；连接廊净宽2.40m保持。',3)
 text(p,30,275,'四节点镜像裁切，合计删除109.48平方米楼板。',3)
 text(p,285,52,'SW人员电梯井 / 修复后 / 1:50',3.6)
 xy,q=panel(d,285,65,50,(-5,18,-1.5,24.5))
 shaft=next(r for r in d['passenger_shaft_voids'] if r['zone']=='SW')
 a,b=xy(shaft['x1'],shaft['y2']);rect(p,a,b,(shaft['x2']-shaft['x1'])*q,(shaft['y2']-shaft['y1'])*q,.22,'#fff','#25618a')
 text(p,285,212,'井道净洞2.10×2.40m；四处同法扣除。',3)
 text(p,285,222,'0.20m井壁脚下支承保留；前室保留楼板。',3)
 text(p,285,232,'独立轿厢地面参照隐藏，仅显示结构井道洞口。',3)
 text(p,285,255,'南侧西墙闭合保持',3.4);text(p,435,255,'东墙镜像闭合保持 / 1:10',3.4)
 panel(d,300,265,10,(-2.8,27.7,-2.2,28.5));panel(d,450,265,10,(188.6,27.7,189.2,28.5))
 text(p,285,360,'Y28.00-28.20的0.20m缝闭合；东侧镜像同步。',3)
 text(p,285,370,'上轮两片补墙保留；本轮墙体与门洞完全不变。',3)
 text(p,30,310,'冻结范围：48室 / 960舱、四分区、人员电梯、四楼梯、',3)
 text(p,30,320,'四货梯、Q等待位、机器核心、外包和疏散拓扑均保持。',3)
 text(p,30,340,'本页平面源与3D结构板共用同一floor_cells几何。',3)
 text(p,30,350,'3D仍为单层空间灰模；高度与结构做法为暂定值。',3)
 return p
