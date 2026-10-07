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
 text(p,22,399,'Echoes of Ruin | 标准休眠层 v1 | P = 暂定 / 仅二维工程验证',3)
 text(p,572,399,scale+' | A2原尺寸 | 2026-10-07',3,'end');return p
def mapper(px,py,scale,bounds):
 q=1000/scale;return lambda x,y:(px+(x-bounds[0])*q,py+(bounds[3]-y)*q),q
def draw_plan(p,d,xy,q,bounds,labels=True,flows=False):
 x1,y1,x2,y2=bounds
 def cut(r):
  a,b=max(x1,r['x1']),max(y1,r['y1']);c,f=min(x2,r['x2']),min(y2,r['y2'])
  if c>a and f>b:return a,b,c,f
 def fill(r,color,lw=.12,stroke='#aaa'):
  b=cut(r)
  if b:
   a,y,c,f=b;xx,yy=xy(a,f);rect(p,xx,yy,(c-a)*q,(f-y)*q,lw,color,stroke)
 for r in d['corridors']:fill(r,'#eaf1f6',.08,BLUE)
 for r in d['elevator_nodes']:fill(r,'#f1f6f9',.12,BLUE)
 fill(d['freight_lobby'],'#f4f4f1',.12,MACHINE)
 for r in d['references']:fill(r,'#f0f0ed',.1,'#777')
 for w in d['walls']:fill(w,'#333',.08,'#333')
 for door in d['doors']:
  x,y=door['x'],door['y'];a=door['width']/2
  if not (x1<=x<=x2 and y1<=y<=y2):continue
  col=BLUE if door['kind'] in ['room','elevator'] else ORANGE if door['kind']=='emergency' else MACHINE
  ends=[xy(x-a,y),xy(x+a,y)] if door['orientation']=='H' else [xy(x,y-a),xy(x,y+a)]
  line(p,*ends[0],*ends[1],.18,col,True)
  # Symbolic two-leaf swinging fire door only on stair/machine-cross junctions.
  if door['kind']=='emergency' and door['orientation']=='V' and abs(y-d['parameters']['CrossCenterY'])<.001:
   for yy in [y-a,y+a]:line(p,*xy(x,yy),*xy(x+a,yy),.1,ORANGE)
 if labels:
  for r in d['rooms']:
   if cut(r):
    x,y=xy((r['x1']+r['x2'])/2,(r['y1']+r['y2'])/2)
    text(p,x,y-1,r['id'],2.8 if q<3 else 3.6,'middle');text(p,x,y+3,'20人',2.4 if q<3 else 2.8,'middle','#666')
 if flows:
  for e in d['routes']['edges']:
   if e['kind']=='daily':
    a=d['routes']['nodes'][e['a']];b=d['routes']['nodes'][e['b']]
    if a['role']=='room' or b['role']=='room':continue
    if all(x1<=pt['x']<=x2 and y1<=pt['y']<=y2 for pt in [a,b]):line(p,*xy(a['x'],a['y']),*xy(b['x'],b['y']),.26,BLUE)
  v=d['parameters']
  for side,x in [('West',-1.2),('East',v['MainWidth']+1.2)]:
   for y in [22.6,48.0]:arrow(p,[xy(x,y),xy(x,v['CrossCenterY'])],ORANGE,True,.28)
  arrow(p,[xy(v['SpineCenterX'],3),xy(v['SpineCenterX'],v['MainDepth']-3)],MACHINE,True,.32)
  arrow(p,[xy(6,v['CrossCenterY']),xy(v['MainWidth']-6,v['CrossCenterY'])],MACHINE,True,.32)
def legend(p,x,y):
 for i,(col,dash,s) in enumerate([(BLUE,False,'日常人员：本分区 → 外侧电梯'),(ORANGE,True,'应急人员：受控连接 → 两侧楼梯'),(MACHINE,True,'机器：6m脊柱 / 4m横廊 → 货梯')]):
  line(p,x,y+i*8,x+16,y+i*8,.35,col,dash);text(p,x+21,y+1+i*8,s,3)
