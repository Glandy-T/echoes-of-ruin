"""Build the single-storey administration-facility spatial review in FreeCAD.

Run with G:/卒業制作/FreeCAD_1.1.4-Windows-x86_64-py311/bin/python.exe.
This script deliberately records unresolved locations and construction values as
TBD.  It does not convert concept-sketch dimensions into construction values.
"""
from pathlib import Path
import json
import math
import xml.etree.ElementTree as ET

import FreeCAD as App
import Part
import Sketcher
import TechDraw

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "exports"
OUT.mkdir(exist_ok=True)
COMMIT = "d67e58a89410abfc42f48a28dcbe2228a1b12a90"
BLOB = "1244a2238e522a888d71199cf62f233b55a5e37f"
SPEC_URL = "https://github.com/Glandy-T/echoes-of-ruin/blob/%s/docs/CRYO_FACILITY_LAYOUT.md" % COMMIT

TBD = [
    ("T01", "外包与结构", "最终外包尺寸、墙厚、结构与构造控制面 TBD；65×45 m 仅为当前可编辑验证基准。"),
    ("T02", "工作人员区", "18×12 m 是用户确认的概念分区边界；精确 XY、边界、出入口与内部工位 TBD。"),
    ("T03", "中央内部厕所", "原升降台关系位置已知；尺寸、洁具、门、边界和控制面 TBD。"),
    ("T04", "左右公共厕所", "面积、位置、厕位、无障碍配置、边界及门 TBD。"),
    ("T05", "入口组与认证", "入口组净宽、中心 X、闸机数量、认证进深、排队与异常分流 TBD。"),
    ("T06", "后出口", "三个出口的净宽、中心 X、门型、控制面及通往园区的流线 TBD。"),
    ("T07", "吞吐输入", "峰值到场率、各组服务率、出口实测流率、停留时间与分流比例 TBD；无这些输入不能给出吞吐结论。"),
    ("T08", "导视与工作人员工位", "导视占地，以及工作人员监控/日志工位实际需要与数量 TBD。"),
    ("T09", "标高与屋面", "准确标高、屋面及层高范围控制面 TBD。"),
]

doc = App.newDocument("AdminFacilityV2")
doc.Label = "管理设施 v2 | 单层空间验证 | 定位与吞吐 TBD"

def group(name, label):
    obj = doc.addObject("App::DocumentObjectGroup", name)
    obj.Label = label
    return obj

def prop(obj, typ, name, group_name, value=None):
    obj.addProperty(typ, name, group_name)
    if value is not None:
        setattr(obj, name, value)
    return obj

params = doc.addObject("App::FeaturePython", "Parameters")
params.Label = "参数表 | 已确认尺寸与历史草图参考"
prop(params, "App::PropertyLength", "EnvelopeWidth", "Confirmed", 65000.0)
prop(params, "App::PropertyLength", "EnvelopeDepth", "Confirmed", 45000.0)
prop(params, "App::PropertyLength", "StaffWidth", "Confirmed", 18000.0)
prop(params, "App::PropertyLength", "StaffDepth", "Confirmed", 12000.0)
for name, val in [("HistoricEntranceWidth", 2500.0), ("HistoricRearLeftWidth", 6000.0),
                  ("HistoricRearCenterWidth", 8000.0), ("HistoricRearRightWidth", 6000.0)]:
    prop(params, "App::PropertyLength", name, "Historical sketch reference", val)
prop(params, "App::PropertyString", "CoordinateConvention", "Documentation", "+X: 左至右；+Y: 正面至后侧；O: 外包左前角")
prop(params, "App::PropertyString", "Status", "Documentation", "当前验证基准；历史门宽不能作为最终入口组/出口净宽")

def constrained_rectangle(name, label, width_expr, depth_expr):
    sk = doc.addObject("Sketcher::SketchObject", name)
    sk.Label = label
    pts = [(0, 0), (1, 0), (1, 1), (0, 1)]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        sk.addGeometry(Part.LineSegment(App.Vector(*a, 0), App.Vector(*b, 0)), False)
    for i in range(4):
        sk.addConstraint(Sketcher.Constraint("Coincident", i, 2, (i + 1) % 4, 1))
    sk.addConstraint(Sketcher.Constraint("Horizontal", 0))
    sk.addConstraint(Sketcher.Constraint("Vertical", 1))
    sk.addConstraint(Sketcher.Constraint("Horizontal", 2))
    sk.addConstraint(Sketcher.Constraint("Vertical", 3))
    sk.addConstraint(Sketcher.Constraint("DistanceX", 0, 1, 0.0))
    sk.addConstraint(Sketcher.Constraint("DistanceY", 0, 1, 0.0))
    widx = sk.addConstraint(Sketcher.Constraint("Distance", 0, 1.0))
    didx = sk.addConstraint(Sketcher.Constraint("Distance", 1, 1.0))
    sk.setExpression("Constraints[%d]" % widx, width_expr)
    sk.setExpression("Constraints[%d]" % didx, depth_expr)
    return sk

