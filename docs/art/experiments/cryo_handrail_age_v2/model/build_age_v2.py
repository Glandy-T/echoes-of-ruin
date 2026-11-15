"""Package C-stair contact ageing without changing the approved v1 geometry.

This runs in Blender background mode.  It samples the approved v1 material
maps into one UV0 atlas per affected mesh, preserving the exact UV scale
(80 px/m), and overlays only fixed semantic contact masks from the three
PixelLab source maps.  It does not synthesize marks, noise, scratches, or
stains.  The alpha map is retained beside the flattened map so Godot can make
an identical base/composite A/B comparison while the GLB stays portable.
"""
from pathlib import Path
from array import array
import hashlib
import json
import math

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
EXPERIMENT = HERE.parent
ROOT = EXPERIMENT.parents[3]
SOURCE = ROOT / "docs/art/experiments/cryo_handrail_full_v1/model/handrail_full_v1.blend"
RAW = EXPERIMENT / "source/raw"
OUT = ROOT / "assets/art/cryo_handrail_age_v2"
TEX = OUT / "textures"
BLEND_OUT = HERE / "handrail_age_v2.blend"
GLB_OUT = OUT / "cryo_handrail_age_v2.glb"
MANIFEST = EXPERIMENT / "model_manifest.json"
PLACEMENT = EXPERIMENT / "source/placement_manifest.json"
MATERIAL_MAP = OUT / "material_map.json"
PX = 80
PAD = 2
MULTIPLIER = {
    "M01_STAIR": (1, 1, 1), "M03_STAIR": (180/255, 186/255, 192/255),
    "M01": (1, 1, 1), "C_BODY": (1, 1, 1), "C_SLOT": (152/255, 164/255, 160/255),
}
ROUGHNESS = {"C_BODY": .90, "C_SLOT": .92, "M01_STAIR": .95, "M03_STAIR": .95, "M01": .95}
for directory in (OUT, TEX):
    directory.mkdir(parents=True, exist_ok=True)
for required in ("mineral_edge.png", "groove.png", "floor_edge.png"):
    if not (RAW / required).is_file():
        raise RuntimeError(f"Missing approved PixelLab source: {RAW / required}")

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0

def geometry_hash(obj):
    h = hashlib.sha256()
    for v in obj.data.vertices:
        h.update(bytes(memoryview(array('d', v.co[:]))))
    for p in obj.data.polygons:
        h.update(bytes(memoryview(array('I', p.vertices[:]))))
    return h.hexdigest()

before_hashes = {o.name: geometry_hash(o) for o in bpy.data.objects if o.type == "MESH"}

def image_pixels(image):
    image.colorspace_settings.name = "sRGB"
    w, h = image.size[:]
    return w, h, list(image.pixels[:])

def load(path, name):
    image = bpy.data.images.load(str(path), check_existing=False)
    image.name = name
    return image_pixels(image)

raw = {
    "mineral": load(RAW / "mineral_edge.png", "AGE_RAW_MINERAL"),
    "groove": load(RAW / "groove.png", "AGE_RAW_GROOVE"),
    "floor": load(RAW / "floor_edge.png", "AGE_RAW_FLOOR"),
}

def source_for(material_name):
    # The baseline Blend carries the approved maps as packed image nodes.
    material = bpy.data.materials[material_name]
    node = next((n for n in material.node_tree.nodes if n.type == "TEX_IMAGE"), None)
    if node is None or node.image is None:
        raise RuntimeError(f"No approved image texture in {material_name}")
    return image_pixels(node.image)

def tinted(pixel, material_name):
    factor = MULTIPLIER[material_name]
    return [pixel[0]*factor[0], pixel[1]*factor[1], pixel[2]*factor[2], pixel[3]]

def rgba_at(data, w, h, u, v):
    # UV and source image coordinates are both bottom-origin in bpy pixels.
    x = int(math.floor((u - math.floor(u)) * w)) % w
    y = int(math.floor((v - math.floor(v)) * h)) % h
    i = (y * w + x) * 4
    return data[i:i + 4]

def tri_area(a, b, c):
    return (b.x-a.x)*(c.y-a.y) - (b.y-a.y)*(c.x-a.x)

