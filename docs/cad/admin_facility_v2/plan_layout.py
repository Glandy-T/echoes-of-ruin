"""Architectural planning geometry in metres. P = user-authorized provisional.

All coordinates share X left-to-right and Y front-to-rear. Geometry expressions
also drive native FreeCAD Sketcher objects. Count changes require regeneration.
"""
import math

PARAMETERS = {
    'EnvelopeWidth': (65., '基准', '当前外包宽'),
    'EnvelopeDepth': (45., '基准', '当前外包进深'),
    'StaffWidth': (18., '用户确认', '工作人员区外边界宽'),
    'StaffDepth': (12., '用户确认', '工作人员区外边界深'),
    'OuterWall': (.30, 'PROVISIONAL', '外墙图示厚度，计入外包内'),
    'Partition': (.20, 'PROVISIONAL', '隔墙图示厚度，计入各区外边界内'),
    'AuthDepth': (8., 'PROVISIONAL', '认证区从前外墙内面起的进深'),
    'FrontOpening': (2.5, 'PROVISIONAL', '前入口组开口，沿用历史草图测试值'),
    'RearSideOpening': (6., 'PROVISIONAL', '左右后出口开口，历史草图测试值'),
    'RearCenterOpening': (8., 'PROVISIONAL', '中央后出口开口，历史草图测试值'),
    'RearOffset': (22., 'PROVISIONAL', '左右后出口中心距建筑中轴'),
    'StaffY': (21., 'PROVISIONAL', '工作人员区外边界前侧Y'),
    'StaffX': (23.5, 'PROVISIONAL', '工作人员区外边界左侧X，初始居中'),
    'StaffOpening': (1.2, 'PROVISIONAL', '工作人员区前侧门洞'),
    'StaffWCWidth': (3., 'PROVISIONAL', '内部厕所外边界宽'),
    'StaffWCDepth': (3., 'PROVISIONAL', '内部厕所外边界深'),
    'StaffWCOpening': (.9, 'PROVISIONAL', '内部厕所前侧门洞'),
    'PublicWCWidth': (8., 'PROVISIONAL', '每侧公共厕所外边界宽'),
    'PublicWCDepth': (10., 'PROVISIONAL', '每侧公共厕所外边界深'),
    'PublicWCY': (21., 'PROVISIONAL', '公共厕所外边界前侧Y'),
    'PublicOpening': (1.2, 'PROVISIONAL', '公共厕所朝大厅的门洞'),
    'PublicDoorOffset': (4.4, 'PROVISIONAL', '公共厕所门洞起点距前边界'),
    'UniversalWidth': (3., 'PROVISIONAL', '通用厕间图示净宽'),
    'UniversalDepth': (3., 'PROVISIONAL', '通用厕间图示净深'),
    'UniversalOpening': (1., 'PROVISIONAL', '通用厕间门洞'),
    'UniversalDoorOffset': (.6, 'PROVISIONAL', '通用厕间门洞起点距前内面'),
    'TurnDiameter': (1.5, 'PROVISIONAL', '空间测试圆直径，非合规认证'),
    'StallWidth': (1.6, 'PROVISIONAL', '普通厕间图示净宽'),
    'StallDepth': (2., 'PROVISIONAL', '普通厕间图示净深'),
    'StallOpening': (.8, 'PROVISIONAL', '普通厕间门洞'),
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
    'TableWidth': (1.8, 'PROVISIONAL', '异常处理工作台宽'),
    'TableDepth': (.8, 'PROVISIONAL', '异常处理工作台深'),
    'ChairWidth': (.55, 'PROVISIONAL', '工作台座位占位'),
    'GuideWidth': (2., 'PROVISIONAL', '墙边地图宽'),
    'GuideDepth': (.15, 'PROVISIONAL', '墙边地图占位深'),
    'StaffTableInset': (2.5, 'PROVISIONAL', '两工作台距工作人员区左右外边界'),
    'StaffTableYInset': (2.5, 'PROVISIONAL', '工作台前端距工作人员区前边界'),
    'ChairGap': (.45, 'PROVISIONAL', '座位与工作台图示间距'),
    'StaffToiletXOffset': (.35, 'PROVISIONAL', '内部坐便器距左内墙偏移'),
    'StaffToiletRearGap': (.20, 'PROVISIONAL', '内部坐便器距后内墙余量'),
    'BasinMargin': (.15, 'PROVISIONAL', '内部/通用洗面台距侧后内墙余量'),
    'UniversalTurnX': (1.8, 'PROVISIONAL', '通用厕间测试圆心距左内面'),
    'UniversalTurnY': (1.2, 'PROVISIONAL', '通用厕间测试圆心距前内面'),
    'UniversalToiletXOffset': (.45, 'PROVISIONAL', '通用坐便器距左内面偏移'),
    'UniversalToiletRearGap': (.45, 'PROVISIONAL', '通用坐便器距后内面余量'),
    'StallToiletRearGap': (.25, 'PROVISIONAL', '普通厕间坐便器后侧余量'),
    'PublicBasinY': (4.5, 'PROVISIONAL', '公共洗面台首个前端距节点前边界'),
    'PublicBasinPitch': (.95, 'PROVISIONAL', '公共洗面台纵向中心节距'),
    'GuideYGap': (2.5, 'PROVISIONAL', '地图前端距公共厕所后侧边界'),
}
COUNTS = {'GateCount': (2,'PROVISIONAL','每组认证通道数；修改数量须重建'),
          'StallCount': (4,'PROVISIONAL','每侧普通厕间数；另有一通用厕间'),
          'BasinCount': (3,'PROVISIONAL','每側公共洗面台数；修改数量须重建'),
          'TableCount': (2,'PROVISIONAL','工作人员区工作台占位数')}