geometry = group("Geometry", "01 已确认几何 | 原点 O = 外包左前角")
envelope = constrained_rectangle("Envelope", "管理设施单层外包 | 65×45 m 验证基准", "Parameters.EnvelopeWidth", "Parameters.EnvelopeDepth")
staff = constrained_rectangle("StaffArea", "工作人员/异常处理区 | 18×12 m 独立局部坐标", "Parameters.StaffWidth", "Parameters.StaffDepth")
geometry.addObject(envelope)
geometry.addObject(staff)
prop(envelope, "App::PropertyString", "LocationStatus", "Evidence", "O=外包左前角；+X左到右，+Y正面到后侧")
prop(staff, "App::PropertyString", "LocationStatus", "Evidence", "独立局部原点；建筑内精确XY=TBD；默认原点不是落位")
for obj in (envelope, staff):
    prop(obj, "App::PropertyString", "GeometryMeaning", "Evidence", "外包/概念分区边界，无墙厚或施工控制面")
    obj.Visibility = obj == envelope

historical = group("HistoricalWidths", "历史草图宽度线 | 独立局部坐标；非最终净宽")
historical_sketches = []
for name, label, key in [("HistoricFront", "前入口草图每处2.5m", "HistoricEntranceWidth"),
                         ("HistoricRearLeft", "左后出口草图6m", "HistoricRearLeftWidth"),
                         ("HistoricRearCenter", "中后出口草图8m", "HistoricRearCenterWidth"),
                         ("HistoricRearRight", "右后出口草图6m", "HistoricRearRightWidth")]:
    sk = doc.addObject("Sketcher::SketchObject", name)
    sk.Label = label + " | 实际入口组/出口净宽 TBD"
    sk.addGeometry(Part.LineSegment(App.Vector(0,0,0), App.Vector(getattr(params,key).Value,0,0)), False)
    sk.addConstraint(Sketcher.Constraint("Coincident",0,1,-1,1))
    sk.addConstraint(Sketcher.Constraint("Horizontal",0))
    ci = sk.addConstraint(Sketcher.Constraint("Distance",0,getattr(params,key).Value))
    sk.setExpression("Constraints[%d]" % ci, "Parameters." + key)
    prop(sk,"App::PropertyString","LocationStatus","Evidence","独立局部宽度线；位置/控制面/最终净宽TBD")
    historical.addObject(sk)
    historical_sketches.append(sk)
    sk.Visibility = False

pending = group("Unresolved", "T01-T09 待确认 | 无数值默认值")
for tid, title, detail in TBD:
    issue = doc.addObject("App::FeaturePython", tid)
    issue.Label = tid + " " + title + " | TBD"
    prop(issue,"App::PropertyString","Status","Pending","TBD")
    prop(issue,"App::PropertyString","Question","Pending",detail)
    pending.addObject(issue)

schedule = doc.addObject("Spreadsheet::Sheet", "ParameterSchedule")
schedule.Label = "参数与来源 | v2快照；编辑 Parameters 更新模型"
for col, value in zip("ABCD", ["参数", "m", "依据", "状态"]):
    schedule.set(col + "1", value)
for row, values in enumerate([
    ["外包宽/深", "65 / 45", "权威规格4.1", "验证基准，最终外包TBD"],
    ["工作人员区宽/深", "18 / 12", "用户明确确认", "概念分区边界，XY和控制面TBD"],
    ["历史前入口每处", "2.5", "用户内部草图", "入口组实际宽及净宽TBD"],
    ["历史后出口左/中/右", "6 / 8 / 6", "用户内部草图", "实际净宽/吞吐TBD"],
    ["层高范围", "5.5 - 6", "权威规格4.1", "没有选定准确高度/控制面"],
],2):
    for col,value in zip("ABCD",values):schedule.set(col + str(row),value)
