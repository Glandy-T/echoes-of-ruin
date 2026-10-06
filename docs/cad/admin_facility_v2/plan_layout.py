"""Architectural planning geometry in metres. P = user-authorized provisional.

All coordinates share X left-to-right and Y front-to-rear. Geometry expressions
also drive native FreeCAD Sketcher objects. Count changes require regeneration.
"""
import math

PARAMETERS = {
    'EnvelopeWidth': (65., '基准', '当前外包宽'),
    'EnvelopeDepth': (45., '基准', '当前外包进深'),
    'StaffWidth': (20., 'PROVISIONAL', 'FINAL_PASS工作人员区测试外包宽'),
    'StaffDepth': (14., 'PROVISIONAL', 'FINAL_PASS工作人员区测试外包深'),
    'OuterWall': (.30, 'PROVISIONAL', '外墙图示厚度，计入外包内'),
    'Partition': (.20, 'PROVISIONAL', '隔墙图示厚度，计入各区外边界内'),
    'AuthDepth': (8., 'PROVISIONAL', '认证区从前外墙内面起的进深'),
    'FrontOpening': (2.5, 'PROVISIONAL', '前入口组开口，沿用历史草图测试值'),
    'RearSideOpening': (6., 'PROVISIONAL', '左右后出口开口，历史草图测试值'),
    'RearCenterOpening': (8., 'PROVISIONAL', '中央后出口开口，历史草图测试值'),
    'RearOffset': (22., 'PROVISIONAL', '左右后出口中心距建筑中轴'),
    'StaffY': (20., 'PROVISIONAL', '保持原中心Y=27 m的测试前边界'),
    'StaffX': (22.5, 'PROVISIONAL', '保持建筑中轴X=32.5 m的测试左边界'),
    'StaffOpening': (1.2, 'PROVISIONAL', '工作人员区前侧门洞'),
    'StaffWCWidth': (4.5, 'PROVISIONAL', '工作人员卫生间测试外包宽'),
    'StaffWCDepth': (4., 'PROVISIONAL', '工作人员卫生间测试外包深'),
    'StaffWCOpening': (1., 'PROVISIONAL', '卫生间前侧门洞，外开测试'),
    'StaffStallWidth': (1.95, 'PROVISIONAL', '工作人员独立隔间图示净宽'),
    'StaffStallDepth': (2., 'PROVISIONAL', '工作人员独立隔间图示净深'),
    'StaffStallOpening': (1., 'PROVISIONAL', '工作人员独立隔间门洞'),
    'StaffStallDoorInset': (.10, 'PROVISIONAL', '两隔间门向共享中部偏移，避开洗手位'),
    'DoorApproachDepth': (1., 'PROVISIONAL', '各平开门两侧接近空间测试深度，非规范认证'),
    'StaffTurnDiameter': (1.2, 'PROVISIONAL', '工作人员卫生间正常转身空间测试圆，非轮椅认证'),
    'PublicWCWidth': (8., 'PROVISIONAL', '每侧公共厕所外边界宽'),
    'PublicWCDepth': (10., 'PROVISIONAL', '每侧公共厕所外边界深'),
    'PublicWCY': (21., 'PROVISIONAL', '公共厕所外边界前侧Y'),
    'PublicOpening': (1.2, 'PROVISIONAL', '公共厕所朝大厅的门洞'),
    'PublicDoorOffset': (4.4, 'PROVISIONAL', '公共厕所门洞起点距前边界'),
    'LargeWidth': (3., 'PROVISIONAL', '较大独立隔间图示净宽'),
    'LargeDepth': (3., 'PROVISIONAL', '较大独立隔间图示净深'),
    'LargeOpening': (1.1, 'PROVISIONAL', '较大独立隔间门洞'),
    'TurnDiameter': (1.5, 'PROVISIONAL', '空间测试圆直径，非合规认证'),
    'StallWidth': (1.75, 'PROVISIONAL', '公共后排普通独立隔间图示净宽'),
    'PublicFrontStallWidth': (2.1, 'PROVISIONAL', '公共前排普通独立隔间图示净宽'),
    'StallDepth': (2.2, 'PROVISIONAL', '公共普通独立隔间图示净深'),
    'StallOpening': (1., 'PROVISIONAL', '公共普通独立隔间门洞'),
    'GateWide': (1.2, 'PROVISIONAL', '每组首条通道图示净宽'),
    'GateStandard': (.9, 'PROVISIONAL', '其他认证通道图示净宽'),
    'GateBarrier': (.18, 'PROVISIONAL', '闸机设备条宽'),
    'GateLength': (1.6, 'PROVISIONAL', '闸机设备条长'),
    'GateFence': (.10, 'PROVISIONAL', '闸机组两侧挡栏图示厚度'),
    'GateY': (5., 'PROVISIONAL', '闸机设备前端Y'),
    'DoorLeaf': (.05, 'PROVISIONAL', '滑门图示扇厚'),
    'FixtureWidth': (.5, 'PROVISIONAL', '简化坐便器占位宽'),
    'FixtureDepth': (.7, 'PROVISIONAL', '简化坐便器占位深'),
    'BasinWidth': (.6, 'PROVISIONAL', '简化洗面台占位宽'),
    'BasinDepth': (.5, 'PROVISIONAL', '简化洗面台占位深'),
    'TableWidth': (1.8, 'PROVISIONAL', 'A–J监控/日志工位桌面宽'),
    'TableDepth': (.8, 'PROVISIONAL', 'A–J监控/日志工位桌面深'),
    'ChairWidth': (.55, 'PROVISIONAL', '工作台座位占位'),
    'GuideWidth': (4., 'CONFIRMED', '封盘要求：地图正面宽'),
    'GuideDepth': (.15, 'PROVISIONAL', '地图占位厚度'),
    'StaffTableYInset': (1.8, 'PROVISIONAL', '前排工位前端距工作人员区前边界'),
    'TableGap': (.8, 'PROVISIONAL', '同排桌面之间间距，非指定通道'),
    'TableRowPitch': (3.6, 'PROVISIONAL', '两排桌面前端纵向节距'),
    'ChairGap': (.45, 'PROVISIONAL', '座位与工作台图示间距'),
    'ChairRetreat': (.6, 'PROVISIONAL', '座椅后额外退让区进深'),
    'ChairZoneWidth': (.8, 'PROVISIONAL', '座椅后退让测试区宽'),
    'StaffClearanceTest': (1.2, 'PROVISIONAL', '内部通路几何测试目标，非规范标准'),
    'MonitorWidth': (.55, 'PROVISIONAL', '每块监控屏平面占位宽'),
    'MonitorDepth': (.12, 'PROVISIONAL', '监控屏平面占位深'),
    'MonitorGap': (.15, 'PROVISIONAL', '双屏横向间距'),
    'MonitorFrontInset': (.10, 'PROVISIONAL', '屏幕距桌面前端偏移'),
    'StaffToiletRearGap': (.20, 'PROVISIONAL', '内部坐便器距后内墙余量'),
    'BasinMargin': (.15, 'PROVISIONAL', '内部/通用洗面台距侧后内墙余量'),
    'LargeTurnX': (1.8, 'PROVISIONAL', '较大隔间测试圆心距左内面'),
    'LargeTurnY': (1.2, 'PROVISIONAL', '较大隔间测试圆心距前内面'),
    'LargeToiletXOffset': (.45, 'PROVISIONAL', '较大隔间坐便器距左内面偏移'),
    'LargeToiletFrontGap': (.45, 'PROVISIONAL', '较大隔间坐便器距前内面余量'),
    'StallToiletRearGap': (.25, 'PROVISIONAL', '普通厕间坐便器后侧余量'),
    'PublicBasinY': (3.55, 'PROVISIONAL', '共享洗手区首台距公共节点前边界'),
    'PublicBasinPitch': (1.05, 'PROVISIONAL', '共享洗面台侧墙纵向节距'),
    'GuideYInset': (2., 'PROVISIONAL', '地图前端距工作人员区前侧Y；正面朝-Y'),
}
COUNTS = {'GateCount': (2,'PROVISIONAL','每组认证通道数；修改数量须重建'),
          'StallCount': (4,'PROVISIONAL','每侧公共后排独立隔间数'),
          'PublicFrontStallCount': (2,'PROVISIONAL','每侧公共前排普通独立隔间数；另有1较大隔间'),
          'StaffStallCount': (2,'已确认','工作人员卫生间2个全封闭独立隔间'),
          'StaffBasinCount': (2,'已确认','工作人员卫生间2个洗手位'),
          'BasinCount': (3,'PROVISIONAL','每側公共洗面台数；修改数量须重建'),
          'WorkstationCount': (10,'已确认','A–J十个监控/日志工位，当前两排五个')}