def make_layout(overrides=None):
    values = {k:v[0] for k,v in PARAMETERS.items()}
    values.update({k:v[0] for k,v in COUNTS.items()})
    if overrides: values.update(overrides)
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
    WX=f'({SX})+(StaffWidth-StaffWCWidth)/2';WY='StaffY+(StaffDepth-StaffWCDepth)/2'
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
    # Staff boundary is 18x12; wall is within that confirmed planning boundary.
    def enclosed(name,owner,x,y,w,d,opening):
        a=f'({x})+(({w})-({opening}))/2';b=f'({a})+({opening})'
        wall(name+'_FrontL',owner,x,y,f'({a})-({x})',P)
        wall(name+'_FrontR',owner,b,y,f'({x})+({w})-({b})',P)
        wall(name+'_Back',owner,x,f'({y})+({d})-Partition',w,P)
        wall(name+'_Left',owner,x,f'({y})+Partition',P,f'({d})-2*Partition')
        wall(name+'_Right',owner,f'({x})+({w})-Partition',f'({y})+Partition',P,f'({d})-2*Partition')
        door(name+'_Door',owner,a,f'({y})+Partition',opening,0,90)
    enclosed('Staff','Staff',SX,SY,'StaffWidth','StaffDepth','StaffOpening')
    enclosed('StaffWC','Staff',WX,WY,'StaffWCWidth','StaffWCDepth','StaffWCOpening')
    rect('StaffToilet','fixture','Staff',f'({WX})+Partition+StaffToiletXOffset',f'({WY})+StaffWCDepth-Partition-FixtureDepth-StaffToiletRearGap','FixtureWidth','FixtureDepth')
    rect('StaffBasin','basin','Staff',f'({WX})+StaffWCWidth-Partition-BasinWidth-BasinMargin',f'({WY})+StaffWCDepth-Partition-BasinDepth-BasinMargin','BasinWidth','BasinDepth')
    for i in range(int(values['TableCount'])):
        tx=f'({SX})+StaffTableInset' if i==0 else f'({SX})+StaffWidth-StaffTableInset-TableWidth'
        rect(f'StaffTable_{i}','table','Staff',tx,'StaffY+StaffTableYInset','TableWidth','TableDepth')
        rect(f'StaffChair_{i}','chair','Staff',f'({tx})+(TableWidth-ChairWidth)/2','StaffY+StaffTableYInset+TableDepth+ChairGap','ChairWidth','ChairWidth')
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
    wall('UniversalL_Back','PublicL',ux,'PublicWCY+Partition+UniversalDepth','UniversalWidth+Partition',P)
    uxr='OuterWall+Partition+UniversalWidth'
    wall('UniversalL_Right1','PublicL',uxr,uy,P,'UniversalDoorOffset')
    wall('UniversalL_Right2','PublicL',uxr,'PublicWCY+Partition+UniversalDoorOffset+UniversalOpening',P,'UniversalDepth-UniversalDoorOffset-UniversalOpening')
    door('UniversalL_Door','PublicL',uxr,'PublicWCY+Partition+UniversalDoorOffset','UniversalOpening',0,0)
    circle('UniversalL_Turn','PublicL','OuterWall+Partition+UniversalTurnX','PublicWCY+Partition+UniversalTurnY','TurnDiameter/2')
    rect('UniversalL_Toilet','fixture','PublicL','OuterWall+Partition+UniversalToiletXOffset','PublicWCY+Partition+UniversalDepth-FixtureDepth-UniversalToiletRearGap','FixtureWidth','FixtureDepth')
    rect('UniversalL_Basin','basin','PublicL','OuterWall+Partition+UniversalWidth-BasinWidth-BasinMargin','PublicWCY+Partition+UniversalDepth-BasinDepth-BasinMargin','BasinWidth','BasinDepth')
    fy='PublicWCY+PublicWCDepth-Partition-StallDepth';front=f'({fy})-Partition'
    for i in range(int(values['StallCount'])):
        xx=f'OuterWall+Partition+{i}*(StallWidth+Partition)'
        hole=f'({xx})+(StallWidth-StallOpening)/2'
        wall(f'StallL_{i}_FL','PublicL',xx,front,'(StallWidth-StallOpening)/2',P)
        wall(f'StallL_{i}_FR','PublicL',f'({hole})+StallOpening',front,'(StallWidth-StallOpening)/2',P)
        wall(f'StallL_{i}_Side','PublicL',f'({xx})+StallWidth',front,P,'StallDepth+Partition')
        door(f'StallL_{i}_Door','PublicL',hole,fy,'StallOpening',0,90)
        rect(f'StallL_{i}_Toilet','fixture','PublicL',f'({xx})+(StallWidth-FixtureWidth)/2','PublicWCY+PublicWCDepth-Partition-FixtureDepth-StallToiletRearGap','FixtureWidth','FixtureDepth')
    for i in range(int(values['BasinCount'])):rect(f'PublicL_Basin_{i}','basin','PublicL','OuterWall+Partition',f'PublicWCY+PublicBasinY+{i}*PublicBasinPitch','BasinDepth','BasinWidth')
    left_features=features[before:]
    for item in left_features:
        right=dict(item);right['name']=item['name'].replace('L_','R_').replace('PubL','PubR').replace('UniversalL','UniversalR').replace('StallL','StallR').replace('PublicL','PublicR');right['owner']='PublicR'
        if item['kind']=='rect':right['x']=f'EnvelopeWidth-({item["x"]})-({item["w"]})'
        elif item['kind'] in ['circle','arc']:
            right['x']=f'EnvelopeWidth-({item["x"]})'
            if item['kind']=='arc':right['angle']=str((90-float(item['angle']))%360)
        else:
            right['x1']=f'EnvelopeWidth-({item["x1"]})';right['x2']=f'EnvelopeWidth-({item["x2"]})'
        features.append(right)
    rect('GuideLeft','guide','Guide','OuterWall','PublicWCY+PublicWCDepth+GuideYGap','GuideDepth','GuideWidth')
    rect('GuideRight','guide','Guide','EnvelopeWidth-OuterWall-GuideDepth','PublicWCY+PublicWCDepth+GuideYGap','GuideDepth','GuideWidth')
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
    obstacles=[f for f in rectangles if f['role'] in ['wall','gate','fixture','basin','table','chair']]
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
    return {'left_clear_gap_m':gap,'right_clear_gap_m':right_gap,'front_merge_depth_m':front_hall,'rear_clear_depth_m':rear_hall,
            'gate_footprint_m':gate_footprint,'minimum_bay_width_m':min_bay,
            'solid_obstacle_overlap_conflicts':conflicts,'turning_circle_obstacle_conflicts':turning_conflicts,'geometric_fit':'passed',
            'code_compliance_verified':False,'throughput_verified':False}