for col,width in zip("ABCD",[170,110,180,260]):schedule.setColumnWidth(col,width)

semantic = group("SemanticObjects", "02 语义对象 | 坐标与净尺寸均 TBD")
def tbd_object(name, label, relation):
    o = doc.addObject("App::FeaturePython", name)
    o.Label = label
    prop(o, "App::PropertyString", "Status", "TBD", "位置、净尺寸及边界控制面 TBD；绝不用默认零值替代")
    prop(o, "App::PropertyString", "Relation", "TBD", relation)
    prop(o, "App::PropertyString", "Coordinate", "TBD", "TBD")
    prop(o, "App::PropertyString", "ClearSize", "TBD", "TBD")
    semantic.addObject(o)
    return o

for letter in "ABCDEFGHIJ":
    tbd_object("Entrance_" + letter, "入口组 " + letter + " | 认证后进入共享汇流大厅", "正面；A-J 左至右顺序已确认")
for title, relation in [("RearExit_Left", "后侧左出口；不绑定固定楼栋"),
                        ("RearExit_Center", "后侧中出口；不绑定固定楼栋"),
                        ("RearExit_Right", "后侧右出口；不绑定固定楼栋"),
                        ("PublicWC_Left", "共享大厅左侧公共厕所节点"),
                        ("PublicWC_Right", "共享大厅右侧公共厕所节点"),
                        ("StaffWC_Internal", "工作人员区中央原升降台关系位置；仅内部使用")]:
    tbd_object(title, title.replace("_", " ") + " | 关系符号", relation)
for name, relation in [("Guide_Left", "共享大厅左侧必要地图/电子导视占位"),
                       ("Guide_Right", "共享大厅右侧必要地图/电子导视占位")]:
    tbd_object(name, name + " | 导视关系占位", relation)

area = doc.addObject("App::FeaturePython", "AreaReview")
area.Label = "面积复核 | 非净面积/非功能配额"
prop(area, "App::PropertyArea", "GrossArea", "Area review")
prop(area, "App::PropertyArea", "StaffArea", "Area review")
prop(area, "App::PropertyArea", "UnallocatedGrossDifference", "Area review")
area.setExpression("GrossArea", "Parameters.EnvelopeWidth * Parameters.EnvelopeDepth")
area.setExpression("StaffArea", "Parameters.StaffWidth * Parameters.StaffDepth")
area.setExpression("UnallocatedGrossDifference", "AreaReview.GrossArea - AreaReview.StaffArea")
prop(area, "App::PropertyString", "Interpretation", "Area review", "外包与工作人员区毛面积差额包含共享大厅、认证、待定厕所与墙体；不是闲置净面积，不能据此自行缩小外包。")

def m2(v):
    return round(v.getValueAs("m^2").Value, 6)

# Paper primitive schema is intentionally compatible with v1 render_pdf.py.
PAGES = []
def text(p, x, y, s, size=3.2, anchor="start", color="#111111"):
    p["items"].append({"k":"text", "x":x, "y":y, "s":s, "size":size, "anchor":anchor, "color":color})
def line(p, x1, y1, x2, y2, lw=.25, dash=False):
    p["items"].append({"k":"line", "x1":x1, "y1":y1, "x2":x2, "y2":y2, "lw":lw, "dash":dash})
def box(p, x, y, w, h, lw=.4, dash=False):
    p["items"].append({"k":"rect", "x":x, "y":y, "w":w, "h":h, "lw":lw, "dash":dash})
def arrow(p, x1, y1, x2, y2):
    line(p, x1, y1, x2, y2, .35)
    a = math.atan2(y2-y1, x2-x1)
    for sign in (-1, 1):
        q = a + math.pi + sign*.42
        line(p, x2, y2, x2+2.1*math.cos(q), y2+2.1*math.sin(q), .35)
def dimh(p, x1, x2, y, target_y, label):
    line(p, x1, y, x2, y, .25)
    for x in (x1, x2):
        line(p, x-1.1, y+1.1, x+1.1, y-1.1, .3); line(p, x, y, x, target_y, .18)
    text(p, (x1+x2)/2, y-2.2, label, 3.2, "middle")
