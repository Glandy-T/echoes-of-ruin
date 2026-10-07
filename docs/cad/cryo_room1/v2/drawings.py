"""A2 architectural drawings. Identical metre data to native FreeCAD model."""
import math,xml.etree.ElementTree as ET

def make_pages(v,pods,checks):
 pages=[]
 def text(p,x,y,s,size=3.2,anchor='start',color='#222'):
  p['items'].append(dict(k='text',x=x,y=y,s=s,size=size,anchor=anchor,color=color))
 def line(p,x1,y1,x2,y2,lw=.15,color='#222',dash=False):
  p['items'].append(dict(k='line',x1=x1,y1=y1,x2=x2,y2=y2,lw=lw,color=color,dash=dash))
 def rect(p,x,y,w,h,lw=.15,fill='none',color='#222',dash=False):
  p['items'].append(dict(k='rect',x=x,y=y,w=w,h=h,lw=lw,fill=fill,color=color,dash=dash))
 def polygon(p,pts,lw=.15,fill='none',color='#222',dash=False):
  p['items'].append(dict(k='poly',pts=pts,lw=lw,fill=fill,color=color,dash=dash))
 def circle(p,x,y,r,lw=.15,fill='none',color='#555',dash=False):
  p['items'].append(dict(k='circle',x=x,y=y,r=r,lw=lw,fill=fill,color=color,dash=dash))
 def page(code,title,scale):
  p=dict(code=code,title=title,scale=scale,items=[]);pages.append(p)
  rect(p,12,12,570,396,.3);text(p,22,27,title,5);text(p,572,27,code,5,'end')
  line(p,12,34,582,34,.25);line(p,12,388,582,388,.25)
  text(p,22,399,'Echoes of Ruin | Room 1 单室工程验证 | v2 / P = PROVISIONAL',3)
  text(p,572,399,scale+' | A2原尺寸 | 2026-10-07',3,'end');return p
 def dimh(p,x1,x2,y,label,fy=None,size=2.8):
  line(p,x1,y,x2,y,.12)
  for x in [x1,x2]:
   line(p,x-.9,y+.9,x+.9,y-.9,.22)
   if fy is not None:line(p,x,fy,x,y+1.8 if y<fy else y-1.8,.1)
  text(p,(x1+x2)/2,y-1.8,label,size,'middle')
 def dimv(p,y1,y2,x,label,fx=None,size=2.8):
  line(p,x,y1,x,y2,.12)
  for y in [y1,y2]:
   line(p,x-.9,y+.9,x+.9,y-.9,.22)
   if fx is not None:line(p,fx,y,x-1.8 if x>fx else x+1.8,y,.1)
  text(p,x-2,(y1+y2)/2+1,label,size,'end')
 def arrow(p,pts,color='#999'):
  for a,b in zip(pts,pts[1:]):line(p,*a,*b,.18,color)
  a,b=pts[-2:];ang=math.atan2(b[1]-a[1],b[0]-a[0])
  for turn in [-.5,.5]:line(p,*b,b[0]-2.2*math.cos(ang+turn),b[1]-2.2*math.sin(ang+turn),.18,color)
 def mapper(px,py,scale,depth):
  q=1000/scale;return lambda x,y:(px+x*q,py+(depth-y)*q),q
 def cp(x,y,w,d,c):return [(x+c,y),(x+w-c,y),(x+w,y+c),(x+w,y+d-c),(x+w-c,y+d),(x+c,y+d),(x,y+d-c),(x,y+c)]
 def pod(p,a,xy,q,labels=True):
  x,y,w,d=a['x'],a['y'],a['w'],a['d']
  polygon(p,[xy(*pt) for pt in cp(x,y,w,d,v['BaseChamfer'])],.18,'#c9cdd0')
  for inset,c,fill in [(v['BodyInset'],.14,'#e1e3e5'),(v['LidInset'],.16,'#f5f5f5')]:
   polygon(p,[xy(*pt) for pt in cp(x+inset,y+inset,w-2*inset,d-2*inset,c)],.10,fill,'#666')
  wy=y+v['WindowEndInset'] if a['head']=='front' else y+d-v['WindowEndInset']-v['WindowLength']
  polygon(p,[xy(*pt) for pt in cp(x+v['WindowInset'],wy,w-2*v['WindowInset'],v['WindowLength'],.07)],.12,'#aebac0','#555')
  if labels:text(p,*xy(x+w/2,y+d/2),a['id'],3.0,'middle')
 def wall(p,xy,q,x,y,w,d):
  xx,yy=xy(x,y+d);rect(p,xx,yy,w*q,d*q,.20,'#292929')
 def plan(p,px,py,scale):
  W,D,T=v['RoomWidth'],v['RoomDepth'],v['Wall'];xy,q=mapper(px,py,scale,D)
  for x,y,w,d in [(0,0,W,T),(0,T,T,D-2*T),(W-T,T,T,D-2*T),(0,D-T,(W-v['DoorWidth'])/2,T),((W+v['DoorWidth'])/2,D-T,(W-v['DoorWidth'])/2,T)]:wall(p,xy,q,x,y,w,d)
  for a in pods:pod(p,a,xy,q)
  x,y=xy((W+v['DoorWidth'])/2+v['PanelOffset'],D-T);rect(p,x,y,v['PanelWidth']*q,v['PanelDepth']*q,.15,'#666')
  # Dashed threshold denotes a vertically retracting door, not a hinged leaf.
  line(p,*xy((W-v['DoorWidth'])/2,D-T/2),*xy((W+v['DoorWidth'])/2,D-T/2),.14,'#777',True)
  for x in [(W-v['LongAisle'])/2,(W+v['LongAisle'])/2]:line(p,*xy(x,T),*xy(x,D-T),.08,'#bbb',True)
  for y in [(D-v['CrossAisle'])/2,(D+v['CrossAisle'])/2]:line(p,*xy(T,y),*xy(W-T,y),.08,'#bbb',True)
  return xy,q

 W,D,T=v['RoomWidth'],v['RoomDepth'],v['Wall']
 p=page('A301','Room 1 / 标准休眠室建筑方案平面图','1:50')
 px,py=70,120;xy,q=plan(p,px,py,50);bottom=py+D*q;right=px+W*q
 dimh(p,px,right,50,f'{W:.2f} m P / 外包',py)
 dimh(p,px+T*q,right-T*q,64,f'{v["InnerWidth"]:.2f} m / 室内净宽',py)
 chain=[T,v['SideMargin'],v['BlockWidth'],v['LongAisle'],v['BlockWidth'],v['SideMargin'],T]
 labels=['',f'{v["SideMargin"]:.2f}',f'{v["BlockWidth"]:.2f} / 5舱区',f'{v["LongAisle"]:.2f}',f'{v["BlockWidth"]:.2f} / 5舱区',f'{v["SideMargin"]:.2f}','']
 x=px
 for d,s in zip(chain,labels):
  if s:dimh(p,x,x+d*q,83,s,py,2.6)
  x+=d*q
 text(p,px,94,'尺寸链：墙0.20 + 侧余量1.05 + 区块8.05 + 中轴2.40 + 区块8.05 + 侧余量1.05 + 墙0.20 = 21.00 m',2.8)
 dx1=xy((W-v['DoorWidth'])/2,D)[0];dx2=xy((W+v['DoorWidth'])/2,D)[0]
 dimh(p,dx1,dx2,108,'门净宽 1.40 P',py,2.7)
 text(p,px+80,112,'后侧 / 唯一人员门：向上开启',3.0)
 text(p,px+280,112,'门旁壁面认证面板 P',2.8)
 dimv(p,py,bottom,42,f'{D:.2f} m P',px)
 dimv(p,py+T*q,bottom-T*q,58,f'{v["InnerDepth"]:.2f} 净',px)
 a=(D-v['CrossAisle'])/2;b=(D+v['CrossAisle'])/2
 segments=[(D-T,D-T-v['EndMargin'],f'{v["EndMargin"]:.2f}'),(D-T-v['EndMargin'],b,'2.30'),(b,a,'3.50 净'),(a,T+v['EndMargin'],'2.30'),(T+v['EndMargin'],T,f'{v["EndMargin"]:.2f}')]
 for hi,lo,s in segments:dimv(p,xy(W,hi)[1],xy(W,lo)[1],right+14,s,right,2.5)
 text(p,*xy(W*.25,D/2),'中央横向主通道 / 净宽 3.50 m',3.6,'middle')
 text(p,*xy(W*.75,D/2),'长边侧面上下舱 / 四个5舱区块',3.2,'middle')
 arrow(p,[xy(W/2,D-.25),xy(W/2,D/2+.7)])
 arrow(p,[xy(W/2,D/2-.35),xy(W/2,.8)])
 arrow(p,[xy(W/2-.3,D/2+.5),xy(W*.35,D/2+.5)])
 arrow(p,[xy(W/2+.3,D/2+.5),xy(W*.65,D/2+.5)])
 # Person's shoulder/footprint reference is symbolic, not a furniture obstacle.
 hx,hy=xy(W/2,D/2);circle(p,hx,hy,.10*q,.12,'#ddd');line(p,hx-.22*q,hy+.16*q,hx+.22*q,hy+.16*q,.3,'#777')
 gapx=pods[0]['x']+pods[0]['w'];gapend=pods[1]['x']
 dimh(p,*[xy(x,0)[0] for x in [pods[0]['x'],gapx]],330,'1.05 P',bottom)
 dimh(p,*[xy(x,0)[0] for x in [gapx,gapend]],330,'0.70',bottom)
 text(p,px+80,332,'同区重复：1.05 m 舱宽 + 0.70 m 长边操作间距；每区5舱、4间距',3)
 text(p,px,348,'单舱最大外包：1.05 × 2.30 × 1.00 m P；倒角、内收、分层均在外包内。详见 A302。',3.2)
 text(p,px,360,'左右墙边余量各1.05 m；前后端余量各0.50 m；门内入口缓冲带0.50 m。',3.2)
 text(p,px,372,'1.40 m人员门接入2.40 m纵向通道，两侧各展开0.50 m；静态闭舱验证通过，动作待验证。',3.2)
 text(p,512,139,'验证摘要',3.8)
 for i,s in enumerate(['20舱 / 单层平躺','4区 × 每区5舱','净面积187.46 m²','外包面积199.50 m²','实体碰撞：0','净高：TBD','P：设计阶段暂定']):text(p,512,153+i*12,s,2.8)
 text(p,512,264,'坐标：O=左前外角',2.7);text(p,512,276,'+X向右 / +Y向后',2.7)
 text(p,*xy(0,0),'O',2.8,'end')

 p=page('A302','Room 1 / 休眠舱简化几何与长边操作间距','局部 1:10 / 1:25')
 text(p,30,49,'01 单舱平面 / 1:10',4)
 text(p,30,60,'P01头端朝前；后排沿Y镜像观察区。',3)
 a=dict(id='P01',x=0,y=0,w=v['PodWidth'],d=v['PodLength'],head='front');xy,q=mapper(55,85,10,v['PodLength']);pod(p,a,xy,q,False)
 dimh(p,55,55+v['PodWidth']*q,74,f'{v["PodWidth"]:.2f} m P',85)
 dimv(p,85,85+v['PodLength']*q,39,f'{v["PodLength"]:.2f} m',55)
 text(p,107.5,326,'头端 / 观察区',3,'middle')
 text(p,195,49,'02 长边立面 / 1:10',4)
 text(p,195,60,'分层高度占比为P；结构间留0.04 m间隙。',3)
 # Front row head is at left of this long-side elevation.
 sx,sy,q=200,95,100
 for x,z,w,h,fill in [(0,0,v['PodLength'],.2*v['PodHeight'],'#bbc1c5'),(v['BodyInset'],.24*v['PodHeight'],v['PodLength']-2*v['BodyInset'],.4*v['PodHeight'],'#e1e3e5'),(v['LidInset'],.68*v['PodHeight'],v['PodLength']-2*v['LidInset'],.3*v['PodHeight'],'#f1f2f2'),(v['WindowEndInset'],.98*v['PodHeight'],v['WindowLength'],.02*v['PodHeight'],'#aebac0')]:
  rect(p,sx+x*q,sy+(v['PodHeight']-z-h)*q,w*q,h*q,.18,fill)
 dimh(p,sx,sx+v['PodLength']*q,83,'2.30 m',sy)
 dimv(p,sy,sy+v['PodHeight']*q,448,'1.00 P',430)
 for y,s in [(116,'低矮独立舱盖'),(151,'内收卧式主体'),(186,'略厚稳定底座')]:text(p,315,y,s,3.3,'middle')
 text(p,200,211,'观察区位于头部至锁骨稍下；本轮不锁定开盖机构。',3)
 text(p,470,49,'03 端视 / 1:10',4)
 for inset,z,h,fill in [(0,0,.2,'#bbc1c5'),(v['BodyInset'],.24,.4,'#e1e3e5'),(v['LidInset'],.68,.3,'#f1f2f2')]:
  rect(p,465+inset*100,95+(1-z-h)*100,(v['PodWidth']-2*inset)*100,h*100,.18,fill)
 dimh(p,465,465+v['PodWidth']*100,83,'1.05 m P',95)
 text(p,517.5,211,'底座外包控制通道',3,'middle')
 text(p,195,233,'04 相邻舱侧面接近 / 1:25',4)
 xy,q=mapper(205,248,25,v['PodLength'])
 for i in range(2):pod(p,dict(id='P0'+str(i+1),x=i*(v['PodWidth']+v['Gap']),y=0,w=v['PodWidth'],d=v['PodLength'],head='front'),xy,q)
 dimh(p,205+v['PodWidth']*q,205+(v['PodWidth']+v['Gap'])*q,240,'0.70 m 净',248)
 gx=205+(v['PodWidth']+v['Gap']/2)*q;gy=300
 rect(p,gx-.225*q,gy-.125*q,.45*q,.25*q,.1,'none','#888',True)
 text(p,375,264,'虚线人体投影：0.45 × 0.25 m P',3)
 text(p,375,278,'只作比例参照；不证明转身 / 上下舱动作。',3)
 text(p,375,300,'0.70 m按底座最大外包量取。',3.2)
 text(p,375,314,'主体内收后：约0.78 m局部间隙。',3)
 text(p,375,328,'舱盖内收后：约0.82 m局部间隙。',3)
 text(p,30,348,'构造简化 P：底座0.20H；主体Z=0.24H、厚0.40H；舱盖Z=0.68H、厚0.30H；观察区Z=0.98H、厚0.02H。',3)
 text(p,30,360,'底座角部倒角0.12 m；主体每侧内收0.04 m；舱盖每侧内收0.06 m。几何分层与角部为占位设计。',3)
 text(p,30,372,'磨砂观察区采用独立浅层体块示意；玻璃厚度、密封、铰链、内部人体与机械构造均未设计。',3)

 p=page('A303','Room 1 / 实尺参数、尺寸反算与验证结果','米制参数表')
 text(p,30,50,'01 本版实际测量结果',4)
 rows=[('外包宽 × 深',f'{W:.2f} × {D:.2f} m','PROVISIONAL'),('室内净宽 × 深',f'{v["InnerWidth"]:.2f} × {v["InnerDepth"]:.2f} m','由外包与墙厚计算'),('舱体最大外包',f'{v["PodWidth"]:.2f} × {v["PodLength"]:.2f} × {v["PodHeight"]:.2f} m','W/H暂定；L基准'),('中央纵向 / 横向通道','2.40 P / 3.50 m 净','纵向暂定；横向基准'),('同区相邻舱操作间距','0.70 m 净','目标值'),('左右墙边余量','各 1.05 m','净尺寸 / 最外底座'),('前后墙边 / 入口缓冲','各 0.50 m / 后侧0.50 m','不是回转前室'),('墙厚 / 唯一后门净宽','0.20 / 1.40 m','PROVISIONAL')]
 xs=[30,140,273,565];top=60;rh=11
 for x in xs:line(p,x,top,x,top+rh*(len(rows)+1),.12,'#aaa')
 for i in range(len(rows)+2):line(p,xs[0],top+i*rh,xs[-1],top+i*rh,.12,'#aaa')
 for x,s in zip(xs[:-1],['参数','实际值','状态 / 测量口径']):text(p,x+4,top+7,s,3.2)
 for i,row in enumerate(rows):
  for x,s in zip(xs[:-1],row):text(p,x+4,top+(i+1)*rh+7,s,3.0)
 text(p,30,175,'02 v1 / v2 对照与余量反算',4)
 text(p,30,187,'21.00 = 2×0.20 + 2×1.05 + 2(5×1.05 + 4×0.70) + 2.40；9.50 = 2×0.20 + 2×0.50 + 2×2.30 + 3.50。',3.2)
 text(p,30,199,'v2只调整三项参数；20舱四区布局、单舱尺寸、分层形状、朝向和Y坐标均沿用v1。',3)
 xs=[30,141,236,335,425,565];top=209;rh=12
 heads=['项目 / m','v1','v2','变化','状态 / 口径']
 comparison=[['房间外包宽','20.00','21.00','+1.00','PROVISIONAL'],['纵向通道净宽','1.60','2.40','+0.80','PROVISIONAL'],['后门净宽','1.60','1.40','-0.20','PROVISIONAL'],['侧墙净余量 / 每侧','0.95','1.05','+0.10','由布局反算'],['前后端净余量 / 每侧','0.50','0.50','保持','由布局反算']]
 for x in xs:line(p,x,top,x,top+rh*6,.12,'#aaa')
 for i in range(7):line(p,30,top+i*rh,565,top+i*rh,.12,'#aaa')
 for x,s in zip(xs[:-1],heads):text(p,x+3,top+8,s,3)
 for i,row in enumerate(comparison):
  for x,val in zip(xs[:-1],row):text(p,x+3,top+(i+1)*rh+8,val,3)
 text(p,30,299,'门后两侧展开量 = (2.40 - 1.40) / 2 = 0.50 m。人员门与通道宽度分别确定；舱体更换路径留待背部维护系统。',3.1)
 text(p,30,315,'03 原生几何验证 / 范围与来源',4)
 text(p,30,328,'20舱 / 四区各5；实体碰撞0；20个舱外包原生回读一致；原生草图全部约束；参数联动另见QA报告。',3)
 text(p,30,340,'只核验静态闭舱实尺。盖板开启扫掠、人体转身、维修搬运、消防与室内净高仍为待验证项。',3)
 text(p,30,352,'来源：GitHub main / 6ddc2dd（2026-10-07）；ROOM1_ENGINEERING_BRIEF v2决策 + CRYO_FACILITY_LAYOUT。',3)
 text(p,30,364,'80个舱体分层与v1平移对齐后逐一校验形状；原生参数联动、尺寸回读和实体碰撞详见QA报告。',3)
 text(p,30,376,'本版只绘制单室；标准层、整栋休眠楼和园区不在本轮输出范围。修改参数后重建排版页。',3)
 return pages