def make_layout(overrides=None):
    values = {k:v[0] for k,v in PARAMETERS.items()}
    values.update({k:v[0] for k,v in COUNTS.items()})
    if overrides: values.update(overrides)
    assert values['WorkstationCount']==10, '当前权威要求必须保留A–J十个工位'
    assert values['StaffStallCount']==2 and values['StaffBasinCount']==2
    def number(expr): return eval(str(expr), {'__builtins__':{}}, values)
    features=[]
    def add(kind,name,role,owner,**kwargs):
        item=dict(kind=kind,name=name,role=role,owner=owner,**{k:str(v) for k,v in kwargs.items()})
        features.append(item)
        return item
    def rect(name,role,owner,x,y,w,d): return add('rect',name,role,owner,x=x,y=y,w=w,d=d)
    def line(name,owner,x1,y1,x2,y2,role='door'): return add('line',name,role,owner,x1=x1,y1=y1,x2=x2,y2=y2)
    def circle(name,owner,x,y,r,role='testcircle'): return add('circle',name,role,owner,x=x,y=y,r=r)
    def door(name,owner,hx,hy,w,arc_angle,leaf_angle):
        add('arc',name+'_Swing','door',owner,x=hx,y=hy,r=w,angle=arc_angle)
        dx,dy=round(math.cos(math.radians(leaf_angle))),round(math.sin(math.radians(leaf_angle)))
        line(name+'_Leaf',owner,hx,hy,f'({hx})+({w})*{dx}',f'({hy})+({w})*{dy}')
    def wall(name,owner,x,y,w,d): return rect(name,'wall',owner,x,y,w,d)
    W='EnvelopeWidth';D='EnvelopeDepth';T='OuterWall';P='Partition'
    SX='StaffX';SY='StaffY'
    WX=f'({SX})+(StaffWidth-StaffWCWidth)/2';WY='StaffY+StaffDepth-StaffWCDepth'
    # Outer wall cut-outs are genuine openings. All wall strips lie inside 65x45.
    fronts=[(f'(EnvelopeWidth/10)*{i+.5}-FrontOpening/2',f'(EnvelopeWidth/10)*{i+.5}+FrontOpening/2') for i in range(10)]
    rears=[('EnvelopeWidth/2-RearOffset-RearSideOpening/2','EnvelopeWidth/2-RearOffset+RearSideOpening/2'),
           ('EnvelopeWidth/2-RearCenterOpening/2','EnvelopeWidth/2+RearCenterOpening/2'),
           ('EnvelopeWidth/2+RearOffset-RearSideOpening/2','EnvelopeWidth/2+RearOffset+RearSideOpening/2')]
    for label,intervals,y in [('Front',fronts,'0'),('Rear',rears,'EnvelopeDepth-OuterWall')]:
        previous='0'
        for i,(a,b) in enumerate(intervals):
            wall(f'Outer_{label}_{i}','Outer',previous,y,f'({a})-({previous})',T)
            rect(f'{label}Slider_{i}','door','Outer',a,f'({y})+OuterWall/2-DoorLeaf/2',f'({b})-({a})','DoorLeaf')
            line(f'{label}SliderCenter_{i}','Outer',f'(({a})+({b}))/2',y,f'(({a})+({b}))/2',f'({y})+OuterWall')
            previous=b
        wall(f'Outer_{label}_End','Outer',previous,y,f'EnvelopeWidth-({previous})',T)
    wall('Outer_Left','Outer','0','OuterWall','OuterWall','EnvelopeDepth-2*OuterWall')
    wall('Outer_Right','Outer','EnvelopeWidth-OuterWall','OuterWall','OuterWall','EnvelopeDepth-2*OuterWall')
    for i in range(1,10): wall(f'AuthPartition_{i}','Auth',f'EnvelopeWidth/10*{i}-Partition/2','OuterWall','Partition','AuthDepth')
    footprint='GateWide+(GateCount-1)*GateStandard+(GateCount+1)*GateBarrier'
    for i,letter in enumerate('ABCDEFGHIJ'):
        left=f'EnvelopeWidth/10*{i+.5}-({footprint})/2'
        for j in range(int(values['GateCount'])+1):
            offset='0' if j==0 else f'{j}*GateBarrier+GateWide+{j-1}*GateStandard'
            rect(f'Gate_{letter}_{j}','gate','Auth'+letter,f'({left})+({offset})','GateY','GateBarrier','GateLength')
        bay_left='OuterWall' if i==0 else f'EnvelopeWidth/10*{i}+Partition/2'
        bay_right='EnvelopeWidth-OuterWall' if i==9 else f'EnvelopeWidth/10*{i+1}-Partition/2'
        rect(f'GateFence_{letter}_Left','gate','Auth'+letter,bay_left,'GateY+GateLength/2-GateFence/2',f'({left})-({bay_left})','GateFence')
        rect(f'GateFence_{letter}_Right','gate','Auth'+letter,f'({left})+({footprint})','GateY+GateLength/2-GateFence/2',f'({bay_right})-({left})-({footprint})','GateFence')
    # FINAL_PASS provisional boundary; wall thickness is inside the envelope.
    def enclosed(name,owner,x,y,w,d,opening,outward=False):
        a=f'({x})+(({w})-({opening}))/2';b=f'({a})+({opening})'
        wall(name+'_FrontL',owner,x,y,f'({a})-({x})',P)
        wall(name+'_FrontR',owner,b,y,f'({x})+({w})-({b})',P)
        wall(name+'_Back',owner,x,f'({y})+({d})-Partition',w,P)
        wall(name+'_Left',owner,x,f'({y})+Partition',P,f'({d})-2*Partition')
        wall(name+'_Right',owner,f'({x})+({w})-Partition',f'({y})+Partition',P,f'({d})-2*Partition')
        door(name+'_Door',owner,a,y if outward else f'({y})+Partition',opening,270 if outward else 0,270 if outward else 90)
    enclosed('Staff','Staff',SX,SY,'StaffWidth','StaffDepth','StaffOpening')
    enclosed('StaffWC','Staff',WX,WY,'StaffWCWidth','StaffWCDepth','StaffWCOpening',True)
    sfy=f'({WY})+StaffWCDepth-Partition-StaffStallDepth'
    for i in range(2):
        xx=f'({WX})+Partition+{i}*(StaffStallWidth+Partition)';shift=1 if i==0 else -1
        hole=f'({xx})+(StaffStallWidth-StaffStallOpening)/2+{shift}*StaffStallDoorInset'
        wall(f'StaffStall_{i}_FL','Staff',xx,f'({sfy})-Partition',f'({hole})-({xx})',P)
        wall(f'StaffStall_{i}_FR','Staff',f'({hole})+StaffStallOpening',f'({sfy})-Partition',f'({xx})+StaffStallWidth-({hole})-StaffStallOpening',P)
        wall(f'StaffStall_{i}_Side','Staff',f'({xx})+StaffStallWidth',f'({sfy})-Partition',P,'StaffStallDepth+Partition')
        door(f'StaffStall_{i}_Door','Staff',hole,sfy,'StaffStallOpening',0,90)
        rect(f'StaffStall_{i}_Toilet','fixture','Staff',f'({xx})+(StaffStallWidth-FixtureWidth)/2',f'({WY})+StaffWCDepth-Partition-FixtureDepth-StaffToiletRearGap','FixtureWidth','FixtureDepth')
    for i in range(2):
        bx=f'({WX})+Partition' if i==0 else f'({WX})+StaffWCWidth-Partition-BasinDepth'
        rect(f'StaffBasin_{i}','basin','Staff',bx,f'({WY})+Partition+BasinMargin','BasinDepth','BasinWidth')
    circle('StaffWC_Turn','Staff',f'({WX})+StaffWCWidth/2',f'({WY})+Partition+StaffTurnDiameter/2+BasinMargin','StaffTurnDiameter/2')
    row_span='5*TableWidth+4*TableGap'
    for i,letter in enumerate('ABCDEFGHIJ'):
        row,col=divmod(i,5)
        tx=f'StaffX+(StaffWidth-({row_span}))/2+{col}*(TableWidth+TableGap)'
        ty=f'StaffY+StaffTableYInset+{row}*TableRowPitch'
        rect(f'Workstation_{letter}','table','Staff',tx,ty,'TableWidth','TableDepth')
        rect(f'StaffChair_{letter}','chair','Staff',f'({tx})+(TableWidth-ChairWidth)/2',f'({ty})+TableDepth+ChairGap','ChairWidth','ChairWidth')
        rect(f'ChairRetreat_{letter}','clearance','Staff',f'({tx})+(TableWidth-ChairZoneWidth)/2',f'({ty})+TableDepth+ChairGap+ChairWidth','ChairZoneWidth','ChairRetreat')
        for screen in range(2):
            mx=f'({tx})+(TableWidth-2*MonitorWidth-MonitorGap)/2+{screen}*(MonitorWidth+MonitorGap)'
            rect(f'Monitor_{letter}_{screen+1}','monitor','Staff',mx,f'({ty})+MonitorFrontInset','MonitorWidth','MonitorDepth')
    # Public left node, mirrored to right. Cubicle sizes are clear inside faces.
    before=len(features); X='OuterWall';Y='PublicWCY';PW='PublicWCWidth';PD='PublicWCDepth'
    wall('PubL_Front','PublicL',X,Y,PW,P)
    wall('PubL_Back','PublicL',X,f'({Y})+PublicWCDepth-Partition',PW,P)
    wall('PubL_Left','PublicL',X,f'({Y})+Partition',P,'PublicWCDepth-2*Partition')
    hx='OuterWall+PublicWCWidth-Partition';hy='PublicWCY+PublicDoorOffset'
    wall('PubL_Right1','PublicL',hx,'PublicWCY+Partition',P,'PublicDoorOffset-Partition')
    wall('PubL_Right2','PublicL',hx,'PublicWCY+PublicDoorOffset+PublicOpening',P,'PublicWCDepth-Partition-PublicDoorOffset-PublicOpening')
    door('PubL_Entry','PublicL',hx,hy,'PublicOpening',90,180)
    ux='OuterWall+Partition';uy='PublicWCY+Partition'
    # Front row: one larger room + two ordinary rooms, all fully enclosed.
    def front_room(name,xx,width,depth,opening,large=False):
        rear=f'PublicWCY+Partition+({depth})';hole=f'({xx})+(({width})-({opening}))/2'
        wall(name+'_BackL','PublicL',xx,rear,f'({hole})-({xx})',P)
        wall(name+'_BackR','PublicL',f'({hole})+({opening})',rear,f'({width})-(({opening})+({width}))/2',P)
        wall(name+'_Side','PublicL',f'({xx})+({width})',uy,P,depth)
        door(name+'_Door','PublicL',hole,rear,opening,270,270)
        fx=f'({xx})+LargeToiletXOffset' if large else f'({xx})+(({width})-FixtureWidth)/2'
        fy='PublicWCY+Partition+LargeToiletFrontGap' if large else 'PublicWCY+Partition+StallToiletRearGap'
        rect(name+'_Toilet','fixture','PublicL',fx,fy,'FixtureWidth','FixtureDepth')
    front_room('LargeL',ux,'LargeWidth','LargeDepth','LargeOpening',True)
    circle('LargeL_Turn','PublicL','OuterWall+Partition+LargeTurnX','PublicWCY+Partition+LargeTurnY','TurnDiameter/2')
    for i in range(int(values['PublicFrontStallCount'])):
        xx=f'OuterWall+Partition+LargeWidth+Partition+{i}*(PublicFrontStallWidth+Partition)'
        front_room(f'FrontStallL_{i}',xx,'PublicFrontStallWidth','StallDepth','StallOpening')
    # Rear row faces the common wash/entry lobby; doors swing into each room.
    fy='PublicWCY+PublicWCDepth-Partition-StallDepth';front=f'({fy})-Partition'
    for i in range(int(values['StallCount'])):
        xx=f'OuterWall+Partition+{i}*(StallWidth+Partition)'
        hole=f'({xx})+(StallWidth-StallOpening)/2'
        wall(f'StallL_{i}_FL','PublicL',xx,front,'(StallWidth-StallOpening)/2',P)
        wall(f'StallL_{i}_FR','PublicL',f'({hole})+StallOpening',front,'(StallWidth-StallOpening)/2',P)
        wall(f'StallL_{i}_Side','PublicL',f'({xx})+StallWidth',front,P,'StallDepth+Partition')
        door(f'StallL_{i}_Door','PublicL',hole,fy,'StallOpening',0,90)
        rect(f'StallL_{i}_Toilet','fixture','PublicL',f'({xx})+(StallWidth-FixtureWidth)/2','PublicWCY+PublicWCDepth-Partition-FixtureDepth-StallToiletRearGap','FixtureWidth','FixtureDepth')
    for i in range(int(values['BasinCount'])):
        rect(f'PublicL_Basin_{i}','basin','PublicL','OuterWall+Partition',f'PublicWCY+PublicBasinY+{i}*PublicBasinPitch','BasinDepth','BasinWidth')
    left_features=features[before:]
    for item in left_features:
        right=dict(item);right['name']=item['name'].replace('L_','R_').replace('PubL','PubR').replace('LargeL','LargeR').replace('StallL','StallR').replace('PublicL','PublicR');right['owner']='PublicR'
        if item['kind']=='rect':right['x']=f'EnvelopeWidth-({item["x"]})-({item["w"]})'
        elif item['kind'] in ['circle','arc']:
            right['x']=f'EnvelopeWidth-({item["x"]})'
            if item['kind']=='arc':right['angle']=str((90-float(item['angle']))%360)
        else:
            right['x1']=f'EnvelopeWidth-({item["x1"]})';right['x2']=f'EnvelopeWidth-({item["x2"]})'
        features.append(right)
    rect('GuideLeft','guide','Guide','(OuterWall+PublicWCWidth+StaffX-GuideWidth)/2','StaffY+GuideYInset','GuideWidth','GuideDepth')
    rect('GuideRight','guide','Guide','(StaffX+StaffWidth+EnvelopeWidth-OuterWall-PublicWCWidth-GuideWidth)/2','StaffY+GuideYInset','GuideWidth','GuideDepth')
    for f in list(features):
        if f['kind']=='rect' and f['role'] in ['fixture','basin']:
            circle(f['name']+'_Symbol',f['owner'],f'({f["x"]})+({f["w"]})/2',
                   f'({f["y"]})+({f["d"]})/2',f'({f["w"]})*.32',f['role'])
    for i,letter in enumerate('ABCDEFGHIJ'):
        left=f'EnvelopeWidth/10*{i+.5}-({footprint})/2'
        for j in range(int(values['GateCount'])):
            x=f'({left})+GateBarrier' if j==0 else f'({left})+2*GateBarrier+GateWide+{j-1}*(GateStandard+GateBarrier)'
            width='GateWide' if j==0 else 'GateStandard'
            line(f'GateArm_{letter}_{j}','Auth'+letter,x,'GateY+GateLength/2',f'({x})+({width})','GateY+GateLength/2','gate')
    evaluated=[]
    for item in features:
        measured={k:number(v) for k,v in item.items() if k not in ['kind','name','role','owner']}
        if item['kind']=='rect':assert measured['w']>0 and measured['d']>0,item
        evaluated.append(dict(item,values=measured))
    return values,evaluated