def make_pages(d,c):
 v=d['parameters'];pages=[]
 p=page('A401','标准休眠层 / 总平面、共享墙尺寸链与分流','1:500');pages.append(p)
 bounds=(-v['ExternalReach'],0,v['MainWidth']+v['ExternalReach'],v['MainDepth']);xy,q=mapper(55,112,500,bounds)
 draw_plan(p,d,xy,q,bounds,True,True)
 left,right=xy(0,0)[0],xy(v['MainWidth'],0)[0];top,bottom=112,112+v['MainDepth']*q
 dimh(p,55,55+v['MaxWidth']*q,50,f'含外置楼梯总包络 {v["MaxWidth"]:.2f} m',top)
 dimh(p,left,right,67,f'主体 {v["MainWidth"]:.2f} m',top)
 cuts=[0,v['ZoneWidth'],v['ServiceStart'],v['EastZoneX'],v['MainWidth']]
 for a,b,s in zip(cuts,cuts[1:],['83.40 / 4室共享墙','6.00','4.20','83.40 / 4室共享墙']):dimh(p,xy(a,0)[0],xy(b,0)[0],84,s,top,2.5)
 text(p,55,98,'4.20 = 0.20隔墙 + 4.00货梯服务带；不占6m机器脊柱。长边21.00沿X / 短边9.50沿Y。',3)
 dimv(p,top,bottom,37,'70.60 m',left)
 for hi,lo,s in [(70.6,37.3,'33.30'),(37.3,33.3,'4.00'),(33.3,0,'33.30')]:dimv(p,xy(0,hi)[1],xy(0,lo)[1],52,s,left,2.5)
 for zone in ['SW','SE','NW','NE']:
  core=next(r for r in d['elevator_nodes'] if r['zone']==zone);x=v['MainWidth']+3.65 if zone.endswith('E') else -3.65;y=(core['y1']+core['y2'])/2
  xx,yy=xy(x,y);text(p,xx,yy,'L',2.7,'middle',BLUE)
 for r in d['stairs']:
  xx,yy=xy((r['x1']+r['x2'])/2,(r['y1']+r['y2'])/2);text(p,xx,yy-2,'S',3,'middle',ORANGE)
 xx,yy=xy(91.6,43.6);text(p,xx,yy-1,'F',2.6,'middle',MACHINE)
 text(p,465,121,'数量 / 平面验证',3.6)
 for i,s in enumerate(['4分区 × 12室 = 48室','每室20舱 / 共960舱','8条人员廊 / 净2.40','64个人员门 / 净1.40','中排16室两端门','4外置人员电梯节点','2独立楼梯 / 净1.80','楼梯内不含人员电梯','十字转向区净6×4','机器货梯独立服务带']):text(p,465,134+i*10,s,2.9)
 legend(p,55,277)
 text(p,55,311,'尺寸反算：单区宽 = 4×21.00 - 3×0.20 = 83.40；单区深 = 3×9.50 + 2×2.40 = 33.30 m。',3.2)
 text(p,55,324,'无货梯服务带骨架172.80×70.60；本版增加4.20 m宽服务带后主体177.00×70.60 m。',3.2)
 rect(p,50,335,507,42,.18,'#fff8ed',ORANGE)
 text(p,58,346,'待解决：最远房间中心 → 最近楼梯 106.95 m；舱侧操作位保守路径约117.70 m。',3.4,color=ORANGE)
 text(p,58,357,'仅证明路径拓扑连通与静态净宽；960人疏散容量、时间、消防分隔及可达性尚未验证。',3.1)
 text(p,58,368,'本版为可审阅二维方案；该长距离问题需继续设计，不能作为疏散设计定案。',3.1)
 p=page('A402','标准分区 / 3×4室、双门中排与外侧电梯接入','1:200');pages.append(p)
 bounds=(-5.1,0,89.4,33.3);xy,q=mapper(55,123,200,bounds)
 draw_plan(p,d,xy,q,bounds,True,False)
 text(p,*xy(-3.65,16.65),'L',3.5,'middle',BLUE)
 x0=xy(0,0)[0];xr=xy(83.4,0)[0]
 dimh(p,x0,xr,53,'83.40 m / 外包共享墙',123)
 for col in range(4):
  a=col*20.8;b=a+21;dimh(p,xy(a,0)[0],xy(b,0)[0],71,'21.00 / 外包',123)
 text(p,55,87,'共享隔墙0.20；相邻室原点间距20.80。单室净宽20.60 / 净深9.10。禁止将墙厚重复累计。',3)
 text(p,55,101,'SW示例；NW、SE、NE同构镜像。外排朝人员廊开1门；中排朝两条人员廊各开1门。',3)
 for y in [10.7,22.6]:
  arrow(p,[xy(78,y),xy(-1.2,y),xy(-1.2,16.65)],BLUE)
  text(p,*xy(46,y+.4),'人员廊净2.40 / 不经过中排房间',3.2,'middle',BLUE)
  xx,yy=xy(83.3,y);circle(p,xx,yy,2,.18,'#fff',ORANGE);text(p,xx+4,yy+1,'受控1.80',2.6,color=ORANGE)
 # One representative middle-row room: immutable Room1 v2 plan footprint, not 3D geometry.
 room=next(r for r in d['rooms'] if r['id']=='SW-06')
 for row in range(2):
  for side in range(2):
   for col in range(5):
    x=room['x1']+1.25+side*10.45+col*1.75;y=room['y1']+.7+row*5.8
    xx,yy=xy(x,y+2.3);rect(p,xx,yy,1.05*q,2.3*q,.15,'#d4dadd','#666')
 xx,yy=xy(room['x1']+10.5,room['y1']+4.75);rect(p,xx-29,yy-4.5,58,10,.1,'#fff','#fff');text(p,xx,yy-1,'SW-06 / Room1 v2',3,'middle');text(p,xx,yy+3,'纵2.40 / 横3.50 / 舱间0.70',2.6,'middle')
 dimv(p,123,123+33.3*q,40,'33.30',x0)
 # Room depth and personnel clear widths are measured vertically in physical plan.
 for hi,lo,s in [(33.3,23.8,'9.50'),(23.8,21.4,'2.40'),(21.4,11.9,'9.50'),(11.9,9.5,'2.40'),(9.5,0,'9.50')]:dimv(p,xy(0,hi)[1],xy(0,lo)[1],54,s,x0,2.6)
 dimh(p,xy(83.4,0)[0],xy(89.4,0)[0],313,'机器6.00',290,2.7)
 text(p,55,311,'L = 独立外侧电梯节点',3,color=BLUE)
 text(p,55,326,'蓝线：两条人员廊各自进入同一外侧前室；中排双门不构成公共穿房走廊。',3.2)
 text(p,55,340,'橙圈：机器廊端受控应急门；日常封闭。外侧2.40m连接带向楼梯延伸部分也只用于应急。',3.1)
 text(p,55,354,'Room1 v2仅增开所需对向人员门：房间21×9.5、墙0.20、20舱位置与通道尺度沿用既有模型。',3.1)
 text(p,55,368,'图中SW-06示意20舱；其余房间使用同一模块。单室原生v2文件完整保留，本轮不修改。',3.1)
 p=page('A403','核心节点 / 人员电梯、独立楼梯与机器货梯','局部1:100 / 1:50');pages.append(p)
 text(p,27,51,'01 人员电梯节点 / 1:100',3.8);text(p,196,51,'02 独立折返楼梯 / 1:50',3.8);text(p,419,51,'03 机器货梯 / 1:100',3.8)
 bounds=(-4.9,9.3,.2,24.0);xy,q=mapper(53,85,100,bounds);draw_plan(p,d,xy,q,bounds,False)
 dimh(p,53,104,73,'5.10 m外包',85);dimv(p,85,232,39,'14.70',53)
 for y in [10.7,22.6]:arrow(p,[xy(.1,y),xy(-1.2,y),xy(-1.2,16.65)],BLUE)
 xx,yy=xy(-3.65,16.65);text(p,xx,yy,'L',3.2,'middle',BLUE)
 text(p,114,97,'前室连接带',3);text(p,114,107,'净2.40 m',3,color=BLUE)
 text(p,114,130,'轿厢净',3);text(p,114,140,'2.10×2.40 P',3)
 text(p,114,158,'井道外包',3);text(p,114,168,'2.50×2.80 P',3)
 text(p,114,188,'电梯门1.40 P',3);text(p,114,208,'上下端应急门',3);text(p,114,218,'各1.80 P',3,color=ORANGE)
 bounds=(-9.7,33.2,0,37.4);xy,q=mapper(216,97,50,bounds);draw_plan(p,d,xy,q,bounds,False)
 for r in d['references']:
  if r['tag']=='stair_flight' and r.get('side')=='West':
   for i in range(1,11):line(p,*xy(r['x1']+i*.3,r['y1']),*xy(r['x1']+i*.3,r['y2']),.15,'#666')
   cy=(r['y1']+r['y2'])/2
   a,b=(r['x2']-.15,r['x1']+.15) if r['flight']==0 else (r['x1']+.15,r['x2']-.15)
   arrow(p,[xy(a,cy),xy(b,cy)],ORANGE,False,.25)
 dimh(p,216,362,84,'井道外包7.30 m',97);dimv(p,97,181,204,'4.20',216)
 dimh(p,xy(-2.4,0)[0],xy(0,0)[0],193,'前室净2.40',181)
 text(p,220,211,'层高3.80 / 24级 / 每跑12级',3.1)
 text(p,220,224,'级高158.33 mm P；踏步300 mm P',3)
 text(p,220,237,'每跑水平投影11×0.30 = 3.30 m',3)
 text(p,220,250,'双跑净1.80；中缝0.20；平台1.80',3)
 text(p,220,263,'外包 = (1.8+3.3+1.8+0.4)×',3)
 text(p,220,275,'(1.8+0.2+1.8+0.4) = 7.30×4.20',3)
 text(p,220,288,'防火门净1.80 / 双扇0.90+0.90 P',3,color=ORANGE)
 text(p,220,301,'无电梯；扶手/净空/耐火等级待定',3)
 bounds=(83.4,33.3,93.8,45.7);xy,q=mapper(447,85,100,bounds);draw_plan(p,d,xy,q,bounds,False)
 for x,y in [(86.4,35.3),(91.6,39.5)]:circle(p,*xy(x,y),c['turn_circle_diameter_m']/2*q,.23,'none',MACHINE,True)
 arrow(p,[xy(86.4,35.3),xy(86.4,39.5),xy(91.6,39.5),xy(91.6,43.6)],MACHINE,False,.3)
 xx,yy=xy(91.6,43.6);text(p,xx,yy-3,'轿厢净3.20×3.80',2.6,'middle');text(p,xx,yy+2,'井道外包3.60×4.20',2.5,'middle')
 xx,yy=xy(91.6,39.5);text(p,xx,yy+4,'前室净4.00×4.00',2.6,'middle')
 dimh(p,xy(83.4,0)[0],xy(89.4,0)[0],73,'机器脊柱6.00',85)
 text(p,429,226,'运输外包1.70×3.10 P',3)
 text(p,429,239,'含舱体1.10×2.30 + 运输余量',2.8)
 text(p,429,252,'整车旋转包络直径3.736 m',3)
 text(p,429,265,'4m空间每侧余量0.132 m',3)
 text(p,429,278,'机器门净2.40 / 每侧0.35余量',2.9)
 text(p,429,291,'轿厢余量：侧0.75 / 端0.35',2.9)
 text(p,429,304,'轮距/挂接/井道机构待设计',2.9)
 text(p,27,251,'每分区两条人员廊接入同一前室；',3)
 text(p,27,264,'4节点均位于主体外侧，不接机器廊。',3)
 text(p,27,277,'每节点1台轿厢仅为尺寸占位；',3)
 text(p,27,290,'台数、运力和无障碍适配未定。',3)
 line(p,26,321,568,321,.18,'#999');legend(p,27,335)
 text(p,27,365,'门叶仅示意；旋转圆验证静态空间，不替代运输机构轨迹、消防或960人疏散评估。',3.1)
 text(p,27,377,'来源：GitHub 71ba463 / 标准层工程简报；Room1 v2 b819189；该层没有正式三维、立面或材质。',3)
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
