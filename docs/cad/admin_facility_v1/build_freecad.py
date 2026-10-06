"""Run with the installed FreeCAD bin/python.exe; no third-party CAD packages.
Known sizes are parametric Sketcher geometry. Unspecified construction values
are strings 'TBD', never zero/default construction dimensions.
"""
from pathlib import Path
import json
import math
import os
import sys
import xml.etree.ElementTree as ET
import FreeCAD as App
import Part
import Sketcher
import TechDraw

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'exports'
OUT.mkdir(exist_ok=True)
SPEC_URL = 'https://github.com/Glandy-T/echoes-of-ruin/blob/8bc29124bacb78d9d1fe84df7165d89765180e6c/docs/CRYO_FACILITY_LAYOUT.md'
PARAMS = {
    'Floor1Width': (65, '1F 外包宽', '4.1', '约值/当前基准'),
    'Floor1Depth': (45, '1F 外包进深', '4.1', '约值/当前基准'),
    'Floor2Width': (40, '2F 外包宽', '4.1', '约值/当前基准'),
    'Floor2Depth': (30, '2F 外包进深', '4.1', '约值/当前基准'),
    'LiftWidth': (3, '升降台宽', '5.4/6.4', '约值/当前占位'),
    'LiftDepth': (3, '升降台进深', '5.4/6.4', '约值/当前占位'),
    'DeskWidth': (1.8, '工位桌面宽', '6.2', '约值/当前基准'),
    'DeskDepth': (0.8, '工位桌面进深', '6.2', '约值/当前基准'),
    'ModuleWidth': (2.5, '工位操作模块宽', '6.2', '约值/当前基准'),
    'ModuleDepth': (2.2, '工位操作模块进深', '6.2', '约值/当前基准'),
    'WCWidth': (3, '工作人员卫生间宽', '6.4', '约值/当前占位'),
    'WCDepth': (4, '工作人员卫生间进深', '6.4', '约值/当前占位'),
    'CabinetWidth': (2, '设备柜区宽', '6.4', '约值/当前占位'),
    'CabinetDepth': (4, '设备柜区进深', '6.4', '约值/当前占位'),
    'FrontDoorWidth': (2.5, '正面入口标注宽', '用户内部草图', '草图明确标注；净/洞口定义TBD'),
    'RearDoorLeftWidth': (6, '后侧左出口标注宽', '用户内部草图', '草图明确标注；净/洞口定义TBD'),
    'RearDoorCenterWidth': (8, '后侧中出口标注宽', '用户内部草图', '草图明确标注；净/洞口定义TBD'),
    'RearDoorRightWidth': (6, '后侧右出口标注宽', '用户内部草图', '草图明确标注；净/洞口定义TBD'),
    'StaffDepth': (12, '工作人员区进深', '用户内部草图', '草图明确标注；外包/净尺寸定义TBD'),
    'StaffWidth': (18, '工作人员区横向宽', '用户明确确认2026-10-06', '18×12m已确认；外包/净尺寸定义TBD'),
    'SameRowGapMin': (1.2, '同排模块净距下限', '6.2', '范围下限/非选定值'),
    'SameRowGapMax': (1.5, '同排模块净距上限', '6.2', '范围上限/非选定值'),
    'RowGapMin': (2, '前后模块通道下限', '6.2', '范围下限/非选定值'),
    'RowGapMax': (2.4, '前后模块通道上限', '6.2', '范围上限/非选定值'),
    'LoopGapMin': (1.5, '外圈巡查通道下限', '6.2', '范围下限/非选定值'),
    'LoopGapMax': (2, '外圈巡查通道上限', '6.2', '范围上限/非选定值'),
    'ScreenWidthMin': (6, '主屏宽下限', '6.4', '范围下限/非选定值'),
    'ScreenWidthMax': (8, '主屏宽上限', '6.4', '范围上限/非选定值'),
    'ScreenHeightMin': (1.8, '主屏高下限', '6.4', '范围下限/非选定值'),
    'ScreenHeightMax': (2.2, '主屏高上限', '6.4', '范围上限/非选定值'),
}
TBD = [
    ('T01', '墙与结构', '墙厚、墙体类型、内外表面定义；柱网、柱截面、结构与防火分隔。'),
    ('T02', '1F 十入口', 'A-J顺序和宽2.5m见草图；各门中心X、宽度控制面、洞高、门型/开启方式未定。'),
    ('T03', '自动认证', '认证区进深、闸机尺寸/数量、通道宽和异常分流位置。'),
    ('T04', '1F 三后出口', '草图宽6/8/6m；三门中心X、宽度控制面、洞高、门型；不绑定楼栋。'),
    ('T05', '工作人员岛', '18×12m由用户确认；精确XY、边界控制面、区域围护/出入口TBD。'),
    ('T06', '升降台', '后侧中央区域内的精确 XY、井道/外围护、上下口方向和平台净尺寸定义。'),
    ('T07', '疏散楼梯', '草图在岛两端，文档要求建筑边侧封闭楼梯；按文档。位置/数量/全部构造TBD。'),
    ('T08', '上下层对位', '2F 相对 1F 的 X/Y 偏移、准确楼面标高、楼板厚度；草图没有定位尺寸。'),
    ('T09', '2F 工位定位', '阵列在 2F 的坐标与朝向；范围内实际通道值；桌面、椅子与模块内部位置。'),
    ('T10', '双屏与主屏', '各显示器物理尺寸/支架；主屏实际宽高、墙位、厚度、安装标高。'),
    ('T11', '2F 配套', '卫生间具体边角、门洞/围护/洁具；柜列墙位、柜数、朝向及操作净距。'),
    ('T12', '导视与公共卫生间', '导视具体位置/占地；1F 公共/无障碍卫生间是否设置及尺寸。'),
]

