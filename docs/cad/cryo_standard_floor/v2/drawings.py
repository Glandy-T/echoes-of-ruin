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
 text(p,22,399,'Echoes of Ruin | 标准休眠层 v2 | P = 暂定 / 仅二维工程验证',3)
 text(p,572,399,scale+' | A2原尺寸 | 2026-10-07',3,'end');return p
def mapper(px,py,scale,bounds):
 q=1000/scale;return lambda x,y:(px+(x-bounds[0])*q,py+(bounds[3]-y)*q),q
def draw_plan(p,d,xy,q,bounds,labels=True,flow=False,omit_core=False):
 x1,y1,x2,y2=bounds;v=d['parameters']
 def fill(r,col,stroke='#aaa',lw=.08):
  a,b=max(x1,r['x1']),max(y1,r['y1']);c,f=min(x2,r['x2']),min(y2,r['y2'])
  if c>a and f>b:
   xx,yy=xy(a,f);rect(p,xx,yy,(c-a)*q,(f-b)*q,lw,col,stroke)
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
  col=BLUE if door['kind'] in ['room','elevator'] else ORANGE if door['kind'] in ['emergency','stair'] else MACHINE
  ends=[xy(x-a,y),xy(x+a,y)] if door['orientation']=='H' else [xy(x,y-a),xy(x,y+a)]
  line(p,*ends[0],*ends[1],.16,col,True)
  if door['kind']=='stair':
   # Open double leaves point into the landing, away from exterior approach.
   towards=1 if y<v['CenterY'] else -1
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
   col=BLUE if e['kind']=='daily' else ORANGE if e['kind']=='emergency' else MACHINE
   line(p,*xy(a['x'],a['y']),*xy(b['x'],b['y']),.22 if q<3 else .28,col,e['kind']!='daily')
def legend(p,x,y):
 for i,(col,dash,s) in enumerate([(BLUE,False,'日常人员 / 本区外侧电梯'),(ORANGE,True,'应急人员 / 上下两门直入楼梯'),(MACHINE,True,'机器物流 / 四向绕行入中央核心')]):
  line(p,x,y+i*8,x+16,y+i*8,.35,col,dash);text(p,x+21,y+1+i*8,s,3)