def dimv(p, y1, y2, x, target_x, label):
    line(p, x, y1, x, y2, .25)
    for y in (y1, y2):
        line(p, x-1.1, y+1.1, x+1.1, y-1.1, .3); line(p, x, y, target_x, y, .18)
    text(p, x-3, (y1+y2)/2, label, 3.2, "end")
def newpage(code, title, scale):
    p = {"code":code, "title":title, "scale":scale, "width_mm":594, "height_mm":420, "items":[]}
    PAGES.append(p)
    box(p, 12, 12, 570, 396, .45)
    text(p, 22, 27, "ECHOES OF RUIN / 管理设施单层空间验证", 5)
    text(p, 22, 37, title, 5)
    text(p, 22, 47, "单位 m；实线尺寸为已确认基准。虚线、关系符号与历史草图参考均不可量取定位。", 3)
    line(p, 12, 374, 582, 374, .4)
    for x in (360, 475, 533): line(p, x, 374, x, 408, .35)
    text(p, 20, 384, "依据：CRYO_FACILITY_LAYOUT.md §§4-5；GitHub main " + COMMIT[:12], 3)
    text(p, 20, 393, "状态：v2 单层验证；图页/导出为参数快照；位置/构造/吞吐 TBD。", 3)
    text(p, 368, 384, "比例 / A2 100%", 3); text(p, 368, 397, scale, 3.2)
    text(p, 483, 384, "图号", 3); text(p, 483, 398, code, 5)
    text(p, 541, 384, "版本", 3); text(p, 541, 398, "v2", 5)
    return p
def draw_rect_m(p, x, y, width, depth, scale, label):
    w, h = width*1000/scale, depth*1000/scale
    box(p, x, y, w, h, .5)
    dimh(p, x, x+w, y-8, y, "≈ %g m" % width)
    dimv(p, y, y+h, x-8, x, "≈ %g m" % depth)
    text(p, x+w/2, y+h+8, label, 3.2, "middle")
def notes(p, x, y, rows, gap=6, size=3.1):
    for i, row in enumerate(rows): text(p, x, y+i*gap, row, size)

p = newpage("A201", "管理设施单层 / 外包平面与功能关系", "主图 1:200；关系 NTS")
draw_rect_m(p, 65, 100, 65, 45, 200, "前侧：A-J 十入口；后侧：园区 / 三出口")
p["items"][-1]["y"] = 350
text(p, 227.5, 75, "+Y 后侧 / 园区", 3.3, "middle")
text(p, 227.5, 335, "+X 左→右；O=(0,0) 外包左前角", 3.1, "middle")
for i, letter in enumerate("ABCDEFGHIJ"):
    x = 82 + i*32.3
    box(p, x-4, 296, 8, 4, .28, True); text(p, x, 292, letter, 3.5, "middle")
    arrow(p, x, 288, x, 275)
text(p, 227.5, 311, "正面：十个入口组 → 自动芯片认证（闸机/净宽/定位 TBD）", 3.1, "middle")
line(p, 77, 267, 378, 267, .4, True); text(p, 227.5, 260, "自动认证区 / 深度、设备、异常支路 TBD", 3.1, "middle")
box(p, 172, 171, 111, 62, .35, True)
text(p, 227.5, 183, "工作人员 / 异常处理区", 3.8, "middle")
text(p, 227.5, 192, "18×12m 独立详图见 A202", 3.1, "middle")
text(p, 227.5, 225, "精确 XY 与边界控制面 TBD", 3.0, "middle")
box(p, 214, 197, 27, 11, .3, True); text(p, 227.5, 204, "内部厕所 / NTS", 2.8, "middle")
for x, label in ((120, "公共厕所 左 / NTS"), (335, "公共厕所 右 / NTS")):
    box(p, x-18, 201, 36, 17, .3, True); text(p, x, 211, label, 2.8, "middle")
for x in (120,335):
    box(p,x-12,180,24,2,.28,True)
    text(p,x,176,"地图/导视 NTS",2.8,"middle")
text(p, 227.5, 247, "共享汇流大厅 / 边界与主通道净宽 TBD", 3.6, "middle")
for x, lab in ((130, "后出口 左"), (227.5, "后出口 中"), (325, "后出口 右")):
    box(p, x-10, 145, 20, 4, .3, True); text(p, x, 160, lab + " / TBD", 2.8, "middle")
    arrow(p, x, 168, x, 153)
