"""Measured A2 architectural sheets from the same metre geometry as FreeCAD.

Paper coordinates are mm. P means PROVISIONAL. Publication sheets are
regenerated snapshots; CAD_Live remains associative to native geometry.
"""
import math
import xml.etree.ElementTree as ET

def make_pages(v, features, checks):
    pages=[]
    def text(p,x,y,s,size=3.2,anchor='start',color='#111'):
        p['items'].append(dict(k='text',x=x,y=y,s=s,size=size,anchor=anchor,color=color))
    def line(p,x1,y1,x2,y2,lw=.15,color='#111',dash=False):
        p['items'].append(dict(k='line',x1=x1,y1=y1,x2=x2,y2=y2,lw=lw,color=color,dash=dash))
    def rect(p,x,y,w,h,lw=.15,fill='none',color='#111'):
        p['items'].append(dict(k='rect',x=x,y=y,w=w,h=h,lw=lw,fill=fill,color=color))
    def page(code,title,scale):
        p={'code':code,'title':title,'scale':scale,'items':[]};pages.append(p)
        rect(p,12,12,570,396,.3);text(p,22,27,title,5);text(p,572,27,code,5,'end')
        line(p,12,34,582,34,.25);line(p,12,388,582,388,.25)
        text(p,22,399,'管理设施 | 单层建筑方案 / 空间验证 | v2-R1',3.2)
        text(p,572,399,scale+' | 米制尺寸 | 2026-10-06',3.2,'end');return p
    def dimh(p,x1,x2,y,label,from_y=None):
        line(p,x1,y,x2,y,.12)
        for x in (x1,x2):
            line(p,x-.9,y+.9,x+.9,y-.9,.22)
            if from_y is not None:line(p,x,from_y,x,y-1.8 if y>from_y else y+1.8,.1)
        text(p,(x1+x2)/2,y-1.6,label,2.8,'middle')
    def dimv(p,y1,y2,x,label,from_x=None):
        line(p,x,y1,x,y2,.12)
        for y in (y1,y2):
            line(p,x-.9,y+.9,x+.9,y-.9,.22)
            if from_x is not None:line(p,from_x,y,x+1.8 if x<from_x else x-1.8,y,.1)
        text(p,x-2,(y1+y2)/2+1,label,2.8,'end')
    def mapper(px,py,scale,window):
        wx,wy,ww,wd=window;q=1000/scale
        return lambda x,y:(px+(x-wx)*q,py+(wy+wd-y)*q),q
    def plan(p,px,py,scale,window,subset=None):
        xy,q=mapper(px,py,scale,window)
        for f in subset if subset is not None else features:
            a=f['values'];role=f['role'];kind=f['kind']
            lw=.20 if role=='wall' and f['owner']=='Outer' else .13 if role=='wall' else .12
            color='#222' if role=='wall' else '#444' if role not in ['testcircle','guide'] else '#888'
            if kind=='rect':
                x,y=xy(a['x'],a['y']+a['d']);fill='#292929' if role=='wall' else '#dedede' if role in ['gate','table','chair'] else 'none'
                rect(p,x,y,a['w']*q,a['d']*q,lw,fill,color)
            elif kind=='line':
                x1,y1=xy(a['x1'],a['y1']);x2,y2=xy(a['x2'],a['y2']);line(p,x1,y1,x2,y2,lw,color)
            elif kind=='circle':
                x,y=xy(a['x'],a['y']);p['items'].append(dict(k='circle',x=x,y=y,r=a['r']*q,lw=.10,color=color,fill='none',dash=role=='testcircle'))
            elif kind=='arc':
                x,y=xy(a['x'],a['y']);p['items'].append(dict(k='arc',x=x,y=y,r=a['r']*q,angle=a['angle'],lw=.12,color=color))
        return xy,q
    def label(p,xy,x,y,s,size=3.2,color='#111'):
        px,py=xy(x,y);text(p,px,py,s,size,'middle',color)
    def arrow(p,xy,points):
        points=[xy(*pt) for pt in points]
        for a,b in zip(points,points[1:]):line(p,*a,*b,.18,'#a0a0a0')
        a,b=points[-2:];ang=math.atan2(b[1]-a[1],b[0]-a[0]);l=2.2
        for turn in [-.5,.5]:line(p,*b,b[0]-l*math.cos(ang+turn),b[1]-l*math.sin(ang+turn),.18,'#a0a0a0')
    W,D=v['EnvelopeWidth'],v['EnvelopeDepth'];sx=v['StaffX'];sy=v['StaffY'];t=v['OuterWall']
    sw,sd=v['StaffWidth'],v['StaffDepth'];sc=sx+sw/2;pw,pd=v['PublicWCWidth'],v['PublicWCDepth'];pwy=v['PublicWCY'];ae=t+v['AuthDepth']
    wcx=sx+(sw-v['StaffWCWidth'])/2;wcy=sy+(sd-v['StaffWCDepth'])/2
    p=page('A201','管理设施单层建筑方案平面图','1:150（A2原尺寸）')
    xy,q=plan(p,70,70,150,(0,0,W,D))
    dimh(p,70,70+W*q,46,f'{W:.2f} m  验证基准',70);dimv(p,70,70+D*q,51,f'{D:.2f} m 基准',70)
    rear=[(W/2-v['RearOffset'],v['RearSideOpening']),(W/2,v['RearCenterOpening']),(W/2+v['RearOffset'],v['RearSideOpening'])]
    for i,(cx,w) in enumerate(rear):
        x1,_=xy(cx-w/2,D);x2,_=xy(cx+w/2,D);dimh(p,x1,x2,61,f'{w:.1f} P',70)
        label(p,xy,cx,D-1.8,['后出口 1','后出口 2','后出口 3'][i],3)
    text(p,70+W*q/2,38.5,'后侧 / 园区',3,'middle','#555')
    for i,letter in enumerate('ABCDEFGHIJ'):
        cx=W/10*(i+.5);label(p,xy,cx,1.35,letter,4);label(p,xy,cx,3.55,'自动认证',2.7);label(p,xy,cx,ae-.65,f'{v["GateCount"]} 通道 P',2.3,'#666')
    label(p,xy,W/2,-1.6,'正面 / A–J 连续入口',3.4)
    cx=W/20;ax,_=xy(cx-v['FrontOpening']/2,0);bx,_=xy(cx+v['FrontOpening']/2,0);dimh(p,ax,bx,381,f'{v["FrontOpening"]:.2f} P',370)
    label(p,xy,W/2,ae+(sy-ae)*.54,'共享汇流大厅',5);label(p,xy,W/2,ae+(sy-ae)*.35,'认证后共享 / 主流线绕行中央工作人员区',2.6,'#666')
    label(p,xy,sc,sy+sd-2,'工作人员 / 异常处理区',3.8);label(p,xy,sc,sy+sd-3.5,f'{sw:.2f} × {sd:.2f} m',3.2);label(p,xy,sc,wcy+v['StaffWCDepth']*.43,'内部厕所 P',2.4)
    for cx in [t+pw*.5625,W-t-pw*.5625]:label(p,xy,cx,pwy+pd*.53,'公共厕所 P',2.9);label(p,xy,cx,pwy+pd*.44,f'{pw:g} × {pd:g} m',2.6,'#555')
    for cx in [t+v['Partition']+v['UniversalWidth']/2,W-t-v['Partition']-v['UniversalWidth']/2]:label(p,xy,cx,pwy+v['Partition']+.45,'通用 P',2.1)
    for cx in [1.25,W-1.25]:label(p,xy,cx,pwy+pd+v['GuideYGap']+.9,'地图',2.5,'#666')
    a,_=xy(sx,sy+sd);b,_=xy(sx+sw,sy+sd);dimh(p,a,b,xy(0,sy+sd+1.2)[1],f'{sw:.2f} m 已确认')
    y1=xy(0,sy+sd)[1];y2=xy(0,sy)[1];dimv(p,y1,y2,b+8,f'{sd:.2f} 已确认',b)
    for left,right in [(t+v['PublicWCWidth'],sx),(sx+v['StaffWidth'],W-t-v['PublicWCWidth'])]:
        a,y=xy(left,pwy+pd*.7);b,_=xy(right,pwy+pd*.7);dimh(p,a,b,y,f'{right-left:.2f} m P 净间距')
    x=70+W*q+24;ys=[D,sy+sd,sy,ae,0];dims=[f'{D-sy-sd:.2f} P',f'{sd:.2f} 已确认',f'{sy-ae:.2f} P',f'{ae:.2f} P']
    for hi,lo,s in zip(ys,ys[1:],dims):dimv(p,xy(W,hi)[1],xy(W,lo)[1],x,s,70+W*q)
    arrow(p,xy,[(9.75,2),(9.75,11),(17,16),(17,37),(10.5,41)]);arrow(p,xy,[(55.25,2),(55.25,11),(48,16),(48,37),(54.5,41)])
    arrow(p,xy,[(48,sy+sd+4),(W/2,sy+sd+4),(W/2,D-4)]);arrow(p,xy,[(sc,sy-4),(sc,sy-1)])
    label(p,xy,sc+2.7,sy-1.75,'异常分流',2.5,'#888');text(p,346,382,'P = PROVISIONAL / 暂定；待确认项见 A203',2.7)

    p=page('A202','管理设施局部放大平面图','详见各局部比例（A2原尺寸）')
    text(p,30,49,'01 工作人员 / 异常处理区',4);text(p,30,58,f'边界 {sw:g}×{sd:g} m 已确认；内部布局 P | 1:100',3)
    staff=[f for f in features if f['owner']=='Staff'];sxy,sq=plan(p,35,81,100,(sx,sy,sw,sd),staff)
    dimh(p,35,35+sw*sq,70,f'{sw:.2f} 已确认',81);dimv(p,81,81+sd*sq,25,f'{sd:.2f}',35)
    label(p,sxy,sc,sy+sd-2,'工作人员 / 异常处理',3.6);label(p,sxy,sc,wcy+1.6,'内部厕所',3.1);label(p,sxy,sc,wcy+.9,f'{v["StaffWCWidth"]:g}×{v["StaffWCDepth"]:g} m P',2.7);label(p,sxy,sc,sy+2,f'门洞 {v["StaffOpening"]:.2f} P',2.8)
    text(p,35,219,f'墙体计入{sw:g}×{sd:g} m边界；内部厕所外包{v["StaffWCWidth"]:g}×{v["StaffWCDepth"]:g} m。',2.9);text(p,35,228,f'工作台与座位仅为{v["TableCount"]}处异常处理占位（P）。',2.9)
    text(p,272,49,'02 左公共厕所（右侧镜像）',4);text(p,272,58,f'外包 {pw:g}×{pd:g} m P | 1:75',3)
    public=[f for f in features if f['owner']=='PublicL'];pxy,pq=plan(p,285,81,75,(t,pwy,pw,pd),public)
    dimh(p,285,285+pw*pq,70,f'{pw:.2f} P',81);dimv(p,81,81+pd*pq,274,f'{pd:.2f} P',285)
    label(p,pxy,t+pw*.5625,pwy+pd*.5,'公共厕所',3.4);label(p,pxy,t+v['Partition']+v['UniversalWidth']/2,pwy+v['Partition']+.45,'通用厕间 P',2.8);label(p,pxy,t+v['Partition']+v['UniversalTurnX'],pwy+v['Partition']+v['UniversalTurnY'],'测试圆',2.2,'#888')
    text(p,285,234,f'{v["StallCount"]}普通厕间 + 1通用厕间 / 每侧（P）',2.9);text(p,285,244,f'普通净{v["StallWidth"]:.2f}×{v["StallDepth"]:.2f}；通用净{v["UniversalWidth"]:.2f}×{v["UniversalDepth"]:.2f} m。',2.8);text(p,285,254,f'{v["TurnDiameter"]:.2f} m测试圆及图示洁具仅作几何检查。',2.8)
    text(p,440,49,'03 入口 A / 认证组',4);text(p,440,58,'其余B–J同组重复 | 1:75',3)
    auth=[f for f in features if f['owner']=='AuthA' or f['name'] in ['Outer_Front_0','Outer_Front_1','FrontSlider_0','FrontSliderCenter_0','Outer_Left','AuthPartition_1']]
    local=[];aw=W/10+v['Partition']/2
    for f in auth:
        if f['kind']=='rect':
            a=dict(f['values']);x0=max(0,a['x']);x1=min(aw,a['x']+a['w']);y0=max(0,a['y']);y1=min(ae,a['y']+a['d'])
            if x1<=x0 or y1<=y0:continue
            local.append(dict(f,values=dict(a,x=x0,y=y0,w=x1-x0,d=y1-y0)))
        else:local.append(f)
    axy,aq=plan(p,457,81,75,(0,0,aw,ae),local);dimh(p,457,457+W/10*aq,70,f'{W/10:.2f} P 组中心节距',81)
    label(p,axy,W/20,1.2,'A 入口',3.5);label(p,axy,W/20,3.6,'自动认证区',3.3);label(p,axy,W/20,ae-.6,'开放接入共享大厅',2.6);dimv(p,81,81+ae*aq,448,f'{ae:.2f} P',457)
    text(p,443,221,f'前开口 {v["FrontOpening"]:.2f} m；{v["GateCount"]}条认证通道 P。',2.8);text(p,443,231,f'净宽{v["GateWide"]:.2f} / {v["GateStandard"]:.2f}；设备长{v["GateLength"]:.2f} m。',2.8);text(p,443,241,f'闸机设备组总宽{checks["gate_footprint_m"]:.2f} m P。',2.8)
    line(p,30,274,564,274,.2);text(p,30,291,'本轮设计阶段暂定值（P / PROVISIONAL）',4)
    text(p,30,307,f'外墙{t:.2f} m；隔墙{v["Partition"]:.2f} m；公共厕所入口{v["PublicOpening"]:.2f} m；通用门{v["UniversalOpening"]:.2f} m；普通门{v["StallOpening"]:.2f} m。',3.2)
    text(p,30,320,f'工作人员内部厕所门{v["StaffWCOpening"]:.2f} m；门扇、洁具、工作台与地图均为可测量的简化占位。',3.2)
    text(p,30,338,'边界与尺寸均使用同一建筑坐标；局部放大保留主图坐标关系。',3.2)
    text(p,30,352,'门扇开启方向为方案测试；无障碍、疏散、结构与机电合规复核 TBD。',3.2)

    p=page('A203','参数与待确认事项（辅助审查页）','不按比例')
    text(p,28,53,'已确认 / 当前验证基准',4)
    text(p,28,68,'单层；A–J十入口；认证后共享大厅；中央工作人员与内部厕所；左右公共厕所；三后出口。',3.3)
    text(p,28,82,f'工作人员区边界{sw:g}×{sd:g} m：用户确认。建筑外包{W:g}×{D:g} m：当前验证基准，最终外包待确认。',3.3)
    text(p,28,107,'本轮 PROVISIONAL 参数',4)
    rows=[('墙 / 门',f'外墙{t:.2f}；隔墙{v["Partition"]:.2f}；前开口{v["FrontOpening"]:.2f}；后开口{v["RearSideOpening"]:g} / {v["RearCenterOpening"]:g} / {v["RearSideOpening"]:g} m；门型及开启P。'),
          ('定位',f'工作人员X={sx:.2f}，Y={sy:.2f}；两公共厕所Y={pwy:.2f} m，均以外边界定位。'),
          ('工作人员',f'内部厕所外包{v["StaffWCWidth"]:g}×{v["StaffWCDepth"]:g} m，居中；工作人员门{v["StaffOpening"]:.2f}；内部厕所门{v["StaffWCOpening"]:.2f}；{v["TableCount"]}处工作台。'),
          ('公共厕所',f'每侧外包{pw:g}×{pd:g} m；{v["StallCount"]}普通+1通用；普通净{v["StallWidth"]:.2f}×{v["StallDepth"]:.2f}；通用净{v["UniversalWidth"]:.2f}×{v["UniversalDepth"]:.2f} m。'),
          ('认证组',f'每组{v["GateCount"]}通道，净宽{v["GateWide"]:.2f} / {v["GateStandard"]:.2f}；条宽{v["GateBarrier"]:.2f}、长{v["GateLength"]:.2f}；前端Y={v["GateY"]:.2f}；净深{v["AuthDepth"]:.2f} m。'),
          ('几何余量',f'大厅左/右净间距{checks["left_clear_gap_m"]:.2f}/{checks["right_clear_gap_m"]:.2f}；前净深{checks["front_merge_depth_m"]:.2f}；后净深{checks["rear_clear_depth_m"]:.2f} m；仅是布局结果。')]
    for i,(a,b) in enumerate(rows):text(p,28,125+i*14,a,3.2);text(p,83,125+i*14,b,3.1)
    line(p,28,212,566,212,.2);text(p,28,230,'面积 / 参数修改',4)
    text(p,28,245,f'外包面积{W*D:g} m²；工作人员边界{sw*sd:g} m²（含内部厕所{v["StaffWCWidth"]*v["StaffWCDepth"]:g} m²）；两公共厕所合计{2*pw*pd:g} m²。',3.2)
    text(p,28,258,'各分区数字为方案边界面积，包含其墙体；不代表净使用面积或容纳人数。',3.2)
    text(p,28,272,'FreeCAD Parameters内长度/XY直接驱动草图和A204；ParameterTable列出状态与单位。',3.2)
    text(p,28,285,'出版页为快照；用build_freecad.py --parameters-from 已修改文件.FCStd重建，再运行GUI宏与PDF导出。',3.2)
    text(p,28,310,'仍需确认 / TBD',4)
    text(p,28,325,'最终外包与各P参数；厕位配置与通用厕间要求；门型/开启；工作人员真实设备与控制范围。',3.2)
    text(p,28,338,'结构、标高、层高、屋面、机电、防火疏散与适用规范；导视信息及园区出口衔接。',3.2)
    text(p,28,351,'峰值到场率、认证服务时间、失败分流比例、出口流率及大厅停留时间：未输入，吞吐结论TBD。',3.2)
    text(p,28,373,'依据：CRYO_FACILITY_LAYOUT现行版 / REDRAW_BRIEF；仅几何适配通过，尚未验证法规或运行容量。',2.8)
    return pages

