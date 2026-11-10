"""Optional packed Blender viewing materials; GLBs use external Godot textures."""
from pathlib import Path
import bpy

def bind(texture_root):
    root=Path(texture_root)
    alias={'M06':'M06-01','M06-BASE':'M06-02'}
    for mat in bpy.data.materials:
        name=alias.get(mat.name,mat.name)
        png=root/(name+'.png')
        if not png.is_file() or not mat.use_nodes:continue
        nd=mat.node_tree.nodes;bs=next((n for n in nd if n.type=='BSDF_PRINCIPLED'),None)
        if bs is None:continue
        tex=nd.new('ShaderNodeTexImage');tex.interpolation='Closest';tex.extension='CLIP' if name.startswith('FACE_') or name=='M06-R' else 'REPEAT'
        tex.image=bpy.data.images.load(str(png),check_existing=True);tex.image.pack()
        mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