def to_svg(page):
 root=ET.Element('svg',xmlns='http://www.w3.org/2000/svg',width='594mm',height='420mm',viewBox='0 0 594 420')
 for a in page['items']:
  k=a['k']
  if k=='text':
   e=ET.SubElement(root,'text',{'x':str(a['x']),'y':str(a['y']),'font-size':str(a['size']),'font-family':'SimSun,serif','text-anchor':a['anchor'],'fill':a['color']});e.text=a['s'];continue
  attr={'stroke':a['color'],'stroke-width':str(a['lw']),'fill':a.get('fill','none')}
  if a.get('dash'):attr['stroke-dasharray']='1.5,1'
  if k=='line':attr.update({key:str(a[key]) for key in ['x1','y1','x2','y2']});ET.SubElement(root,'line',attr)
  elif k=='rect':attr.update(x=str(a['x']),y=str(a['y']),width=str(a['w']),height=str(a['h']));ET.SubElement(root,'rect',attr)
  elif k=='circle':attr.update(cx=str(a['x']),cy=str(a['y']),r=str(a['r']));ET.SubElement(root,'circle',attr)
  elif k=='poly':attr['points']=' '.join(f'{x},{y}' for x,y in a['pts']);ET.SubElement(root,'polygon',attr)
 return ET.tostring(root,encoding='unicode')