def make_pages(d,c):
 v=d['parameters'];pages=[];cx,cy=v['CenterX'],v['CenterY']
 p=page('A401','标准休眠层 v2 / 嵌入楼梯、中央四货梯与分流总平面','1:500');pages.append(p)
 bounds=(-v['ExternalReach'],0,v['MainWidth']+v['ExternalReach'],v['MainDepth']);xy,q=mapper(55,114,500,bounds);draw_plan(p,d,xy,q,bounds,True,True)
 x0=xy(0,0)[0];xr=xy(v['MainWidth'],0)[0];top=114;bottom=top+v['MainDepth']*q
 dimh(p,55,55+v['MaxWidth']*q,50,f'最大包络 {v["MaxWidth"]:.2f} m / 外置电梯控制',top)
 dimh(p,x0,xr,67,f'主体 {v["MainWidth"]:.2f} m',top)
 for a,b,s in [(0,83.4,'83.40 / 单区'),(83.4,v['EastZoneX'],'19.60 / 核心结构带'),(v['EastZoneX'],v['MainWidth'],'83.40 / 单区')]:dimh(p,xy(a,0)[0],xy(b,0)[0],85,s,top,2.8)
 text(p,55,100,'6m / 4m机器走廊在核心前分流绕行；中央净11.20×11.20，四货梯背墙外侧设4m深转向入口。',3)
 dimv(p,top,bottom,38,f'{v["MainDepth"]:.2f}',x0)
 for hi,lo,s in [(v['MainDepth'],v['NorthZoneY'],'33.30'),(v['NorthZoneY'],33.3,'19.60'),(33.3,0,'33.30')]:dimv(p,xy(0,hi)[1],xy(0,lo)[1],53,s,x0,2.6)
 for zone in ['SW','SE','NW','NE']:
  x=v['MainWidth']+3.65 if zone.endswith('E') else -3.65;y=(v['NorthZoneY'] if zone.startswith('N') else 0)+16.65;text(p,*xy(x,y),'L',2.6,'middle',BLUE)
 for s in d['stairs']:text(p,*xy((s['x1']+s['x2'])/2,cy),'S',2.7,'middle',ORANGE)
 text(p,465,122,'v2 / 变更与验证',3.7)
 for i,s in enumerate(['48室 / 960舱保持','4区各3×4室保持','人员廊净2.40保持','房间64门 / 净1.40','人员电梯4处保持','楼梯嵌入4.70 m','楼梯外伸2.60 m','每侧上/下各1门','删除额外前室及门','中央四货梯FN/FS/FW/FE','Q = 四个独立等待位','逐台停梯：其余3台可达','中央核心不侵入人员区']):text(p,465,135+i*10,s,2.8)
 legend(p,55,305)
 text(p,300,306,'宽 = 83.40 + 19.60 + 83.40 = 186.40',2.9)
 text(p,300,319,'深 = 33.30 + 19.60 + 33.30 = 86.20',2.9)
 rect(p,50,336,507,42,.18,'#fff8ed',ORANGE)
 text(p,58,347,'待解决：最远房间中心 → 最近楼梯 112.75 m；舱侧操作位保守路径约123.50 m。',3.3,color=ORANGE)
 text(p,58,359,'仅二维净空与拓扑验证；960人疏散容量/时间、消防分隔、无障碍和电梯运力尚未定案。',3)
 text(p,58,371,'核心反算扩大导致分区整体退让；间隙余量不定义新功能。本轮不做正式3D或整栋堆叠。',3)
 p=page('A402','典型分区 v2 / 双门中排、外侧电梯与受控应急桥','1:200');pages.append(p)
 bounds=(-5.1,0,cx+3,33.3);xy,q=mapper(55,123,200,bounds);draw_plan(p,d,xy,q,bounds,True,False,True)
 text(p,*xy(cx,31),'接核心 / A403',2.8,'middle',MACHINE)
 dimh(p,xy(0,0)[0],xy(83.4,0)[0],53,'83.40 m / 共享墙外包',123)
 for col in range(4):dimh(p,xy(col*20.8,0)[0],xy(col*20.8+21,0)[0],71,'21.00 / 外包',123)
 text(p,55,89,'共享隔墙0.20；相邻室原点间距20.80；房间净20.60×9.10。Room1 v2原文件完整保留。',3)
 text(p,55,102,'两条人员廊仍接同一外侧电梯；四节点相对各自分区的位置与尺度不改，随分区整体退让。',3)
 text(p,*xy(-3.65,16.65),'L',3.4,'middle',BLUE)
 for y in [10.7,22.6]:
  arrow(p,[xy(78,y),xy(-1.2,y),xy(-1.2,16.65)],BLUE)
  text(p,*xy(48,y+.4),'人员廊净2.40 / 不穿中排房间',3.1,'middle',BLUE)
  line(p,*xy(83.3,y),*xy(cx,y),.26,ORANGE,True)
  text(p,*xy(86.8,y+.35),'仅应急',2.6,'middle',ORANGE)
 r=next(r for r in d['rooms'] if r['id']=='SW-06')
 for row in range(2):
  for side in range(2):
   for col in range(5):
    x=r['x1']+1.25+side*10.45+col*1.75;y=r['y1']+.7+row*5.8;xx,yy=xy(x,y+2.3);rect(p,xx,yy,1.05*q,2.3*q,.15,'#d4dadd','#666')
 xx,yy=xy(r['x1']+10.5,r['y1']+4.75);rect(p,xx-29,yy-4.5,58,10,.1,'#ffffff','#ffffff');text(p,xx,yy-1,'SW-06 / Room1 v2',3,'middle');text(p,xx,yy+3,'纵2.40 / 横3.50 / 舱间0.70',2.6,'middle')
 dimv(p,123,289.5,40,'33.30',xy(0,0)[0])
 for hi,lo,s in [(33.3,23.8,'9.50'),(23.8,21.4,'2.40'),(21.4,11.9,'9.50'),(11.9,9.5,'2.40'),(9.5,0,'9.50')]:dimv(p,xy(0,hi)[1],xy(0,lo)[1],54,s,xy(0,0)[0],2.6)
 dimh(p,xy(cx-3,0)[0],xy(cx+3,0)[0],312,'机器净6.00',290)
 text(p,55,312,'内端净1.80受控门 → 净2.40应急桥',3,color=ORANGE)
 text(p,55,328,'中排16室仍各有两扇1.40m人员门；普通流线不把休眠室作为公共穿行捷径。',3.1)
 text(p,55,342,'外侧连接带继续通向本侧楼梯；上下区只通过楼梯的两道防火门相连，日常保持隔离。',3.1)
 text(p,55,356,'6m脊柱两侧退让余量不定义新功能；跨余量的连接桥仅在应急状态使用。',3.1)
 text(p,55,370,'四区同构镜像；单室21×9.5、20舱位置、2.4纵轴、3.5横廊、0.7操作间距均沿用既有模型。',3)
 p=page('A403','v2交通核心 / 两门直入楼梯与中央四梯机器转运','楼梯1:50 / 物流核心1:100');pages.append(p)
 text(p,27,51,'01 左消防楼梯 / 半外置、无额外前室',3.7)
 bounds=(-2.6,cy-4.5,4.7,cy+4.5);xy,q=mapper(55,85,50,bounds);draw_plan(p,d,xy,q,bounds,False)
 dimh(p,55,201,69,'井道外包7.30 / 净梯段1.80',85)
 dimv(p,xy(0,cy+2.1)[1],xy(0,cy-2.1)[1],39,'4.20',55)
 for r in d['references']:
  if r['tag']=='stair_flight' and r.get('side')=='West':
   for i in range(1,11):line(p,*xy(r['x1']+i*.3,r['y1']),*xy(r['x1']+i*.3,r['y2']),.15,'#666')
   y=(r['y1']+r['y2'])/2;a,b=(r['x1']+.1,r['x2']-.1) if r['flight']==0 else (r['x2']-.1,r['x1']+.1);arrow(p,[xy(a,y),xy(b,y)],ORANGE)
 for sign,s in [(1,'上区应急'),(-1,'下区应急')]:
  arrow(p,[xy(-1.2,cy+sign*4.2),xy(-1.2,cy+sign*.9)],ORANGE,True,.3)
  text(p,120,95 if sign==1 else 258,s+' / 直接门1.80',3.0,color=ORANGE)
 line(p,*xy(0,cy-4.5),*xy(0,cy+4.5),.12,'#777',True)
 text(p,27,273,'梯段净1.80 / 平台1.80 / 跑长3.30 / 踏步300mm P；右侧镜像。',2.7)
 text(p,27,281,'内嵌4.70 / 外伸2.60；虚线X=0；层高3.80 / 24级 / 级高158.33mm P。',2.7)
 text(p,27,289,'中央净11.20×11.20 / 回转圆 Ø3.736m / 四个独立等待位Q。',2.7)
 # Locator: the four passenger nodes are retained at their relative quadrants.
 text(p,27,301,'02 四个人员电梯 L 与楼梯 S / 中央核心相对位置（示意）',2.7)
 bounds=(-4.9,0,v['MainWidth']+4.9,v['MainDepth']);xy,q=mapper(27,306,1100,bounds)
 xx,yy=xy(0,v['MainDepth']);rect(p,xx,yy,v['MainWidth']*q,v['MainDepth']*q,.15,'none','#888')
 xx,yy=xy(83.4,v['NorthZoneY']);rect(p,xx,yy,v['CoreWidth']*q,v['CoreWidth']*q,.15,'#eeeeeb',MACHINE)
 text(p,*xy(cx,cy),'4F',2.6,'middle',MACHINE)
 for zone in ['SW','SE','NW','NE']:
  x=v['MainWidth']+3.65 if zone.endswith('E') else -3.65;y=(v['NorthZoneY'] if zone.startswith('N') else 0)+16.65;text(p,*xy(x,y),'L',2.8,'middle',BLUE)
  text(p,*xy((v['EastZoneX'] if zone.endswith('E') else 0)+41.7,(v['NorthZoneY'] if zone.startswith('N') else 0)+16.65),zone,2.8,'middle')
 for x in [-1.5,v['MainWidth']+1.5]:text(p,*xy(x,cy),'S',2.8,'middle',ORANGE)
 text(p,278,51,'03 中央四货梯 / 原位回转、双侧绕行、四等待位',3.7)
 bounds=(83.4-4.2,33.3-4.2,v['EastZoneX']+4.2,v['NorthZoneY']+4.2);xy,q=mapper(278,78,100,bounds);draw_plan(p,d,xy,q,bounds,False,True)
 dimh(p,xy(83.4,0)[0],xy(v['EastZoneX'],0)[0],66,'物流核心外包19.60×19.60',78)
 rr=c['turn_circle_diameter_m']/2
 for x,y in [(cx,cy),(cx-3.4,cy),(cx+3.4,cy),(cx,cy-3.4),(cx,cy+3.4)]:circle(p,*xy(x,y),rr*q,.17,'none',MACHINE,True)
 for sign in [-1,1]:
  for x,y in [(cx+sign*3.4,v['NorthZoneY']+2),(cx+sign*3.4,33.3-2),(83.4-2,cy+sign*3.4),(v['EastZoneX']+2,cy+sign*3.4)]:circle(p,*xy(x,y),rr*q,.13,'none','#9aa39a',True)
 # Door/car dimensions are common to all four rotated shafts.
 text(p,*xy(cx,v['NorthZoneY']+3.4),'外接脊柱净6.00',2.8,'middle')
 text(p,*xy(cx,33.3-3.4),'外接脊柱净6.00',2.8,'middle')
 for x in [83.4-2,v['EastZoneX']+2]:text(p,*xy(x,cy),'4.00',2.6,'middle')
 text(p,278,367,'四梯净3.20×3.80 / 井道3.60×4.20；门2.40；背部双侧绕行开口2.40。',2.8)
 text(p,278,378,'Q：整车1.70×3.10等待位；4m入口转向，单梯停用后其余3梯均可达。',2.8)
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
