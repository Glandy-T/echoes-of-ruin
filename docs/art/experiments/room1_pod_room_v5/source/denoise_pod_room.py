"""Denoise linear irradiance only, following Room 1's existing HDR pipeline."""
from pathlib import Path
import bpy,json,shutil,hashlib,numpy as np
HERE=Path(__file__).resolve().parents[1];REPO=HERE.parents[3]
OUT=REPO/'assets/art/room1_pod_room_v5'
rows=[]
prior_path=HERE/'source/denoise_validation.json'
prior={r['pose']:r for r in json.loads(prior_path.read_text())['poses']} if prior_path.exists() else {}
for pose in ['closed','open']:
    raw=OUT/f'{pose}_raw_irradiance.exr';target=OUT/f'{pose}_irradiance.exr'
    current_hash=hashlib.sha256(target.read_bytes()).hexdigest()
    if not raw.exists() or current_hash!=prior.get(pose,{}).get('final_sha256'):shutil.copyfile(target,raw)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE'
    camera_data=bpy.data.cameras.new('CompositorCamera');camera=bpy.data.objects.new('CompositorCamera',camera_data);scene.collection.objects.link(camera);scene.camera=camera
    scene.render.resolution_x=16;scene.render.resolution_y=16;scene.render.resolution_percentage=100
    group=bpy.data.node_groups.new('PodRoomLinearDenoise','CompositorNodeTree');scene.compositing_node_group=group
    source=group.nodes.new('CompositorNodeImage');source.image=bpy.data.images.load(str(raw));source.image.colorspace_settings.name='Non-Color'
    denoise=group.nodes.new('CompositorNodeDenoise');group.links.new(source.outputs['Image'],denoise.inputs['Image'])
    output=group.nodes.new('CompositorNodeOutputFile');output.directory=str(OUT);output.file_name=pose+'_denoised'
    output.file_output_items.new('RGBA','Irradiance');output.format.media_type='IMAGE';output.format.file_format='OPEN_EXR'
    output.format.color_mode='RGB';output.format.color_depth='32';output.format.exr_codec='ZIP';output.save_as_render=False
    group.links.new(denoise.outputs['Image'],output.inputs[0]);bpy.ops.render.render()
    generated=OUT/f'{pose}_denoisedIrradiance.exr';assert generated.is_file();generated.replace(target)
    image=bpy.data.images.load(str(target),check_existing=False);assert tuple(image.size)==(2048,2048)
    values=np.empty(len(image.pixels),dtype=np.float32);image.pixels.foreach_get(values);assert np.isfinite(values).all()
    rows.append({'pose':pose,'final_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'size':list(image.size),'finite':True,'rgb_range':[float(values.reshape(-1,4)[:,:3].min()),float(values.reshape(-1,4)[:,:3].max())]})
    blend=HERE/f'room1_pod_{pose}_room_v5_packed.blend';bpy.ops.wm.open_mainfile(filepath=str(blend))
    image=bpy.data.images[f'P12V4_{pose}_irradiance']
    if image.packed_file:image.unpack(method='REMOVE')
    image.filepath=str(target);image.reload();image.pack()
    assert hashlib.sha256(bytes(image.packed_file.data)).hexdigest()==rows[-1]['final_sha256']
    bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True,check_existing=False)
(HERE/'source/denoise_validation.json').write_text(json.dumps({'scope':'Denoised irradiance, not pixel color maps. Same compositor method as original r9; linear 32-bit ZIP EXR. Raw retained locally, excluded from delivery.','poses':rows},indent=2),encoding='utf8')
print('POD_ROOM_DENOISE_COMPLETE',flush=True)