def to_svg(page):
    root=ET.Element('svg',{'xmlns':'http://www.w3.org/2000/svg','width':'594mm','height':'420mm','viewBox':'0 0 594 420'})
    ET.SubElement(root,'rect',dict(width='594',height='420',fill='white'))
    for a in page['items']:
        k=a['k'];color=a.get('color','#111')
        if k=='text':
            e=ET.SubElement(root,'text',{'x':str(a['x']),'y':str(a['y']),'font-size':str(a['size']),'font-family':'SimSun, Microsoft YaHei, sans-serif','text-anchor':a['anchor'],'fill':color});e.text=a['s'];continue
        attr={'stroke':color,'stroke-width':str(a['lw']),'fill':a.get('fill','none')}
        if a.get('dash'):attr['stroke-dasharray']='1.5 1'
        if k=='rect':attr.update(x=str(a['x']),y=str(a['y']),width=str(a['w']),height=str(a['h']))
        elif k=='line':attr.update({key:str(a[key]) for key in ['x1','y1','x2','y2']})
        elif k=='circle':attr.update(cx=str(a['x']),cy=str(a['y']),r=str(a['r']))
        elif k=='arc':
            r=a['r'];b=math.radians(a['angle']);x,y=a['x'],a['y'];sx=x+r*math.cos(b);sy=y-r*math.sin(b);ex=x+r*math.cos(b+math.pi/2);ey=y-r*math.sin(b+math.pi/2)
            attr['d']=f'M {sx} {sy} A {r} {r} 0 0 0 {ex} {ey}';k='path'
        ET.SubElement(root,k,attr)
    return ET.tostring(root,encoding='unicode')