doc = App.newDocument('AdminFacility_v1')
doc.Label = '管理设施 v1 | 已知尺寸 + TBD | 空间验证'
params = doc.addObject('App::FeaturePython', 'Parameters')
params.Label = '01 已知参数（FreeCAD 内部 mm；图纸 m）'
for key, (value, label, section, status) in PARAMS.items():
    params.addProperty('App::PropertyLength', key, 'Known sizes', f'{label}; §{section}; {status}')
    setattr(params, key, value * 1000)
params.addProperty('App::PropertyString', 'SourceURL', 'Evidence')
params.SourceURL = SPEC_URL
params.addProperty('App::PropertyString', 'SourceBlobSHA', 'Evidence')
params.SourceBlobSHA = '9a6c228210b9fef6b1471312afeda0987ebaf8ab'
params.addProperty('App::PropertyString', 'CoordinateRule', 'Evidence')
params.CoordinateRule = 'X=左→右；Y=正面→后侧；O1=1F左前外包角。O2全局偏移=TBD；部件/阵列为独立局部坐标，禁止视为落位。'
params.addProperty('App::PropertyString', 'FloorElevation', 'TBD')
params.FloorElevation = 'TBD；1F层高范围5.5-6m，2F约4m，不能当作精确楼面标高'

sheet = doc.addObject('Spreadsheet::Sheet', 'ParameterSchedule')
sheet.Label = '02 参数表与证据（编辑 Parameters 驱动草图）'
for col, text in zip('ABCDE', ['参数名', '值 / m', '用途', '权威章节', '状态']):
    sheet.set(col+'1', text)
for row, (key, (val, label, section, status)) in enumerate(PARAMS.items(), 2):
    for col, text in zip('ABCDE', [key, str(val), label, '§'+section, status]):
        sheet.set(col+str(row), text)
sheet.setColumnWidth('A', 165)
sheet.setColumnWidth('B', 70)
sheet.setColumnWidth('C', 190)
sheet.setColumnWidth('D', 90)
sheet.setColumnWidth('E', 200)

pending = doc.addObject('App::DocumentObjectGroup', 'Unresolved')
pending.Label = '03 TBD（无数字默认值；不是施工构件）'
for tid, title, desc in TBD:
    obj = doc.addObject('App::FeaturePython', tid)
    obj.Label = f'{tid} {title}: TBD'
    obj.addProperty('App::PropertyString', 'Status', 'Pending')
    obj.Status = 'TBD'
    obj.addProperty('App::PropertyString', 'Question', 'Pending')
    obj.Question = desc
    pending.addObject(obj)

def group(name, label):
    g = doc.addObject('App::DocumentObjectGroup', name)
    g.Label = label
    return g

def rect(name, label, width_key, depth_key, parent):
    w, h = getattr(params, width_key).Value, getattr(params, depth_key).Value
    obj = doc.addObject('Sketcher::SketchObject', name)
    obj.Label = label
    pts = [(0,0), (w,0), (w,h), (0,h)]
    for i in range(4):
        p, q = pts[i], pts[(i+1)%4]
        obj.addGeometry(Part.LineSegment(App.Vector(p[0],p[1],0), App.Vector(q[0],q[1],0)), False)
    for i in range(4):
        obj.addConstraint(Sketcher.Constraint('Coincident', i, 2, (i+1)%4, 1))
        obj.addConstraint(Sketcher.Constraint('Horizontal' if i%2 == 0 else 'Vertical', i))
    obj.addConstraint(Sketcher.Constraint('Coincident',0,1,-1,1))
    c = obj.addConstraint(Sketcher.Constraint('Distance', 0, w))
    obj.renameConstraint(c, 'Width')
    obj.setExpression('Constraints.Width', f'Parameters.{width_key}')
    c = obj.addConstraint(Sketcher.Constraint('Distance', 1, h))
    obj.renameConstraint(c, 'Depth')
    obj.setExpression('Constraints.Depth', f'Parameters.{depth_key}')
    obj.addProperty('App::PropertyString', 'LocationStatus', 'Evidence')
    obj.LocationStatus = '独立局部原点；建筑内位置 TBD' if name != 'Envelope1F' else 'O1=1F左前外包角'
    obj.addProperty('App::PropertyString', 'GeometryMeaning', 'Evidence')
    obj.GeometryMeaning = '外包/占位线，无墙厚、门洞、结构构造；约值基准'
    parent.addObject(obj)
    obj.Visibility = False
    return obj

