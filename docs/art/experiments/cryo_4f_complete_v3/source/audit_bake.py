"""Reopen exported runtime geometry and verify the matched HDR set."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,runpy,math
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];EXP=HERE.parent;OUT=ROOT/'assets/art/cryo_4f_complete_v3'
manifest=json.loads((OUT/'manifest.json').read_text());layout=json.loads((OUT/'layout.json').read_text())
hashes={n:hashlib.sha256((OUT/n).read_bytes()).hexdigest()==h for n,h in manifest['files'].items()};assert all(hashes.values())
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(OUT/'cryo_4f_complete_v3.glb'))
receivers=[bpy.data.objects[n] for n in layout['receivers']]
for ob in receivers:
 assert len(ob.data.uv_layers)==2
 ob.data.uv_layers[1].name='LightmapUV' # glTF stores TEXCOORD_1, not Blender layer names.
audit=runpy.run_path(str(ROOT/'scripts/dev/room1_uv2_audit.py'))['audit_uv2_layout'](receivers)
assert audit['positive_area_overlap_count']==audit['uv_degenerate_triangle_count']==audit['out_of_atlas_vertex_count']==0
max_chart_error=0
for ob in receivers:
 uv=np.array([v.uv[:] for v in ob.data.uv_layers[1].data])*4096
 actual=np.r_[uv.min(axis=0),uv.max(axis=0)]
 max_chart_error=max(max_chart_error,float(np.max(abs(actual-layout['receivers'][ob.name]['chart']))))
assert max_chart_error<.01
hdr={}
for name in ['strip_irradiance.exr','strip_irradiance_denoised.exr','source_strip_irradiance.exr','source_strip_irradiance_denoised.exr']:
 im=bpy.data.images.load(str(OUT/name),check_existing=False);p=np.empty(len(im.pixels),np.float32);im.pixels.foreach_get(p);p=p.reshape(-1,4)[:,:3]
 hdr[name]={'size':list(im.size),'finite':bool(np.isfinite(p).all()),'minimum':float(p.min()),'maximum':float(p.max()),'nonzero_components':int(np.count_nonzero(p))}
 assert hdr[name]['finite'] and hdr[name]['minimum']>=0 and hdr[name]['maximum']>0
 bpy.data.images.remove(im)
rects=json.loads((EXP/'continuous_uv_validation.json').read_text())['group_rectangles']
minimum=math.inf
for i,a in enumerate(rects):
 for b in rects[i+1:]:
  dx=max(a[0]-b[2],b[0]-a[2],0);dy=max(a[1]-b[3],b[1]-a[3],0)
  minimum=min(minimum,math.hypot(dx,dy))
assert minimum>=16-.001
report={'exported_glb_uv_audit':audit,'manifest_hashes':hashes,'max_exported_chart_error_px':max_chart_error,'measured_chart_rectangle_gap_px':minimum,'remaining_after_two_4px_dilations':minimum-8,'hdr':hdr,'result':'PASS'}
(EXP/'bake_validation.json').write_text(json.dumps(report,indent=2));print('F4_BAKE_AUDIT_PASS',flush=True)
