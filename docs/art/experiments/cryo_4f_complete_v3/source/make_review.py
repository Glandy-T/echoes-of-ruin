from pathlib import Path
from PIL import Image,ImageDraw
import json,html
EXP=Path(__file__).resolve().parent.parent;E=EXP/'evidence'
def sheet(names,out,cols=4,w=320):
 h=180+22;im=Image.new('RGB',(w*cols,h*((len(names)+cols-1)//cols)),(20,28,29));d=ImageDraw.Draw(im)
 for i,n in enumerate(names):
  p=E/(n+'.png');a=Image.open(p).convert('RGB');a.thumbnail((w,180));x=(i%cols)*w;y=(i//cols)*h;im.paste(a,(x,y));d.text((x+5,y+182),n.replace('tech_',''),fill='#b8cdce')
 im.save(E/(out+'.jpg'),quality=93)
game=['sw_room1','sw_middle','sw_inner_gate','sw_second_corridor','sw_foyer','west_stair_approach','se_corridor','nw_corridor','ne_corridor']
sheet(['denoised_'+s for s in game],'game_contact',3,400)
for raw in ['raw','denoised']:
 for i in range(8):sheet([f'tech_{raw}_c{i}_s{s}_p{p}' for s in [-1,1] for p in range(8)],f'contact_{raw}_c{i}')
 sheet([f'tech_{raw}_floor_c{i}_p{p}' for i in range(8) for p in range(4)],f'contact_{raw}_floors')
def figure(name,label):return f'<figure><a href="evidence/{name}.png"><img loading="lazy" src="evidence/{name}.png" alt="{html.escape(label)}"></a><figcaption>{label}</figcaption></figure>'
parts=['''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>4F 整层外壳与走廊 v3</title><style>body{margin:0 auto;max-width:1440px;padding:28px;background:#10191c;color:#dce8e8;font:16px/1.65 system-ui}h1{font-size:28px}h2{margin-top:44px}p{max-width:1050px}a{color:#9bdedb}img{width:100%;image-rendering:pixelated;display:block}figure{margin:0 0 20px}figcaption{padding:8px;color:#b2c8ca}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:16px}.note{padding:16px;border-left:3px solid #70bab5;background:#19272a}select{font:inherit;padding:8px;color:inherit;background:#25383c}details{margin:16px 0}summary{cursor:pointer}</style><h1>4F 整层外壳与走廊 v3 · 实机待审</h1><p>2026-11-04。48间房按冻结布局补齐外壳；仅 Room 1 保留现有20舱，其余47间不制作舱内。墙r24、过道地坪r26继续复用，新增生成0次。走廊共用一套4096采样烘焙；颜色贴图保持原生像素。楼梯入口继续沿用已有灰盒。</p><p class="note">当前为独立 F6：scenes/dev/cryo_4f_complete_v3.tscn。WASD移动；E认证，门开后再次E进出黑门洞；F7遮挡透明；F8回门外；F11整层俯视；F12技术切区；F9灯带；F10 raw／降噪。正式F5仍为r19。其他门维持权限锁定，技术切区不授予游戏通行权限。</p><p><a href="README.md">源工程、复建步骤及边界</a> · <a href="functional_validation.json">功能验证</a> · <a href="bake_validation.json">UV／HDR／版本校验</a></p><h2>整层外壳</h2>''',figure('full_floor_overview','技术俯视：仅左下SW-01具有室内舱体，其他房间为空壳。编号仅技术总览显示。'),'<h2>游戏镜头</h2><p>相同相机和曝光，1280×720输出。默认降噪，可比较未降噪线性光照。点击图片查看原尺寸。</p><select id="zone">'+''.join(f'<option value="{s}">{s}</option>' for s in game)+'</select><div class="grid"><figure><img id="raw"><figcaption>raw：未降噪烘焙经连续UV2重投影</figcaption></figure><figure><img id="denoised"><figcaption>denoised：默认</figcaption></figure></div><script>const z=document.getElementById("zone");function refresh(){for(const mode of ["raw","denoised"])document.getElementById(mode).src="evidence/"+mode+"_"+z.value+".png"}z.onchange=refresh;refresh()</script><h2>开门后互动</h2><div class="grid">']
for n,t in [('portal_01_idle','靠近门不会自动认证'),('portal_02_authenticating','第一次E：认证'),('portal_03_open_black','门开后出现 E：廊下へ，门洞保持全黑'),('portal_04_transfer_black','第二次E：全黑时转镜及换位'),('portal_05_outside','外侧 E：休眠室へ'),('portal_06_inside_restored','E返回室内，恢复原方向')]:parts.append(figure(n,t))
parts+=['</div><h2>遮挡透明</h2><div class="grid">',figure('occlusion_on','透明开启：只留下邻室墙的半透明轮廓'),figure('occlusion_off','透明关闭：实体墙遮挡视线'),figure('occlusion_restored','恢复透明：碰撞始终保留'),'</div><h2>全走廊技术巡检</h2><p>八条走廊，两侧墙各八段重叠近景，另有分段地面；同时保留raw和降噪。技术相机留在走廊，墙体恢复不透明，地坪检查时临时隐藏外壳。下方联系表可点击每张原图。</p>']
for i in range(8):
 parts.append(f'<details><summary>走廊 {i}：两侧完整墙面／门楣／墙脚／灯槽</summary>')
 for mode in ['raw','denoised']:
  parts.append(f'<p>{mode}</p><img loading="lazy" src="evidence/contact_{mode}_c{i}.jpg"><p>')
  parts.extend(f'<a href="evidence/tech_{mode}_c{i}_s{s}_p{p}.png">{s}/{p}</a> ' for s in [-1,1] for p in range(8));parts.append('</p>')
 parts.append('</details>')
for mode in ['raw','denoised']:parts.append(f'<details><summary>全部分段地坪 {mode}</summary><img loading="lazy" src="evidence/contact_{mode}_floors.jpg"></details>')
parts.append('<h2>当前边界</h2><p>这是整层外壳和走廊的试运行候选，等待用户判断空壳透明效果；其他房间没有可进入室内。楼梯入口、公共区专用门型、电梯和正式3D主角尚未完成美术。保留既有权限与剧情，未扩展至1F室外。全层光图密度16px/m，低于局部v2的120px/m；材质仍80px/m，光照平滑程度与像素原画密度分别记录。</p>')
(EXP/'preview.html').write_text(''.join(parts),encoding='utf-8')
print('REVIEW_PAGE_READY')
