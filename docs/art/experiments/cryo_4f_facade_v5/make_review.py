from pathlib import Path
from PIL import Image,ImageDraw
import json,re
HERE=Path(__file__).resolve().parent;E=HERE/'evidence'
records=json.loads((E/'capture_record.json').read_text(encoding='utf-8'));by_file={r['file']:r for r in records}
for r in records:
 if r['file'].startswith('lateral_') or r['file']=='walk_crossing.png':
  assert len(r['facade_alphas'])==5 and all(abs(a-.42)<.001 for a in r['facade_alphas'].values())
for n in ['opposite_target','opposite_yellow','opposite_red','open_main_opposite_target','open_main_opposite_yellow','open_main_opposite_red']:
 r=by_file[n+'.png'];assert r['target']=='D005' and r['locked_prompt'] and not r['main_prompt']
assert by_file['open_main_opposite_target.png']['door_fraction']>.99
assert by_file['open_main_opposite_red.png']['last_interaction']['id']=='D005'
assert by_file['open_main_opposite_red.png']['last_interaction']['outcome']=='denied'
assert by_file['main_return_target.png']['main_prompt']=='E：休眠室へ'
assert by_file['returned_inside.png']['main_prompt']=='E：廊下へ'
assert json.loads((HERE/'functional_validation.json').read_text(encoding='utf-8'))['result']=='PASS'
def fig(n,t):return f'<figure><a href="evidence/{n}.png"><img loading="lazy" src="evidence/{n}.png"></a><figcaption>{t}</figcaption></figure>'
page=['''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>4F 横移透明与门目标修正 v5</title><style>body{margin:0 auto;max-width:1440px;padding:28px;background:#10191c;color:#dce8e8;font:16px/1.7 system-ui}h1{font-size:28px}h2{margin-top:40px}a{color:#a0dfd8}img{width:100%;image-rendering:pixelated;display:block}figure{margin:0}figcaption{padding:10px;color:#b6ced0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:16px}.note{border-left:3px solid #80cac0;background:#1c2a2e;padding:16px}</style><h1>4F 横移时整面墙一致半透明 · v5</h1><p class="note">运行入口不变：scenes/dev/cryo_4f_complete_v3.tscn，停止后重新F6。门、门楣和墙板共用同一墙中心平面判定，不再因人物横移让门单独恢复实体。提示与E共用最近门目标：走向对门只认证对门，主门开着也不会抢走交互。</p><p>保持42%不透明度、原像素材质、双面半透明；门后的灰色环境及Room1的黑色门洞继续保留。因此仍可能透过前景看到后方主门的黑色形状，它不是前景门单独恢复实体。<a href="README.md">源与验证</a> · <a href="functional_validation.json">完整功能回归</a> · <a href="evidence/capture_record.json">逐图alpha及交互目标</a></p><h2>用户提供的修前截图</h2><div class="grid">''',fig('user_before_side','横移时门单独变为近乎实体'),fig('user_before_center','站在门前时又变为半透明'),'</div><h2>修后：横向走位与真实移动</h2><p>六个横向位置的门板、门体、门楣及两侧墙均为0.42；以下四个位置另有实机截图。门后Room1门板／黑幕属于后景，保留其原状态。</p><div class="grid">']
for n,t in [('lateral_9_15','左侧位置 x=9.15m'),('lateral_9_8','x=9.8m'),('lateral_10_5','正对门 x=10.5m'),('lateral_11_4','右侧位置 x=11.4m'),('walk_crossing','实际横向行走越过门的投影中心')]:page.append(fig(n,t))
page.append('</div><h2>对门交互目标</h2><div class="grid">')
for n,t in [('opposite_target','走近对门：仅显示对门交互'),('opposite_yellow','E：对门黄闪'),('opposite_red','对门红色拒绝'),('open_main_opposite_target','主门仍全开时，走到对门：目标仍为对门'),('open_main_opposite_yellow','主门全开时按E：对门认证，不返回Room1'),('open_main_opposite_red','拒绝后仍在走廊'),('main_return_target','走回主门附近：才显示 E：休眠室へ'),('returned_inside','E返回室内，恢复 E：廊下へ')]:page.append(fig(n,t))
page.append('</div><p>修后原图1280×720。静态几何、UV、像素颜色和光图均未改；原整层楼梯／室内灰盒边界保持，新增生成0次。</p></html>')
html=''.join(page);assert all((HERE/t).exists() for t in re.findall(r'(?:href|src)="([^"]+)"',html))
(HERE/'preview.html').write_text(html,encoding='utf-8')
im=Image.new('RGB',(1280,764),(17,26,29));d=ImageDraw.Draw(im)
for i,n in enumerate(['lateral_9_15','lateral_9_8','lateral_10_5','lateral_11_4']):
 a=Image.open(E/(n+'.png')).convert('RGB');a.thumbnail((640,360));x=(i%2)*640;y=(i//2)*382;im.paste(a,(x,y));d.text((x+8,y+363),n,fill='#b6ced0')
im.save(E/'lateral_contact.jpg',quality=94)
print('FACADE_REVIEW_PASS')