f1 = group('Floor1', '04 1F | 外包 65×45m | 内部落位 TBD')
f2 = group('Floor2', '05 2F | 独立局部坐标 | 上下层偏移 TBD')
details = group('Components', '06 已知尺寸部件（局部坐标；未落位）')
env1 = rect('Envelope1F', '1F外包线 | 非实体墙', 'Floor1Width','Floor1Depth', f1)
env2 = rect('Envelope2F', '2F外包线 | 非实体墙 | O2偏移TBD', 'Floor2Width','Floor2Depth',f2)
env1.Visibility = True
lift = rect('LiftMaster', 'L01 升降台 3×3m | 共用部件母版', 'LiftWidth','LiftDepth',details)
desk = rect('DeskMaster', 'D01 桌面 1.8×0.8m | 内部朝向TBD', 'DeskWidth','DeskDepth',details)
module = rect('ModuleMaster', 'W01 工位模块 2.5×2.2m', 'ModuleWidth','ModuleDepth',details)
wc = rect('WCMaster', 'WC01 工作人员卫生间 3×4m | 净/外包定义TBD','WCWidth','WCDepth',details)
cab = rect('CabinetMaster', 'EQ01 设备柜区 2×4m | 开放柜列区域','CabinetWidth','CabinetDepth',details)
staff = rect('StaffMaster', 'ST01 工作人员区 18×12m | 用户已确认 | XY=TBD','StaffWidth','StaffDepth',details)
def width_line(name,label,key):
    width=getattr(params,key).Value
    s=doc.addObject('Sketcher::SketchObject',name)
    s.Label=label
    s.addGeometry(Part.LineSegment(App.Vector(0,0,0),App.Vector(width,0,0)),False)
    s.addConstraint(Sketcher.Constraint('Coincident',0,1,-1,1))
    s.addConstraint(Sketcher.Constraint('Horizontal',0))
    c=s.addConstraint(Sketcher.Constraint('Distance',0,width))
    s.renameConstraint(c,'Width')
    s.setExpression('Constraints.Width',f'Parameters.{key}')
    s.addProperty('App::PropertyString','LocationStatus','Evidence')
    s.LocationStatus='独立局部宽度线；不表示门位/洞高/门构造'
    details.addObject(s)
    s.Visibility=False
    return s
front=width_line('FrontDoorMaster','IN A-J 正面入口宽2.5m | 未落位','FrontDoorWidth')
rear_l=width_line('RearLeftMaster','EX-L 后出口宽6m | 未落位','RearDoorLeftWidth')
rear_c=width_line('RearCenterMaster','EX-C 后出口宽8m | 未落位','RearDoorCenterWidth')
rear_r=width_line('RearRightMaster','EX-R 后出口宽6m | 未落位','RearDoorRightWidth')
openings=group('OpeningSchedule','1F 洞口清单 | 10前入口 + 3后出口 | 坐标TBD')
for code,master in [(f'IN_{c}',front) for c in 'ABCDEFGHIJ']+[('EX_L',rear_l),('EX_C',rear_c),('EX_R',rear_r)]:
    link=doc.addObject('App::Link',code)
    link.setLink(master)
    link.Label=code+' | 宽度有依据；位置/门构造TBD'
    link.addProperty('App::PropertyString','LocationStatus','Pending')
    link.LocationStatus='TBD；默认矩阵不是建筑(0,0)门位'
    openings.addObject(link)
    link.Visibility=False
for parent, name in [(f1,'Lift1F'),(f2,'Lift2F')]:
    link = doc.addObject('App::Link', name)
    link.setLink(lift)
    link.Label = 'L01 同一升降台 | XY= TBD（不是坐标0）'
    link.addProperty('App::PropertyString','PlacementStatus','Evidence')
    link.PlacementStatus = 'TBD；未注册到建筑坐标。默认链接矩阵不表示落位。'
    parent.addObject(link)
    link.Visibility = False

stations = group('Workstations', '07 A-J十工位清单（双屏；建筑坐标TBD）')
for letter in 'ABCDEFGHIJ':
    item = doc.addObject('App::FeaturePython', 'WS_'+letter)
    item.Label = f'WS-{letter} | 双屏工位 | 位置TBD'
    item.addProperty('App::PropertyInteger','DisplayCount','Confirmed')
    item.DisplayCount = 2
    item.addProperty('App::PropertyLink','DeskTemplate','Confirmed')
    item.DeskTemplate = desk
    item.addProperty('App::PropertyLink','ModuleTemplate','Confirmed')
    item.ModuleTemplate = module
    item.addProperty('App::PropertyString','PlacementStatus','Pending')
    item.PlacementStatus = 'TBD；参照独立阵列范围验证，未落位到2F'
    stations.addObject(item)