SECTION = [(0.000, -.200), (.020, -.220), (.080, -.220), (.080, 1.100), (.020, 1.100), (.000, 1.080), (.000, 1.040), (.020, 1.020), (.067, 1.020), (.067, .900), (.010, .900), (.000, .890), (.000, .878), (.016, .866), (.050, .866), (.050, .820), (.000, .820)]
RISE = 1.90 / 12

def stepped_floor(name, p):
    """Actual discrete tread/platform level, never the visual slope."""
    if "Lower_Entry" in name: return 0.0
    if "Lower_Run" in name:
        return max(RISE, min(12*RISE, (math.floor((p.x + 1.65) / .30) + 1) * RISE))
    if "Upper_Run" in name:
        return 1.90 + max(RISE, min(12*RISE, (math.floor((1.65 - p.x) / .30) + 1) * RISE))
    if "Upper_Floor" in name: return 3.80
    if "Turn" in name: return 1.90
    return 0.0

def grip_base(name, p):
    """The slot follows the continuous rail slope, unlike tread contacts."""
    if "Lower_Run" in name: return (p.x + 1.65) * 1.90 / 3.30
    if "Upper_Run" in name: return 3.80 - (p.x + 1.65) * 1.90 / 3.30
    if "Upper_Floor" in name: return 3.80
    if "Turn" in name: return 1.90
    return 0.0