notes(p, 404, 88, ["运营关系 / NTS", "入口组认证后进入共享大厅。", "十条流线不再强制隔离。", "后侧左/中/右出口不固定对应楼栋。", "认证异常 → 工作人员处理区。", "两侧公共厕所不得侵占主流线。", "所有关系符号不代表墙、门位或净尺寸。"], 7, 3.2)
notes(p, 404, 211, ["历史草图门宽仅供比较：", "正面 A-J：每处 2.5 m", "后侧 左/中/右：6 / 8 / 6 m", "实际入口组/出口净宽 TBD。", "没有客流、服务率和净宽输入，", "本页不做吞吐结论。"], 7, 3.2)

p = newpage("A202", "工作人员区 / 独立局部尺寸与卫生关系", "工作人员区 1:100；关系 NTS")
draw_rect_m(p, 68, 112, 18, 12, 100, "ST01 工作人员 / 异常处理区")
text(p, 158, 85, "18×12m 用户确认的概念分区边界；建筑内定位 TBD。", 3.2, "middle")
box(p, 137, 162, 42, 20, .3, True); text(p, 158, 170, "内部厕所 / NTS", 3.1, "middle")
text(p, 158, 177, "尺寸 TBD", 2.7, "middle")
text(p, 158, 190, "中央原升降台关系位置", 2.9, "middle")
text(p, 158, 205, "净尺寸、洁具、门、墙体及精确位置 TBD", 3, "middle")
notes(p, 315, 108, ["卫生关系 / 不按比例", "公共厕所 左：共享大厅左侧 / TBD", "公共厕所 右：共享大厅右侧 / TBD", "工作人员内部厕所：ST01 中央 / TBD", "中央不设公共厕所。", "不画厕位、洁具或门，避免虚构工程尺寸。"], 7, 3.2)
box(p, 340, 166, 68, 29, .3, True); text(p, 374, 183, "公共厕所 左 / NTS", 3.3, "middle")
box(p, 467, 166, 68, 29, .3, True); text(p, 501, 183, "公共厕所 右 / NTS", 3.3, "middle")
arrow(p, 408, 181, 447, 181); arrow(p, 467, 181, 428, 181)
text(p, 438, 173, "共享大厅", 3.1, "middle")
notes(p, 68, 276, ["独立历史草图宽度线 / 不是建筑落位，也不是最终净宽", "十入口 A-J：10 × 2.5m = 25m（条件比较）", "后出口 左/中/右：6 + 8 + 6m = 20m（条件比较）", "这两个总和不代表可通过人数、能力充足，或“20% 缺口”。"], 7, 3.2)
text(p, 430, 303, "以下独立宽度线 1:100；历史输入", 3.1, "middle")
for x,y,lab,w in [(65,339,"历史前入口每处",2.5), (182,339,"历史后出口左",6),
                  (322,339,"历史后出口中",8), (467,339,"历史后出口右",6)]:
    line(p,x,y,x+w*10,y,.7)
    dimh(p,x,x+w*10,y-8,y,"%g m" % w)
    text(p,x+w*5,y+8,lab,3,"middle")
text(p, 297, 361, "宽度控制面/入口组实际尺度/最终净宽均 TBD；以上线段未放入建筑。", 3, "middle")

p = newpage("A203", "面积复核 / 吞吐条件 / TBD 集中问题", "表格与公式 NTS")
text(p, 30, 70, "面积复核（模型 AreaReview 由表达式驱动；本页为当前参数快照）", 4)
for y, name, value, note in [(90, "外包毛面积", "2,925 m²", "65×45m 当前验证基准"),
                              (106, "工作人员区", "216 m²", "18×12m 已确认"),
                              (122, "未分配毛面积差额", "2,709 m²", "含大厅、认证、待定厕所、墙体等；非闲置净面积")]:
    box(p, 30, y-9, 390, 13, .25); text(p, 40, y, name, 3.2); text(p, 185, y, value, 3.2); text(p, 275, y, note, 2.8)
text(p, 30, 157, "吞吐验证：尚无结论。先收集下列输入，才可计算而非凭门数或行业经验猜测。", 3.6)
for y, s in enumerate(["Q_peak = 高峰到达人数 / 时间窗", "每入口组能力 = 并行闸机数量 × 单闸机服务率", "后出口能力 = 各出口有效净宽与步行流量关系（待选定）", "平衡条件：认证总处理能力 ≥ Q_peak；出口总处理能力 ≥ Q_peak", "还需：分配到场曲线、异常比例、认证失败处理时间、候流可用面积与安全条件。"], start=176):
    text(p, 42, y + (y-176)*7, "• " + s, 3.15)