CASES = {}
for suffix, title in [('Min','范围下限'),('Max','范围上限')]:
    case = group('Array'+suffix, f'08 {title}阵列验证 | 不是最终布置 | 独立局部坐标')
    mw, md = params.ModuleWidth.Value, params.ModuleDepth.Value
    gx = getattr(params,'SameRowGap'+suffix).Value
    gy = getattr(params,'RowGap'+suffix).Value
    loop = getattr(params,'LoopGap'+suffix).Value
    arr_w = 3*mw + 2*gx + 2*loop
    arr_d = 4*md + 3*gy + 2*loop
    # Front -> rear is I/J, F/G/H, C/D/E, A/B. Campus left/right unchanged.
    rows = ['IJ','FGH','CDE','AB']
    links = []
    coords = []
    for r, letters in enumerate(rows):
        offset = (arr_w - (len(letters)*mw + (len(letters)-1)*gx))/2
        for c, letter in enumerate(letters):
            x, y = offset+c*(mw+gx), loop+r*(md+gy)
            link = doc.addObject('App::Link', f'Array{suffix}_{letter}')
            link.setLink(module)
            link.Label = f'{letter} 模块 | {title}检查坐标；非建筑落位'
            # Explicit expressions preserve edits to module and range bounds.
            n = len(letters)
            wx = f'(3*Parameters.ModuleWidth+2*Parameters.SameRowGap{suffix}+2*Parameters.LoopGap{suffix})'
            link.setExpression('Placement.Base.x', f'({wx}-({n}*Parameters.ModuleWidth+{n-1}*Parameters.SameRowGap{suffix}))/2+{c}*(Parameters.ModuleWidth+Parameters.SameRowGap{suffix})')
            link.setExpression('Placement.Base.y', f'Parameters.LoopGap{suffix}+{r}*(Parameters.ModuleDepth+Parameters.RowGap{suffix})')
            case.addObject(link)
            link.Visibility = False
            links.append(link)
            coords.append({'id':letter,'x_m':x/1000,'y_m':y/1000,'width_m':mw/1000,'depth_m':md/1000})
    CASES[suffix] = {'width_m':arr_w/1000,'depth_m':arr_d/1000,'row_gap_m':gy/1000,'same_row_gap_m':gx/1000,'loop_gap_m':loop/1000,'modules':coords,'objects':links}

doc.recompute()

# Paper primitives use mm on A2, top-left origin. Real geometry carries explicit
# drawing scales. Relationship tokens are paper-space symbols, explicitly NTS.
PAGES = []
def newpage(code, title, scale):
    p = {'code':code,'title':title,'scale':scale,'width_mm':594,'height_mm':420,'items':[]}
    PAGES.append(p)
    for x,y,w,h in [(12,12,570,396)]: p['items'].append({'k':'rect','x':x,'y':y,'w':w,'h':h,'lw':0.45})
    text(p,22,26,'ECHOES OF RUIN / 管理设施空间验证',5)
    text(p,22,36,title,5)
    text(p,22,46,'尺寸单位 m；约值为当前验证基准。实线为有依据的尺寸线；虚线/关系符号不构成定位。',3)
    line(p,12,374,582,374,0.4)
    for x in [360,475,533]: line(p,x,374,x,408,0.35)
    text(p,20,383,'依据：CRYO_FACILITY_LAYOUT.md §§4-6 + 本轮用户两张草图',3)
    text(p,20,391,'GitHub main 核对：2026-10-06 / commit 8bc29124bacb / 修订 v1',3)
    text(p,20,400,'状态：空间验证首版；未知工程条件统一 TBD；导出为参数快照。',3)
    text(p,368,384,'比例 / 打印 A2 100%',3)
    text(p,368,395,scale,3.2)
    text(p,483,384,'图号',3)
    text(p,483,398,code,5)
    text(p,541,384,'版本',3)
    text(p,541,398,'v1',5)
    return p
def text(p,x,y,s,size=3.2,anchor='start',color='#111111'):
    p['items'].append({'k':'text','x':x,'y':y,'s':s,'size':size,'anchor':anchor,'color':color})
def line(p,x1,y1,x2,y2,lw=0.25,dash=False):
    p['items'].append({'k':'line','x1':x1,'y1':y1,'x2':x2,'y2':y2,'lw':lw,'dash':dash})
def box(p,x,y,w,h,lw=.5,dash=False):
    p['items'].append({'k':'rect','x':x,'y':y,'w':w,'h':h,'lw':lw,'dash':dash})
def arrow(p,x1,y1,x2,y2):
    line(p,x1,y1,x2,y2,.35)
    theta=math.atan2(y2-y1,x2-x1)
    for sign in [-1,1]:
        a=theta+math.pi+sign*.4
        line(p,x2,y2,x2+2.3*math.cos(a),y2+2.3*math.sin(a),.35)
def dimh(p,x1,x2,y,target_y,label):
    for x in [x1,x2]: line(p,x,target_y,x,y-2,.18)
    line(p,x1,y,x2,y,.2)
    for x in [x1,x2]: line(p,x-1.1,y+1.1,x+1.1,y-1.1,.3)
    text(p,(x1+x2)/2,y-2,label,3.2,'middle')
def dimv(p,y1,y2,x,target_x,label):
    for y in [y1,y2]:line(p,target_x,y,x+2,y,.18)
    line(p,x,y1,x,y2,.2)
    for y in [y1,y2]:line(p,x-1.1,y+1.1,x+1.1,y-1.1,.3)
    text(p,x-3,(y1+y2)/2,label,3.2,'end')