def semantic_strength(name, poly_index, p, normal, minp, maxp, section_local=None):
    """Return (source kind, alpha 0..1, longitudinal phase coordinate).

    Every branch is a structural contact zone.  Broad faces deliberately return
    zero; no procedural shape is introduced here.
    """
    if name.startswith("C_Guard"):
        # Only the two physical groove-contact faces receive groove art.
        # strip 8 is the vertical back (height above its .90m shelf); strip 9
        # is the horizontal shelf (distance from .067m rear edge).  The cap,
        # broad front and bend shaft remain clean unless they meet a floor.
        strip = ((poly_index - 1) // 2) % 17
        if section_local is not None and strip == 8:
            return "groove", .72, p.x + p.y * .37, max(0.0, section_local.y - .900)
        if section_local is not None and strip == 9:
            return "groove", .72, p.x + p.y * .37, max(0.0, .067 - section_local.x)
        return "groove", 0.0, 0.0, 1.0
    if "Grip" in name:
        opening_low = grip_base(name, p) + .90
        if "Back" in name or "GripBack" in name:
            return "groove", .60, p.x + p.y * .53, max(0.0, p.z - opening_low)
        if "LowerLip" in name or "GripLowerLip" in name:
            # Distance from the physical recess back: y=-.965 / 2.965, or
            # x=3.515 at the turn wall.  Upper lips receive no sediment.
            if name.startswith("Wall_Turn_") and "Return" not in name:
                d = 3.515 - p.x
            elif "Upper" in name:
                d = 2.965 - p.y
            else:
                d = p.y - (-.965)
            return "groove", .52, p.x + p.y * .53, max(0.0, d)
        return "groove", 0.0, 0.0, 1.0
    if name.endswith("_Base") or name == "Wall_Turn_Lower":
        d = p.z - stepped_floor(name, p)
        return "mineral", .58 if 0 <= d <= .20 else 0.0, p.x + p.y * .61, max(0.0, d)
    if name == "Lower_ClosedFlight":
        d = abs(p.y + .90)
    elif name == "Upper_ClosedFlight":
        d = abs(p.y - 2.90)
    elif name == "EntryLanding":
        d = abs(p.y + .90)
    elif name == "FloorLanding":
        d = abs(p.y - 2.90)
    elif name == "TurnLanding":
        d = min(abs(p.x - 3.45), abs(p.y + .90), abs(p.y - 2.90))
    else:
        return "floor", 0.0, 0.0, 1.0
    if normal.z < .72 or d > .19:
        return "floor", 0.0, 0.0, 1.0
    # The only fade is distance from a real wall contact (19cm max), not a
    # synthetic grime contour.  The art pixels remain entirely PixelLab's.
    return "floor", .68 * (1.0 - d / .19), p.x + p.y * .47, d

def target_objects():
    result = []
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.data.materials:
            continue
        material = obj.data.materials[0].name
        if obj.name.startswith("C_Guard"):
            result.append((obj, material, "groove"))
        elif "Grip" in obj.name and material == "C_SLOT":
            result.append((obj, material, "groove"))
        elif (obj.name.endswith("_Base") or obj.name == "Wall_Turn_Lower") and material == "M01_STAIR":
            result.append((obj, material, "mineral"))
        elif obj.name in {"Lower_ClosedFlight", "Upper_ClosedFlight", "EntryLanding", "TurnLanding", "FloorLanding"}:
            result.append((obj, material, "floor"))
    return result

def write_image(name, width, height, pixels, path):
    old = bpy.data.images.get(name)
    if old: bpy.data.images.remove(old)
    image = bpy.data.images.new(name, width, height, alpha=True, float_buffer=False)
    image.pixels.foreach_set(array('f', pixels))
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    return image

def package_object(obj, material_name, default_kind):
    base_w, base_h, base_pixels = source_for(material_name)
    mesh = obj.data
    uv = mesh.uv_layers.active
    if uv is None:
        raise RuntimeError(f"{obj.name} has no UV0")
    # v1's metric projection intentionally lets opposite faces repeat the
    # same tile.  That is valid for a single base map, but not for a contact
    # placement map.  Pack only existing continuous charts independently:
    # C retains each complete longitudinal strip plus two end caps; all other
    # closed/prismatic pieces retain each complete planar polygon chart.
    def chart_id(poly_index):
        if obj.name.startswith("C_Guard"):
            if poly_index == 0: return "cap_start"
            if poly_index == len(mesh.polygons)-1: return "cap_end"
            return "strip_%02d" % (((poly_index-1)//2) % 17)
        return "face_%04d" % poly_index
    charts = {}
    for poly in mesh.polygons:
        group = charts.setdefault(chart_id(poly.index), {"loops": [], "polys": []})
        group["polys"].append(poly.index)
        group["loops"].extend(poly.loop_indices)
    for group in charts.values():
        values = [uv.data[l].uv[:] for l in group["loops"]]
        group["minx"] = min(v[0] for v in values)*base_w
        group["miny"] = min(v[1] for v in values)*base_h
        group["w"] = max(1, int(math.ceil(max(v[0] for v in values)*base_w-group["minx"])))
        group["h"] = max(1, int(math.ceil(max(v[1] for v in values)*base_h-group["miny"])))
    # Deterministic shelf packing; a chart's local scale is untouched.
    x=y=PAD; row_h=0; limit=2048
    for key, group in sorted(charts.items(), key=lambda kv:(-kv[1]["h"], kv[0])):
        if x + group["w"] + PAD > limit:
            x=PAD; y += row_h + PAD; row_h=0
        group["x"], group["y"] = x, y
        # At least 2*PAD+1 between content bounds: dilation cannot borrow
        # from a neighbouring UV island even at a sharp chart corner.
        x += group["w"] + PAD*2 + 1; row_h=max(row_h, group["h"])
    width=max(8, max(g["x"]+g["w"]+PAD for g in charts.values()))
    height=max(8, max(g["y"]+g["h"]+PAD for g in charts.values()))
    # Full transparent age layer, base/composite only where the existing UV
    # charts are.  Unused atlas pixels cannot affect the mesh.
    base = [0.0] * (width * height * 4)
    age = [0.0] * (width * height * 4)
    composite = [0.0] * (width * height * 4)
    valid = bytearray(width * height)
    mesh.calc_loop_triangles()
    points = [obj.matrix_world @ v.co for v in mesh.vertices]
    minp = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    maxp = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    seed = int(hashlib.sha256(obj.name.encode()).hexdigest()[:8], 16) % 256
    for tri in mesh.loop_triangles:
        loops = tri.loops
        old_uv = [Vector(uv.data[l].uv[:]) for l in loops]
        group = charts[chart_id(tri.polygon_index)]
        xy = [Vector((u.x*base_w-group["minx"]+group["x"], u.y*base_h-group["miny"]+group["y"])) for u in old_uv]
        denom = tri_area(xy[0], xy[1], xy[2])
        if abs(denom) < 1e-8: continue
        min_x, max_x = max(0, math.floor(min(p.x for p in xy))), min(width-1, math.ceil(max(p.x for p in xy)))
        min_y, max_y = max(0, math.floor(min(p.y for p in xy))), min(height-1, math.ceil(max(p.y for p in xy)))
        wp = [points[mesh.loops[l].vertex_index] for l in loops]
        normal = (wp[1]-wp[0]).cross(wp[2]-wp[0]).normalized()
        poly_idx = tri.polygon_index
        # The final cap is tagged as -1 for concise semantic logic.
        poly_tag = -1 if poly_idx == len(mesh.polygons)-1 else poly_idx
        for y in range(min_y, max_y+1):
            for x in range(min_x, max_x+1):
                q = Vector((x+.5, y+.5))
                a = tri_area(q, xy[1], xy[2]) / denom
                b = tri_area(xy[0], q, xy[2]) / denom
                c = 1.0-a-b
                if a < -1e-5 or b < -1e-5 or c < -1e-5: continue
                ou = old_uv[0]*a + old_uv[1]*b + old_uv[2]*c
                pos = wp[0]*a + wp[1]*b + wp[2]*c
                i = (y*width+x)*4
                valid[y*width+x] = 1
                bpx = tinted(rgba_at(base_pixels, base_w, base_h, ou.x, ou.y), material_name)
                base[i:i+4] = bpx
                local = None
                if obj.name.startswith("C_Guard"):
                    local_points = [Vector(SECTION[mesh.loops[l].vertex_index % 17]) for l in loops]
                    local = local_points[0]*a + local_points[1]*b + local_points[2]*c
                kind, strength, phase, distance_m = semantic_strength(obj.name, poly_tag, pos, normal, minp, maxp, local)
                if strength > 0.0:
                    rw, rh, rp = raw[kind]
                    # Read only the PixelLab-approved bottom band.  Horizontal
                    # phase changes placement, never generates a new pattern.
                    ru = ((phase * PX) + seed) / rw
                    # PixelLab's age exists at source y=0..31.  This maps
                    # physical contact distance, so y=0 is the real contact;
                    # alpha controls blend only and never chooses a row.
                    rv = min(31, max(0, int(distance_m * PX))) / rh
                    apx = tinted(rgba_at(rp, rw, rh, ru, rv), material_name)
                    alpha = max(0.0, min(.78, strength))
                    age[i:i+4] = [apx[0], apx[1], apx[2], alpha]
                    composite[i:i+4] = [bpx[j]*(1-alpha)+apx[j]*alpha for j in range(3)] + [1.0]
                else:
                    composite[i:i+4] = bpx
    # Exact raster-island extrusion: two rounds of 4-neighbour dilation copy
    # the nearest valid texel, including sloped/triangular chart boundaries.
    # Islands have a 2*PAD+1 content gap, so propagation cannot cross charts.
    extruded_pixels = 0
    for _ in range(PAD):
        pending=[]
        for yy in range(height):
            for xx in range(width):
                index=yy*width+xx
                if valid[index]: continue
                neighbour=next((ny*width+nx for nx,ny in ((xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)) if 0<=nx<width and 0<=ny<height and valid[ny*width+nx]), None)
                if neighbour is not None: pending.append((index,neighbour))
        for dst_index,src_index in pending:
            dst=dst_index*4; src=src_index*4
            base[dst:dst+4]=base[src:src+4]; age[dst:dst+4]=age[src:src+4]; composite[dst:dst+4]=composite[src:src+4]
            valid[dst_index]=1
        extruded_pixels += len(pending)
    stem = obj.name.lower()
    paths = {
        "base": TEX / f"{stem}_atlas_base.png",
        "age": TEX / f"{stem}_atlas_age_rgba.png",
        "composite": TEX / f"{stem}_atlas_composite.png",
    }
    images = {key: write_image(f"AGE_{obj.name}_{key.upper()}", width, height, data, paths[key])
              for key, data in (("base", base), ("age", age), ("composite", composite))}
    # Preserve a single continuous chart: translation/reframing only, never
    # per-triangle splitting or UV scaling.
    for p in mesh.polygons:
        group = charts[chart_id(p.index)]
        for loop in p.loop_indices:
            old = uv.data[loop].uv.copy()
            uv.data[loop].uv = (old.x*base_w-group["minx"]+group["x"])/width, (old.y*base_h-group["miny"]+group["y"])/height
    aged_name = "AGE_" + obj.name
    oldmat = obj.data.materials[0]
    aged = bpy.data.materials.get(aged_name) or bpy.data.materials.new(aged_name)
    aged.use_nodes = True
    nodes, links = aged.node_tree.nodes, aged.node_tree.links
    nodes.clear()
    texnode = nodes.new("ShaderNodeTexImage"); texnode.image = images["composite"]; texnode.interpolation = "Closest"
    bsdf = nodes.new("ShaderNodeBsdfPrincipled"); bsdf.inputs["Roughness"].default_value = ROUGHNESS[material_name]; bsdf.inputs["Metallic"].default_value = 0.0; bsdf.inputs["Specular IOR Level"].default_value = .12
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(texnode.outputs["Color"], bsdf.inputs["Base Color"]); links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    obj.data.materials[0] = aged
    return {"object": obj.name, "material": aged_name, "base_material": material_name, "source_kind": default_kind,
            "atlas_px": [width, height], "uv_translation_metric": {"packing": "existing continuous C strip/cap or complete planar polygon chart translated without scale", "chart_count": len(charts), "padding_px": PAD, "density_px_per_m": PX},
            "extrusion": {"nearest_valid_texel_dilation_px": PAD, "content_gap_px": 2*PAD+1, "written_padding_pixels": extruded_pixels},
            "textures": {k: str(v.relative_to(ROOT)).replace('\\', '/') for k,v in paths.items()}}

placements = [package_object(*target) for target in target_objects()]

bpy.ops.object.select_all(action="DESELECT")
for obj in bpy.data.objects:
    if obj.type == "MESH": obj.select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects.get("C_Guard_LowerAndReturn")
bpy.ops.export_scene.gltf(filepath=str(GLB_OUT), export_format="GLB", use_selection=True, export_texcoords=True, export_materials="EXPORT", export_image_format="AUTO")
# Keep the editable file portable across the home and school checkouts.
for image in bpy.data.images:
    if image.source == "FILE" and not image.packed_file:
        _ = image.pixels[0]  # Material images can be lazily loaded on reopen.
        image.pack()
    if image.filepath and not image.filepath.startswith("//"):
        image.filepath = bpy.path.relpath(image.filepath, start=str(BLEND_OUT.parent))
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_OUT))

after_hashes = {o.name: geometry_hash(o) for o in bpy.data.objects if o.type == "MESH"}
if before_hashes != after_hashes:
    raise RuntimeError("Geometry hash changed: UV/material-only packaging violated")
placement_doc = {"method": "fixed semantic contact masks + PixelLab lower-edge samples only; no procedural ageing marks", "entries": placements}
PLACEMENT.write_text(json.dumps(placement_doc, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
MATERIAL_MAP.write_text(json.dumps({entry["material"]: {"base": "textures/" + entry["textures"]["base"].split("textures/",1)[1], "composite": "textures/" + entry["textures"]["composite"].split("textures/",1)[1]} for entry in placements}, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
manifest = {"baseline": str(SOURCE.relative_to(ROOT)).replace('\\','/'), "geometry_hash_before_after_equal": True,
            "geometry_sha256": before_hashes, "target_density_px_per_m": PX, "glb": str(GLB_OUT.relative_to(ROOT)).replace('\\','/'),
            "blend": str(BLEND_OUT.relative_to(ROOT)).replace('\\','/'), "placement_manifest": str(PLACEMENT.relative_to(ROOT)).replace('\\','/'),
            "texture_policy": "base, alpha and flattened composite generated only from v1 base maps plus approved PixelLab images; masks express named structural contact zones", "entries": placements}
MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
print(json.dumps({"aged_objects": len(placements), "glb": str(GLB_OUT)}, ensure_ascii=False))