text(p, 30, 246, "TBD 集中问题", 4)
y = 263
for tid, title, desc in TBD:
    text(p, 32, y, tid, 3.2); text(p, 59, y, title, 3.2); text(p, 143, y, desc, 2.65)
    line(p, 30, y+4, 565, y+4, .14); y += 10
text(p, 30, 367, "未选择墙厚、门宽、厕位、闸机、结构或任何默认零值。无 2F、楼梯、升降台、十工位、主屏、原 2F 卫生间/柜区。", 2.9)

def svg(page):
    root = ET.Element("svg", {"xmlns":"http://www.w3.org/2000/svg", "xmlns:freecad":"http://www.freecadweb.org/wiki/index.php?title=Svg_Namespace", "width":"594mm", "height":"420mm", "viewBox":"0 0 594 420"})
    ET.SubElement(root, "rect", {"width":"594", "height":"420", "fill":"white"})
    for it in page["items"]:
        if it["k"] == "text":
            e = ET.SubElement(root, "text", {"x":str(it["x"]), "y":str(it["y"]), "font-size":str(it["size"]), "font-family":"SimSun, Microsoft YaHei, sans-serif", "text-anchor":it["anchor"], "fill":it.get("color", "#111")})
            e.text = it["s"]
        else:
            attrs = ({"x":str(it["x"]), "y":str(it["y"]), "width":str(it["w"]), "height":str(it["h"])} if it["k"] == "rect" else {"x1":str(it["x1"]), "y1":str(it["y1"]), "x2":str(it["x2"]), "y2":str(it["y2"])})
            attrs.update({"stroke":"#111", "stroke-width":str(it["lw"]), "fill":"none"})
            if it.get("dash"): attrs["stroke-dasharray"] = "2 1.2"
            ET.SubElement(root, it["k"], attrs)
    return ET.tostring(root, encoding="unicode")

drawings = group("DrawingPages", "03 TechDraw 图纸 | 参数快照与实时投影")
blank_snap = OUT / "A2_symbol_template.svg"
blank_snap.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="594mm" height="420mm" viewBox="0 0 594 420"></svg>', encoding="utf-8")
for page_data in PAGES:
    (OUT / (page_data["code"] + "_v2.svg")).write_text(svg(page_data), encoding="utf-8")
    page = doc.addObject("TechDraw::DrawPage", page_data["code"])
    page.Label = page_data["code"] + " " + page_data["title"]
    template = doc.addObject("TechDraw::DrawSVGTemplate", page_data["code"] + "_Template")
    template.Template = str(blank_snap)
    page.Template = template
    symbol = doc.addObject("TechDraw::DrawViewSymbol", page_data["code"] + "_Snapshot")
    root = ET.fromstring(svg(page_data)); root.set("width", "594"); root.set("height", "420")
    symbol.Symbol = ET.tostring(root, encoding="unicode")
    page.addView(symbol); symbol.X = 297; symbol.Y = 210; symbol.ScaleType = "Custom"; symbol.Scale = 10; symbol.LockPosition = True; symbol.Caption = ""
    prop(page, "App::PropertyString", "SnapshotStatus", "Evidence", "参数快照；编辑后需重跑构建来更新 SVG/PDF。")
    drawings.addObject(page)