def notes(p,x,y,lines,size=3.2,gap=6):
    for i,s in enumerate(lines):text(p,x,y+i*gap,s,size)
def datum(p,x,y,origin):
    arrow(p,x,y,x+18,y); arrow(p,x,y,x,y-18)
    text(p,x+20,y+1,'+X',3);text(p,x-3,y-20,'+Y 后侧',3)
    text(p,x+2,y+6,origin,3)
def drawrect(p,x,y,w,h,scale,label,dimension=True):
    box(p,x,y,w*1000/scale,h*1000/scale)
    if dimension:
        dimh(p,x,x+w*1000/scale,y-8,y,f'≈ {w:g} m')
        dimv(p,y,y+h*1000/scale,x-8,x,f'≈ {h:g} m')
    text(p,x+w*1000/scale/2,y+h*1000/scale+9,label,3.2,'middle')

p=newpage('A101','管理设施 1F / 外包平面与功能关系','主图 1:200；关系图 NTS')
drawrect(p,58,102,65,45,200,'正面 / A-J 十入口；宽 2.5m，门位及宽度控制面 TBD')
text(p,220.5,85,'后侧 / 园区 / 三出口宽 6 / 8 / 6 m；定位 TBD',3.2,'middle')
# All interior markers here are paper-space relation symbols, never dimensioned
# building coordinates. Only the envelope and independent component details are
# scaled engineering geometry. This preserves the supplied sketch topology.
for x,lab in [(107,'EX-L / 6m'),(221,'EX-C / 8m'),(330,'EX-R / 6m')]:
    box(p,x-6,100.5,12,3,.3,True)
    text(p,x,115,lab,3,'middle')
    arrow(p,x,125,x,117)
for x in [111,328]:
    line(p,x-19,135,x+19,135,.65,True)
    text(p,x,144,'地图 / NTS',3,'middle')
box(p,170,161,102,60,.3,True)
text(p,221,186,'工作人员 / 异常处理区',3.5,'middle')
text(p,221,196,'18×12m 已确认；精确XY=TBD',3,'middle')
text(p,221,208,'关系符号 NTS；无墙/构造假定',2.9,'middle')
box(p,209,159,24,13,.3,True)
text(p,221,168,'L01 3×3 / NTS',2.7,'middle')
text(p,81,176,'疏散楼梯',3,'middle')
text(p,81,183,'边侧/TBD',2.9,'middle')
text(p,355,176,'疏散楼梯',3,'middle')
text(p,355,183,'数量/TBD',2.9,'middle')
text(p,220.5,241,'共享汇流大厅 / 主通道边界 TBD',3.5,'middle')
line(p,65,264,375,264,.3,True)
text(p,220.5,273,'自动芯片认证区 / 进深、闸机与净通道 TBD（NTS）',3,'middle')
for i,letter in enumerate('ABCDEFGHIJ'):
    x=77+i*31.8
    box(p,x-4,304,8,4,.3,True)
    text(p,x,300,letter,3.7,'middle')
    arrow(p,x,296,x,282)
text(p,220.5,319,'十入口宽均按草图 2.5 m；符号 X 仅示顺序，不是门位坐标。',2.8,'middle')
datum(p,58,327,'O1 (0,0) m')
text(p,403,70,'运营流线 / 不按比例，不用于量取位置',3.5)
box(p,405,84,160,35,.3,True)
text(p,485,94,'正面入口（顺序见立面草图）',3.2,'middle')
text(p,485,104,'A  B  C  D  E  F  G  H  I  J',4,'middle')
text(p,485,114,'10 入口；每入口后自动芯片认证',3,'middle')
arrow(p,485,119,485,132)
box(p,405,132,160,24,.3,True)
text(p,485,142,'共享汇流大厅',3.5,'middle')
text(p,485,152,'认证后不保持十条隔离流线',3,'middle')
arrow(p,485,156,485,174)
box(p,405,174,160,23,.3,True)
text(p,485,184,'后侧三出口：左 / 中 / 右',3.5,'middle')
text(p,485,194,'不固定对应某栋休眠楼',3,'middle')
notes(p,403,218,['例外支路：认证异常 → 工作人员岛', '日常上下：后侧升降台 → 2F', '紧急疏散：边侧封闭楼梯', 'T02-T07：位置、边界及工程构造 TBD'],3.2,7)
notes(p,403,271,['1F 外包基准面积：2,925 m²', '内部符号 NTS；不可量取门位/区域位置。', '楼梯按文档边侧要求；与草图冲突见 T07。', '1F 公共/无障碍卫生间：是否设置 TBD。'],3.2,7)
text(p,403,320,'主要尺寸部件见 A103；待确认清单见 A104。',3)

p=newpage('A102','管理设施 2F / 开放监控层与翻转阵列','外包 1:200；阵列 1:100')
drawrect(p,58,106,40,30,200,'正面 / 相对园区阵列已翻转前后')
text(p,158,85,'后侧 / 从升降台进入监控层',3.5,'middle')
text(p,158,119,'开放监控层 / 内部为 NTS 关系符号',3.2,'middle')
text(p,158,129,'后侧 L01；阵列由此进入，左右不变',3,'middle')
for y,letters in [(141,'AB'),(164,'CDE'),(187,'FGH'),(210,'IJ')]:
    xs=[134,182] if len(letters)==2 else [110,158,206]
    for x,letter in zip(xs,letters):
        box(p,x-10,y-5,20,13,.25,True)
        text(p,x,y+1,letter+' 双屏',3,'middle')
