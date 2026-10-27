"""Read the downloaded Collada geometry without executing any source scripts."""
import bpy, json, math, xml.etree.ElementTree as ET
from pathlib import Path
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parent
DAE = ROOT / 'source/original_unpacked/model/model.dae'
NS = {'c':'http://www.collada.org/2005/11/COLLADASchema'}

def load_robe():
    tree = ET.parse(DAE).getroot()
    mesh = tree.find('c:library_geometries/c:geometry/c:mesh', NS)
    arrays = {}
    for source in mesh.findall('c:source', NS):
        raw = [float(x) for x in source.find('c:float_array',NS).text.split()]
        stride = int(source.find('c:technique_common/c:accessor',NS).get('stride'))
        arrays[source.get('id')] = [raw[i:i+stride] for i in range(0,len(raw),stride)]
    vertices = mesh.find('c:vertices',NS)
    posref = vertices.find("c:input[@semantic='POSITION']",NS).get('source')[1:]
    rawpos = arrays[posref]
    poly = mesh.find('c:polylist',NS)
    inputs = {n.get('semantic'):(int(n.get('offset')),n.get('source')[1:]) for n in poly.findall('c:input',NS)}
    stride = 1+max(v[0] for v in inputs.values())
    p = [int(x) for x in poly.find('c:p',NS).text.split()]
    counts = [int(x) for x in poly.find('c:vcount',NS).text.split()]
    faces, uvfaces = [], []
    at = 0
    for count in counts:
        face,uvface=[],[]
        for i in range(count):
            idx=p[at:at+stride]; at+=stride
            face.append(idx[inputs['VERTEX'][0]])
            uvface.append(arrays[inputs['TEXCOORD'][1]][idx[inputs['TEXCOORD'][0]]][:2])
        faces.append(face); uvfaces.append(uvface)
    matrix_values=[float(x) for x in tree.find('c:library_visual_scenes/c:visual_scene/c:node/c:matrix',NS).text.split()]
    # This Assimp file serializes the displayed node matrix in row order.
    # Together with Y_UP conversion it restores its authored upright Z axis.
    node=Matrix([matrix_values[i:i+4] for i in range(0,16,4)])
    unit=float(tree.find('c:asset/c:unit',NS).get('meter'))
    transform=Matrix.Rotation(math.pi/2,4,'X') @ Matrix.Scale(unit,4) @ node
    coords=[transform @ Vector(p) for p in rawpos]
    data=bpy.data.meshes.new('Robe_Source_DAE_Mesh'); data.from_pydata(coords,[],faces); data.update()
    obj=bpy.data.objects.new('Robe_Source_Original',data); bpy.context.collection.objects.link(obj)
    uv=data.uv_layers.new(name='UV_Source_Preserved')
    for polygon,values in zip(data.polygons,uvfaces):
        for li,value in zip(polygon.loop_indices,values): uv.data[li].uv=value
    material=bpy.data.materials.new('Source_Albedo'); material.use_nodes=True
    nodes=material.node_tree.nodes
    image=nodes.new('ShaderNodeTexImage'); image.image=bpy.data.images.load(str(DAE.parent/'textures/Robe_albedo.jpg'))
    material.node_tree.links.new(image.outputs['Color'],nodes.get('Principled BSDF').inputs['Base Color'])
    nodes.get('Principled BSDF').inputs['Roughness'].default_value=.85
    data.materials.append(material)
    adjacency=[[] for _ in data.vertices]
    for edge in data.edges:
        a,b=edge.vertices; adjacency[a].append(b); adjacency[b].append(a)
    remaining=set(range(len(data.vertices))); components=[]
    while remaining:
        start=remaining.pop(); seen={start}; stack=[start]
        while stack:
            for v in adjacency[stack.pop()]:
                if v in remaining: remaining.remove(v); seen.add(v); stack.append(v)
        components.append(sorted(seen))
    components.sort(key=len,reverse=True)
    obj['source_url']='https://sketchfab.com/3d-models/robe-free-fcc16fda59e84ee29ea7e920d556d166'
    obj['source_author']='wolfgar74'; obj['license']='CC BY 4.0'
    data.calc_loop_triangles()
    def bounds(indices):
        return [[min(data.vertices[i].co[k] for i in indices) for k in range(3)], [max(data.vertices[i].co[k] for i in indices) for k in range(3)]]
    report={'source_unit':unit,'node_matrix_collada':matrix_values,'raw_bounds':[[min(p[k] for p in rawpos) for k in range(3)],[max(p[k] for p in rawpos) for k in range(3)]], 'vertices':len(data.vertices),'faces':len(data.polygons),'triangles':len(data.loop_triangles), 'polygon_sizes':sorted(set(counts)), 'bounds':bounds(range(len(data.vertices))), 'components':[{'index':i,'vertices':len(c),'bounds':bounds(c)} for i,c in enumerate(components)], 'component_vertex_indices':components}
    return obj,report

if __name__=='__main__':
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obj,report=load_robe()
    (ROOT/'source_audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'robe_source_inspected.blend'))
    report.pop('component_vertex_indices')
    print(json.dumps(report,indent=2))