live = doc.addObject("TechDraw::DrawPage", "CAD_Live")
live.Label = "A204 实时 CAD 投影 | 单层 v2"
blank_live = OUT / "A2_blank_live.svg"
blank_live.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="594mm" height="420mm" viewBox="0 0 594 420"><rect x="12" y="12" width="570" height="396" fill="none" stroke="black" stroke-width="0.3"/><text x="22" y="28" font-size="5" font-family="SimSun">A204 实时参数投影 / 管理设施单层 v2</text><text x="22" y="40" font-size="3.2" font-family="SimSun">尺寸自动带 m/mm；各视图独立局部原点；未构成建筑内定位。</text></svg>', encoding="utf-8")
tmpl = doc.addObject("TechDraw::DrawSVGTemplate", "LiveTemplate"); tmpl.Template = str(blank_live); live.Template = tmpl; drawings.addObject(live)
for source, name, x, y, scale, caption in [(envelope, "ViewEnvelope", 207.5, 235, 1/200, "外包验证基准 | 1:200"), (staff, "ViewStaff", 490, 170, 1/100, "工作人员区 | 独立局部原点 | 1:100")]:
    view = doc.addObject("TechDraw::DrawViewPart", name)
    view.Source = [source]; view.Direction = App.Vector(0, 0, 1); view.ScaleType = "Custom"; view.Scale = scale
    live.addView(view); view.X = x; view.Y = y; view.LockPosition = True; view.Caption = ""
    doc.recompute()
    for side, edge, dx, dy in (("W", "Edge2", 0, -(source.Shape.BoundBox.YLength*scale/2+10)), ("D", "Edge1", -(source.Shape.BoundBox.XLength*scale/2+13), 0)):
        dim = doc.addObject("TechDraw::DrawViewDimension", name + "_" + side)
        dim.Type = "DistanceX" if side == "W" else "DistanceY"; dim.References2D = [(view, [edge])]; dim.ShowUnits = True
        live.addView(dim); dim.X = dx; dim.Y = dy; dim.LockPosition = True
    ann = doc.addObject("TechDraw::DrawViewAnnotation", name + "_Label")
    ann.Text = [caption]; ann.TextSize = 3; ann.Font = "SimSun"; live.addView(ann); ann.X = x; ann.Y = y; ann.LockPosition = True

doc.recompute()
assert envelope.FullyConstrained and staff.FullyConstrained
assert all(s.FullyConstrained and s.Shape.isValid() for s in historical_sketches)
assert round(m2(area.GrossArea)) == 2925 and round(m2(area.StaffArea)) == 216 and round(m2(area.UnallocatedGrossDifference)) == 2709
errors = [{"object":o.Name, "state":list(o.State)} for o in doc.Objects if any("invalid" in str(s).lower() or "error" in str(s).lower() for s in o.State)]
if errors: raise RuntimeError(errors)
fcstd = ROOT / "admin_facility_v2.FCStd"
doc.saveAs(str(fcstd))
App.closeDocument(doc.Name)

read = App.openDocument(str(fcstd)); read.recompute()
assert read.Envelope.FullyConstrained and read.StaffArea.FullyConstrained
assert len(read.CAD_Live.Views) >= 2
read.Parameters.EnvelopeWidth = 66000; read.recompute()
assert round(m2(read.AreaReview.GrossArea)) == 2970 and round(m2(read.AreaReview.UnallocatedGrossDifference)) == 2754
read.Parameters.EnvelopeWidth = 65000; read.recompute()
App.closeDocument(read.Name)

report = {
    "freecad_version": App.Version(), "source_url": SPEC_URL, "source_blob_sha": BLOB, "main_commit": COMMIT,
    "scope": "single-storey administration facility v2", "confirmed": {"envelope_m":[65,45], "staff_area_m":[18,12], "gross_area_m2":2925, "staff_area_m2":216, "unallocated_gross_difference_m2":2709},
    "coordinate_convention": "+X left-to-right; +Y front-to-rear; O=outer-envelope front-left", "front_entrance_groups": list("ABCDEFGHIJ"), "rear_exit_count":3,
    "toilets": ["PublicWC_Left", "PublicWC_Right", "StaffWC_Internal"], "no_default_zero_for_tbd": True,
    "fully_constrained_sketches": ["Envelope", "StaffArea", "HistoricFront", "HistoricRearLeft", "HistoricRearCenter", "HistoricRearRight"], "area_expression_update_verified": True,
    "snapshot_pages": [p["code"] for p in PAGES], "live_page": "A204", "live_views": 2, "live_dimensions": 4,
    "unresolved": [{"id":a,"title":b,"detail":c} for a,b,c in TBD], "cad_errors": errors, "no_2f_or_lift_or_stairs": True,
    "pages": PAGES,
    "source_sketches": ["sources/facility_user_sketch_20260930.png", "sources/facility_user_sketch_internal_20261006.png"],
    "static_exports_note": "A201-A203/SVG/PDF/参数表为v2快照；编辑Parameters后先复制新修订并同步构建输入再重建，直接运行本脚本会覆盖v2。A204与面积对象随参数更新。",
}
(ROOT / "cad_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"fcstd":str(fcstd), "sketches":"fully constrained", "pages":[p["code"] for p in PAGES] + ["A204"], "validation":"passed"}, ensure_ascii=False))