text(p,158,231,'主屏：正面相对关系；实际墙位TBD',3,'middle')
text(p,158,242,'阵列 XY、所有符号坐标、配套/楼梯位置 TBD',3,'middle')
datum(p,58,256,'O2 局部 (0,0)；全局偏移 Tx/Ty=TBD')
notes(p,44,295,['统一轴向：+X 左→右；+Y 正面→后侧。', '2F 全局坐标：X=X2+Tx；Y=Y2+Ty；Tx/Ty=TBD。', '本版未做上下层实体对位：不以任意层高或居中偏移替代。', 'WC01 边角；EQ01 靠墙开放柜列；边侧楼梯与1F对应。', '主屏、卫生间、设备柜的已知尺寸详见 A103。'],3.2,7)
text(p,389,72,'2-3-3-2 / 工位模块范围验证',4,'middle')
text(p,389,81,'独立局部原点；本图不表示阵列在 2F 的位置',3,'middle')
c=CASES['Min']; ax,ay=329,108; fac=10
box(p,ax,ay,c['width_m']*fac,c['depth_m']*fac,.25,True)
dimh(p,ax,ax+c['width_m']*fac,ay-8,ay,f"下限包络 {c['width_m']:g} m")
dimv(p,ay,ay+c['depth_m']*fac,ax-8,ax,f"{c['depth_m']:g} m")
for mod in c['modules']:
    x=ax+mod['x_m']*fac; y=ay+(c['depth_m']-mod['y_m']-mod['depth_m'])*fac
    box(p,x,y,mod['width_m']*fac,mod['depth_m']*fac,.4)
    text(p,x+12.5,y+8,mod['id'],4,'middle')
    text(p,x+12.5,y+14,'双屏',2.7,'middle')
    # NTS monitor tokens: no fictional screen footprint/depth.
    text(p,x+12.5,y+19,'1 / 2',2.7,'middle')
text(p,ax+c['width_m']*fac/2,ay-20,'后侧升降台 → A/B → C/D/E → F/G/H → I/J',3,'middle')
notes(p,477,112,['阵列方向：', '后侧 → 正面', 'A / B', 'C / D / E', 'F / G / H', 'I / J', '', '左右关系保持。'],3.2,7)
notes(p,309,312,['此处仅检验文档通道范围的下限组合，不选定最终通道。', '同排净距 1.2-1.5 m；前后通道 2.0-2.4 m；外圈 1.5-2.0 m。', '全取下限：12.9×17.8 m；全取上限：14.5×20.0 m。', '含外圈通道，两种边界均小于 40×30 m 外包；', '墙厚、配套、疏散及阵列最终落位未定，不能据此证明完整净空。'],3.1,6)

p=newpage('A103','尺寸部件 / 独立局部坐标 / 非建筑落位','部件 1:50；门宽线 1:100')
drawrect(p,55,102,3,3,50,'L01 升降台 / 1F与2F共用同一母版')
drawrect(p,192,102,3,4,50,'WC01 工作人员卫生间')
drawrect(p,324,102,2,4,50,'EQ01 靠墙设备柜区（开放区域）')
notes(p,438,96,['草图标注门宽 / 1:100', '正面十入口：每处2.5m'],3.2,7)
for i,(label,w) in enumerate([('IN A-J',2.5),('EX-L',6),('EX-C',8),('EX-R',6)]):
    yy=124+i*18
    line(p,445,yy,445+w*10,yy,.65)
    dimh(p,445,445+w*10,yy-4,yy,f'{label}: {w:g} m')
text(p,438,204,'门位/洞高/门型/宽度控制面 TBD',3)
drawrect(p,55,264,2.5,2.2,50,'W01 工位模块（含椅子/操作余量）')
drawrect(p,181,264,1.8,.8,50,'D01 桌面 / 10套；双屏尺寸 TBD')
notes(p,181,310,['桌面与模块分别标注尺寸。', '内部相对位置、朝向、座椅与双屏', '仅有功能要求，未新增物理尺寸。'],3.2,7)
# Screen is an elevation size range, not invented top-view depth.
box(p,315,258,160,44,.4,True)
box(p,315,258,120,36,.25,True)
dimh(p,315,475,248,258,'主屏宽 6-8 m（范围，未选值）')
dimv(p,258,302,307,315,'高 1.8-2.2 m')
text(p,395,279,'总览主屏 / 正立面尺寸边界',3.2,'middle')
text(p,395,288,'不是平面投影；厚度/墙位/标高 TBD',3,'middle')
notes(p,315,326,['工位通道范围：同排 1.2-1.5 m；前后 2.0-2.4 m。', '外圈巡查通道 1.5-2.0 m；最终取值及控制面 TBD。', '疏散楼梯无可引用的管理楼工程尺寸，本版不画踏步。'],3.2,7)

