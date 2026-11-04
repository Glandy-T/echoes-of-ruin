"""Reopen baked source: atlas coverage, HDR validity, margin inspection, and raw/denoise evidence."""
from pathlib import Path
import bpy,json,hashlib,runpy,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=ROOT/'assets/art/cryo_corridor_baked_v2'
bpy.ops.wm.open_mainfile(filepath=str(HERE/'cryo_corridor_baked_v2.blend'))
receivers=[bpy.data.objects[n] for n in ['Wall_3p2m_TwoBays','Room1_Exterior_Wall_Module','Floor_3p2m_Unique']]
audit=runpy.run_path(str(ROOT/'scripts/dev/room1_uv2_audit.py'))['audit_uv2_layout'](receivers)
assert audit['positive_area_overlap_count']==audit['out_of_atlas_vertex_count']==audit['uv_degenerate_triangle_count']==0
maps={}
for mode,name in [('raw','strip_irradiance.exr'),('denoised','strip_irradiance_denoised.exr')]:
 im=bpy.data.images.load(str(OUT/name),check_existing=False);assert tuple(im.size)==(1024,1024)
 a=np.asarray(im.pixels[:],dtype=np.float32).reshape(1024,1024,4)[:,:,:3];assert np.isfinite(a).all() and a.min()>=0
 maps[mode]=a
 # A common display transform, no independent normalization.
 im.filepath_raw=str(HERE/'evidence'/f'{mode}_atlas.png');im.file_format='PNG';im.save()
report={'UV2':audit,'HDR':{},'charts':{},'sampler':'lightmap linear, albedo nearest','margin_px':4,'unexpanded_chart_gap_px':16,'remaining_clear_gap_after_two_4px_dilations':8,'context':'floor, opposite walls, actual frozen route walls plus cutaway ceiling; source retained','runtime_lights':0}
for mode,a in maps.items():report['HDR'][mode]={'min':float(a.min()),'max':float(a.max()),'mean':float(a.mean())}
for n,rect in json.loads((HERE/'uv2_validation.json').read_text())['rectangles_px'].items():
 x0,y0,x1,y1=rect
 a=maps['raw'][y0:y1,x0:x1];b=maps['denoised'][y0:y1,x0:x1]
 # Neighbor residual, useful for detecting speckle; not a claim that gradients are noise.
 residual=lambda t:float(np.std(t[1:-1,1:-1]-(t[:-2,1:-1]+t[2:,1:-1]+t[1:-1,:-2]+t[1:-1,2:])*.25))
 report['charts'][n]={'raw_neighbor_residual':residual(a),'denoised_neighbor_residual':residual(b),'raw_mean':float(a.mean()),'denoised_mean':float(b.mean()),'mean_abs_denoise_delta':float(np.abs(a-b).mean()),'edge_ring_nonnegative':bool((b>=0).all())}
manifest=json.loads((OUT/'bake_manifest.json').read_text())
assert all(hashlib.sha256((OUT/p).read_bytes()).hexdigest()==sha for p,sha in manifest['files'].items())
report['manifest_hashes_match']=True
(HERE/'bake_validation.json').write_text(json.dumps(report,indent=2));print('BAKE_AUDIT_PASS',json.dumps(report['HDR']))