def check_layout(values,features):
    W,D=values['EnvelopeWidth'],values['EnvelopeDepth']
    rectangles=[f for f in features if f['kind']=='rect']
    for f in rectangles:
        v=f['values'];assert v['x']>=-1e-8 and v['y']>=-1e-8,f['name']
        assert v['x']+v['w']<=W+1e-8 and v['y']+v['d']<=D+1e-8,f['name']
    staff_x=values['StaffX']
    gap=staff_x-values['OuterWall']-values['PublicWCWidth']
    right_gap=W-values['OuterWall']-values['PublicWCWidth']-staff_x-values['StaffWidth']
    front_hall=values['StaffY']-values['OuterWall']-values['AuthDepth']
    rear_hall=D-values['OuterWall']-values['StaffY']-values['StaffDepth']
    gate_footprint=values['GateWide']+(values['GateCount']-1)*values['GateStandard']+(values['GateCount']+1)*values['GateBarrier']
    min_bay=W/10-values['OuterWall']-values['Partition']/2
    assert gate_footprint<min_bay and gap>0 and right_gap>0 and front_hall>0 and rear_hall>0
    # Positive-area overlaps of solid obstacles must be absent (wall joints allowed).
    obstacles=[f for f in rectangles if f['role'] in ['wall','gate','fixture','basin','table','chair','guide']]
    conflicts=[]
    for i,a in enumerate(obstacles):
        av=a['values']
        for b in obstacles[i+1:]:
            if a['role']==b['role']=='wall':continue
            bv=b['values']
            dx=min(av['x']+av['w'],bv['x']+bv['w'])-max(av['x'],bv['x'])
            dy=min(av['y']+av['d'],bv['y']+bv['d'])-max(av['y'],bv['y'])
            if dx>1e-7 and dy>1e-7:conflicts.append((a['name'],b['name']))
    assert not conflicts,conflicts
    turning_conflicts=[]
    for f in features:
        if f['role']!='testcircle':continue
        c=f['values']
        for b in obstacles:
            v=b['values'];dx=c['x']-max(v['x'],min(c['x'],v['x']+v['w']));dy=c['y']-max(v['y'],min(c['y'],v['y']+v['d']))
            if dx*dx+dy*dy < c['r']*c['r']-1e-8:turning_conflicts.append((f['name'],b['name']))
    assert not turning_conflicts,turning_conflicts
    door_conflicts=[];door_approach_conflicts=[];door_approaches=[]
    for f in [f for f in features if f['kind']=='arc' and f['role']=='door']:
        a=f['values'];ang=math.radians(a['angle']);pts=[(a['x'],a['y'])]+[(a['x']+a['r']*math.cos(ang+j*math.pi/2),a['y']+a['r']*math.sin(ang+j*math.pi/2)) for j in [0,1]]
        xmin,xmax=min(p[0] for p in pts),max(p[0] for p in pts);ymin,ymax=min(p[1] for p in pts),max(p[1] for p in pts)
        leaf=next(q['values'] for q in features if q['name']==f['name'].replace('_Swing','_Leaf'))
        depth=values['DoorApproachDepth'];p=values['Partition'];angle=int(round(a['angle']))%360
        if abs(leaf['x1']-leaf['x2'])<1e-8:
            positive=angle in [0,90]
            ys=[a['y'],a['y']-p-depth] if positive else [a['y']-depth,a['y']+p]
            landings=[dict(x=xmin,y=y,w=a['r'],d=depth) for y in ys]
        else:
            positive=angle in [0,270]
            xs=[a['x'],a['x']-p-depth] if positive else [a['x']-depth,a['x']+p]
            landings=[dict(x=x,y=ymin,w=depth,d=a['r']) for x in xs]
        for index,z in enumerate(landings):
            door_approaches.append(dict(door=f['name'],side=index,**z))
            for b in obstacles:
                q=b['values'];dx=min(z['x']+z['w'],q['x']+q['w'])-max(z['x'],q['x']);dy=min(z['y']+z['d'],q['y']+q['d'])-max(z['y'],q['y'])
                if dx>1e-7 and dy>1e-7:door_approach_conflicts.append((f['name'],index,b['name']))
        for b in obstacles:
            z=b['values'];xl=max(xmin,z['x']);xr=min(xmax,z['x']+z['w']);yl=max(ymin,z['y']);yr=min(ymax,z['y']+z['d'])
            if xr-xl>1e-7 and yr-yl>1e-7:
                dx=a['x']-max(xl,min(a['x'],xr));dy=a['y']-max(yl,min(a['y'],yr))
                if dx*dx+dy*dy<a['r']*a['r']-1e-8:door_conflicts.append((f['name'],b['name']))
    assert not door_conflicts,door_conflicts
    assert not door_approach_conflicts,door_approach_conflicts
    stations=[f for f in rectangles if f['role']=='table'];assert len(stations)==10
    monitors=[f for f in rectangles if f['role']=='monitor'];assert len(monitors)==20
    for f in monitors:
        desk=next(s['values'] for s in stations if s['name']=='Workstation_'+f['name'].split('_')[1]);m=f['values']
        assert m['x']>=desk['x'] and m['x']+m['w']<=desk['x']+desk['w']+1e-8 and m['y']>=desk['y'] and m['y']+m['d']<=desk['y']+desk['d']+1e-8
    occupancy=values['TableDepth']+values['ChairGap']+values['ChairWidth']+values['ChairRetreat']
    side_aisle=(values['StaffWidth']-(5*values['TableWidth']+4*values['TableGap']))/2-values['Partition']
    row_aisle=values['TableRowPitch']-occupancy
    wc_approach=values['StaffDepth']-values['StaffWCDepth']-values['StaffTableYInset']-values['TableRowPitch']-occupancy
    front_lobby=values['StaffTableYInset']-values['Partition']
    assert min(side_aisle,row_aisle,wc_approach,front_lobby)>=values['StaffClearanceTest']-1e-8, '工位/椅后退让/厕所通路冲突：需最小修正'
    guide_bypass=min(gap,right_gap)/2-values['GuideWidth']/2
    assert guide_bypass>=values['StaffClearanceTest'] and values['GuideYInset']>=0 and values['GuideYInset']+values['GuideDepth']<=values['StaffDepth']
    # Check an actual reserved route through the right side and rear cross aisle.
    route_width=values['StaffClearanceTest'];half=route_width/2
    entry_x=staff_x+values['StaffWidth']/2
    entry_y=values['StaffY']+values['Partition']+half
    side_x=staff_x+values['StaffWidth']-values['Partition']-side_aisle/2
    rear_y=values['StaffY']+values['StaffDepth']-values['StaffWCDepth']-wc_approach+half
    route_rects=[dict(x=entry_x-half,y=entry_y-half,w=side_x-entry_x+route_width,d=route_width),
                 dict(x=side_x-half,y=entry_y-half,w=route_width,d=rear_y-entry_y+route_width),
                 dict(x=entry_x-half,y=rear_y-half,w=side_x-entry_x+route_width,d=route_width),
                 dict(x=entry_x-values['StaffWCOpening']/2,y=rear_y,w=values['StaffWCOpening'],d=values['StaffY']+values['StaffDepth']-values['StaffWCDepth']+values['Partition']-rear_y)]
    for a in route_rects:
        for f in obstacles:
            b=f['values'];dx=min(a['x']+a['w'],b['x']+b['w'])-max(a['x'],b['x']);dy=min(a['y']+a['d'],b['y']+b['d'])-max(a['y'],b['y'])
            assert dx<=1e-7 or dy<=1e-7,('reserved staff route',f['name'])
    # Retreat rectangles are reserved empty space; they must not touch solid obstacles.
    for f in [f for f in rectangles if f['role']=='clearance']:
        a=f['values']
        for b in obstacles:
            z=b['values'];dx=min(a['x']+a['w'],z['x']+z['w'])-max(a['x'],z['x']);dy=min(a['y']+a['d'],z['y']+z['d'])-max(a['y'],z['y'])
            assert dx<=1e-7 or dy<=1e-7,(f['name'],b['name'])
    staff_lobby=values['StaffWCDepth']-3*values['Partition']-values['StaffStallDepth']
    staff_wash_gap=values['StaffWCWidth']-2*values['Partition']-2*values['BasinDepth']
    assert staff_lobby>=1.2-1e-8 and staff_wash_gap>=1.2
    assert 2*values['StaffStallWidth']+3*values['Partition']<=values['StaffWCWidth']+1e-8
    assert len([f for f in rectangles if f['name'].startswith('StaffStall_') and f['role']=='fixture'])==2
    assert len([f for f in rectangles if f['name'].startswith('StaffBasin_')])==2
    public_lobby=values['PublicWCDepth']-2*values['Partition']-values['LargeDepth']-values['StallDepth']-2*values['Partition']
    assert public_lobby>=values['PublicOpening']
    return {'left_clear_gap_m':gap,'right_clear_gap_m':right_gap,'front_merge_depth_m':front_hall,'rear_clear_depth_m':rear_hall,
            'staff_wc_stalls':2,'staff_wc_basins':2,'staff_wc_stall_clear_size_m':[values['StaffStallWidth'],values['StaffStallDepth']],
            'staff_wc_shared_lobby_depth_m':staff_lobby,'staff_wc_between_basins_clear_m':staff_wash_gap,
            'staff_wc_turning_test_diameter_m':values['StaffTurnDiameter'],
            'public_wc_rows_per_node':2,'public_wc_ordinary_stalls_per_node':values['StallCount']+values['PublicFrontStallCount'],
            'public_wc_larger_stalls_per_node':1,'public_wc_shared_basins_per_node':values['BasinCount'],
            'public_wc_shared_cross_lobby_depth_m':public_lobby,'privacy_design':'fully enclosed independent rooms; all gender; shared wash area',
            'door_swing_obstacle_conflicts':door_conflicts,'stage_space_design':'FINAL_PASS checks passed; stage complete',
            'door_approach_depth_m':values['DoorApproachDepth'],'door_approach_obstacle_conflicts':door_approach_conflicts,
            'door_approach_reserved_rectangles_m':door_approaches,
            'workstations':10,'monitor_screens':20,'workstation_rows':[5,5],
            'staff_side_aisle_m':side_aisle,'staff_row_aisle_after_retreat_m':row_aisle,'staff_wc_approach_after_retreat_m':wc_approach,
            'staff_front_lobby_m':front_lobby,'chair_extra_retreat_m':values['ChairRetreat'],'map_minimum_bypass_width_m':guide_bypass,
            'continuous_staff_wc_route':'entry lobby -> right side aisle -> rear cross aisle -> WC door',
            'staff_route_reserved_rectangles_m':route_rects,'staff_wc_door_clear_m':values['StaffWCOpening'],
            'gate_footprint_m':gate_footprint,'minimum_bay_width_m':min_bay,
            'solid_obstacle_overlap_conflicts':conflicts,'turning_circle_obstacle_conflicts':turning_conflicts,'geometric_fit':'passed',
            'code_compliance_verified':False,'throughput_verified':False}