p=newpage('A104','工作人员区尺寸 / TBD 待确认清单','ST01 1:200；清单 NTS')
text(p,25,66,'只列影响本轮管理设施工程平面的事项；没有以建筑经验补齐任何未定值。',3.5)
drawrect(p,50,93,18,12,200,'ST01 工作人员区 / XY、边界控制面 TBD')
notes(p,170,93,['18×12m：本轮用户明确确认。', '升降台在该区后侧中央相对位置，3×3m；精确XY未定。', '草图楼梯在岛两端，文档要求边侧封闭疏散楼梯。', '后续定位需先解决该冲突；本版没有新增走道或井道尺寸。'],3.2,7)
y=180
for tid,title,desc in TBD:
    text(p,26,y,tid,3.5)
    text(p,47,y,title,3.4)
    text(p,138,y,desc,3)
    line(p,24,y+5,571,y+5,.15)
    y+=13
notes(p,25,338,['所有 CAD 尺寸内部单位为 mm，导出图用 m；约值为验证基准而非最终建造公差。', '零件和范围阵列有各自局部原点；未填写的建筑定位不是 (0,0)。', '2F 相对 1F 偏移、精确楼面标高、楼梯/升降台定位未确认，故未生成虚假的上下层3D对位。'],3.2,7)

def svg(page, geometry=True):
    ns='http://www.w3.org/2000/svg'
    root=ET.Element('svg',{'xmlns':ns,'xmlns:freecad':'http://www.freecadweb.org/wiki/index.php?title=Svg_Namespace','width':'594mm','height':'420mm','viewBox':'0 0 594 420'})
    ET.SubElement(root,'rect',{'width':'594','height':'420','fill':'white'})
    for it in page['items']:
        k=it['k']
        if k=='text':
            node=ET.SubElement(root,'text',{'x':str(it['x']),'y':str(it['y']),'font-size':str(it['size']),'font-family':'SimSun, Microsoft YaHei, sans-serif','text-anchor':it['anchor'],'fill':it.get('color','#111')})
            node.text=it['s']
        else:
            attrs={a:str(it[a]) for a in (['x','y','w','h'] if k=='rect' else ['x1','y1','x2','y2'])}
            if k=='rect':attrs['width']=attrs.pop('w');attrs['height']=attrs.pop('h')
            attrs.update({'stroke':'#111','stroke-width':str(it['lw']),'fill':'none'})
            if it.get('dash'):attrs['stroke-dasharray']='2 1.2'
            ET.SubElement(root,k,attrs)
    return ET.tostring(root,encoding='unicode')

drawings=group('DrawingPages','09 TechDraw 图纸（参数快照；重新生成可更新导出）')
blank_snapshot=OUT/'A2_symbol_template.svg'
blank_snapshot.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="594mm" height="420mm" viewBox="0 0 594 420"></svg>',encoding='utf-8')
for p in PAGES:
    file=OUT/(p['code']+'_v1.svg')
    file.write_text(svg(p),encoding='utf-8')
    page=doc.addObject('TechDraw::DrawPage',p['code'])
    page.Label=p['code']+' '+p['title']
    template=doc.addObject('TechDraw::DrawSVGTemplate',p['code']+'_Template')
    template.Template=str(blank_snapshot)
    page.Template=template
    symbol=doc.addObject('TechDraw::DrawViewSymbol',p['code']+'_Snapshot')
    svg_root=ET.fromstring(svg(p))
    svg_root.set('width','594');svg_root.set('height','420')
    symbol.Symbol=ET.tostring(svg_root,encoding='unicode')
    page.addView(symbol)
    symbol.X=297;symbol.Y=210;symbol.ScaleType='Custom';symbol.Scale=10;symbol.LockPosition=True
    symbol.Caption=''
    page.addProperty('App::PropertyString','SnapshotStatus','Evidence')
    page.SnapshotStatus='参数快照；编辑尺寸后重跑构建以更新本页和SVG/PDF。真实尺寸在Sketcher/投影视图可自动更新。'
    drawings.addObject(page)

# Native TechDraw projections provide model-driven editable CAD views as well
# as the fully annotated snapshot sheets. These pages are deliberately separate
# so a changed parameter can never silently disagree with a static annotation.
native=doc.addObject('TechDraw::DrawPage','CAD_Live')
native.Label='A105 实时CAD投影 | 内部 mm | 局部坐标视图'
blank=OUT/'A2_blank_live.svg'
blank.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="594mm" height="420mm" viewBox="0 0 594 420"><rect x="12" y="12" width="570" height="396" fill="none" stroke="black" stroke-width="0.3"/><text x="22" y="28" font-size="5" font-family="SimSun">A105 实时参数投影 / 各视图均为独立局部坐标 / 单位 mm</text></svg>',encoding='utf-8')
template=doc.addObject('TechDraw::DrawSVGTemplate','LiveTemplate')
template.Template=str(blank)
native.Template=template
drawings.addObject(native)
for source,name,x,y,scale in [(env1,'View1F',195,260,1/200),(env2,'View2F',470,285,1/200),(lift,'ViewLift',85,75,1/50),(desk,'ViewDesk',190,75,1/50),(module,'ViewModule',275,75,1/50),(wc,'ViewWC',390,75,1/50),(cab,'ViewCabinet',510,75,1/50),(staff,'ViewStaff',470,162,1/200)]:
    view=doc.addObject('TechDraw::DrawViewPart',name)
    view.Source=[source]
    view.Direction=App.Vector(0,0,1)
    view.ScaleType='Custom'
    view.Scale=scale
    view.Caption={'View1F':'1F 外包','View2F':'2F 外包','ViewLift':'L01','ViewDesk':'D01','ViewModule':'W01','ViewWC':'WC01','ViewCabinet':'EQ01','ViewStaff':'ST01'}[name]
    native.addView(view)
    view.X=x;view.Y=y
    view.LockPosition=True
    doc.recompute()
    for side,edge,dx,dy in [('W','Edge2',0,-(source.Shape.BoundBox.YLength*scale/2+10)),('D','Edge1',-(source.Shape.BoundBox.XLength*scale/2+12),0)]:
        dim=doc.addObject('TechDraw::DrawViewDimension',name+'_'+side)
        dim.Type='DistanceX' if side=='W' else 'DistanceY'
        dim.References2D=[(view,[edge])]
        dim.ShowUnits=True
        native.addView(dim)
        # Native dimensions use coordinates relative to their source view.
        dim.X=dx;dim.Y=dy
        dim.LockPosition=True
    note=doc.addObject('TechDraw::DrawViewAnnotation',name+'_ID')
    note.Text=[view.Caption];note.TextSize=3;note.Font='SimSun'
    view.Caption=''
    native.addView(note)
    note.X=x;note.Y=y;note.LockPosition=True

doc.recompute()
checks=[]
for source in [env1,env2,lift,desk,module,wc,cab,staff,front,rear_l,rear_c,rear_r]:
    assert source.FullyConstrained, f'{source.Name} is not fully constrained'
    assert source.Shape.isValid()
    bb=source.Shape.BoundBox
    checks.append({'name':source.Name,'fully_constrained':source.FullyConstrained,'width_m':bb.XLength/1000,'depth_m':bb.YLength/1000,'dof':source.FullyConstrained})
assert [m['id'] for m in sorted(CASES['Min']['modules'],key=lambda m:(-m['y_m'],m['x_m']))] == list('ABCDEFGHIJ')
assert len(stations.Group)==10
assert sum(x.DisplayCount for x in stations.Group)==20
assert len(openings.Group)==13
assert len(doc.A101.Views)==1 and doc.A101.Views[0].TypeId=='TechDraw::DrawViewSymbol'
for s in ['Min','Max']:
    assert CASES[s]['width_m']<40 and CASES[s]['depth_m']<30
errors=[{'object':o.Name,'state':o.State} for o in doc.Objects if any('invalid' in str(t).lower() or 'error' in str(t).lower() for t in o.State)]
if errors:raise RuntimeError(errors)
file=ROOT/'admin_facility_v1.FCStd'
doc.saveAs(str(file))
# Readback: persistence, expressions, native drawings and property links.
App.closeDocument(doc.Name)
read=App.openDocument(str(file))
read.recompute()
assert read.Envelope1F.FullyConstrained and read.Envelope2F.FullyConstrained
assert read.Lift1F.LinkedObject==read.Lift2F.LinkedObject
read.Parameters.Floor1Width=66000
read.recompute()
assert abs(read.Envelope1F.Shape.BoundBox.XLength-66000)<1e-6
read.Parameters.Floor1Width=65000
read.Parameters.SameRowGapMin=1300
read.recompute()
assert abs(read.ArrayMin_C.Placement.Base.x-1500)<1e-6
assert abs(read.ArrayMin_D.Placement.Base.x-(1500+2500+1300))<1e-6
read.Parameters.SameRowGapMin=1200
read.recompute()
# Validation changes are in memory only; saved baseline remains unchanged.
App.closeDocument(read.Name)
report={'freecad_version':App.Version(),'source_url':SPEC_URL,'source_blob_sha':'9a6c228210b9fef6b1471312afeda0987ebaf8ab','main_commit':'8bc29124bacb78d9d1fe84df7165d89765180e6c','source_sketches':['sources/facility_user_sketch_20260930.png','sources/facility_user_sketch_internal_20261006.png'],'checks':checks,'cad_errors':errors,'native_projection_count':8,'native_dimension_count':16,'front_entrance_count':10,'rear_exit_count':3,'workstation_count':10,'screen_count':20,'persistence_readback':True,'parameter_edit_recompute':True,'alignment_verified':False,'array_case_note':'both boundary checks, not selected design values; no 2F placement','array_cases':{k:{kk:vv for kk,vv in v.items() if kk!='objects'} for k,v in CASES.items()},'unresolved':TBD,'pages':PAGES}
(ROOT/'cad_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'fcstd':str(file),'sketches':len(checks),'pages':len(PAGES)+1,'array_cases':[(k,v['width_m'],v['depth_m']) for k,v in CASES.items()],'validation':'passed'},ensure_ascii=False))
