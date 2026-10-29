"""Reproducible Room 1 r19 static irradiance bake.

The scene is intentionally bake-only: r9 supplies the frozen shell UV2 and four
wall ribbons; all 160 v3 pod meshes are deleted and replaced by twenty exact v8
GLB poses using the Godot-exported transform/color-map manifest.  P12 has two
endpoint scenes (closed/open); the other nineteen pods stay closed in both.
"""
from pathlib import Path
import bpy, json, hashlib, os, runpy, time, numpy as np
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
ROOM = REPO / "docs/art/experiments/room1_floor_palette_r9/room1_floor_palette_r9_packed.blend"
POD_SOURCE = REPO / "docs/art/experiments/room1_pod_standard_v8/room1_pod_standard_v8_packed.blend"
POD_ASSET = REPO / "assets/art/cryopod_standard_v8"
DOOR_GLB = REPO / "assets/art/room1_integrated_door_v3/room1_integrated_door_v3.glb"
DOOR_PIXELS = REPO / "assets/art/room1_integrated_door_pixellab_v7/door_front.png"
LAYOUT_PATH = HERE / "layout_before.json"
OUT = REPO / "assets/art/room1_complete_r19/lighting"
BLEND_OUT = HERE.parent / "room1_complete_r19.blend"

SHELL_TEX = {
    "Bake_Shell_Floor_continuous_no_tile_seams": REPO / "assets/art/room1_floor_variants_r15/floor_with_leaks.png",
    "Bake_Shell_Wall_left": REPO / "assets/art/room1_wall_lamp_r13/wall_left.png",
    "Bake_Shell_Wall_right": REPO / "assets/art/room1_wall_lamp_r13/wall_right.png",
    "Bake_Shell_Wall_front": REPO / "assets/art/room1_wall_lamp_r13/wall_front.png",
    "Bake_Shell_Wall_rear_left": REPO / "assets/art/room1_wall_lamp_r13/wall_rear.png",
    "Bake_Shell_Wall_rear_right": REPO / "assets/art/room1_wall_lamp_r13/wall_rear.png",
    "Bake_Shell_Wall_rear_door_header": REPO / "assets/art/room1_wall_lamp_r13/wall_rear.png",
}
ROLE_FROM_MATERIAL = {
    "POD_V8_lid": "lid", "POD_V8_shell_side": "shell_side", "POD_V8_shell_end": "shell_end",
    "POD_V8_interior": "interior", "POD_V8_mattress": "mattress", "POD_V8_section": "section",
}
EXCLUDED = ("glass", "display", "tube_diffuser")
SHELL = ["Bake_Shell_Floor_continuous_no_tile_seams", "Bake_Shell_Roof_hidden_for_cutaway", "Bake_Shell_Wall_front", "Bake_Shell_Wall_left",
         "Bake_Shell_Wall_rear_door_header", "Bake_Shell_Wall_rear_left", "Bake_Shell_Wall_rear_right",
         "Bake_Shell_Wall_right"]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def image(path):
    path = Path(path)
    assert path.is_file(), path
    return bpy.data.images.load(str(path), check_existing=False)

def remove_v3():
    old = [o for o in bpy.data.objects if o.name.startswith("Bake_P") and "pod_v3" in o.name]
    assert len(old) == 160, f"expected 160 old v3 pod meshes, found {len(old)}"
    for obj in old:
        bpy.data.objects.remove(obj, do_unlink=True)

def set_image_nodes(mat, source, uv_name=None):
    if not mat or not mat.use_nodes:
        return
    for node in mat.node_tree.nodes:
        if node.type == "TEX_IMAGE":
            node.image = source
            if uv_name and not node.inputs["Vector"].is_linked:
                uv = mat.node_tree.nodes.new("ShaderNodeUVMap")
                uv.uv_map = uv_name
                mat.node_tree.links.new(uv.outputs["UV"], node.inputs["Vector"])

def update_shell_textures():
    for name, path in SHELL_TEX.items():
        obj = bpy.data.objects.get(name)
        assert obj, name
        for mat in obj.data.materials:
            set_image_nodes(mat, image(path))

def replace_placeholder_door():
    old = bpy.data.objects.get("Bake_Shell_MAIN_DOOR_PLACEHOLDER_NOT_APPROVED")
    assert old, "r9 door placeholder missing"
    bpy.data.objects.remove(old, do_unlink=True)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(DOOR_GLB))
    imported = [obj for obj in bpy.data.objects if obj not in before]
    assert imported, "v3 door GLB import produced no objects"
    roots = [obj for obj in imported if obj.parent not in imported]
    root = bpy.data.objects.new("R19_IntegratedDoorV3_Closed", None)
    bpy.context.collection.objects.link(root)
    # Authority is the Godot closed panel centre; Godot -> Blender = (x,-z,y).
    root.location = godot_to_blender((10.5, 1.2, -9.422501))
    for obj in roots:
        obj.parent = root
    for obj in imported:
        if obj.type != "MESH":
            continue
        obj.name = "R19_Door_" + obj.name
        for material in obj.data.materials:
            set_image_nodes(material, image(DOOR_PIXELS))
    return [obj for obj in imported if obj.type == "MESH"]

def godot_to_blender(origin):
    return Vector((float(origin[0]), -float(origin[2]), float(origin[1])))

def clear_stale_v8():
    # r9 may carry stale v8 datablocks from an earlier append.  Remove only
    # unused datablocks so the frozen loader can resolve its canonical names.
    for material in list(bpy.data.materials):
        if material.name.startswith("POD_V8_"):
            if material.users == 0:
                bpy.data.materials.remove(material)
            else:
                material.name = "R9_stale_" + material.name
def add_pod(entry, pose):
    frozen_path = REPO / "docs/art/experiments/room1_pod_standard_v8/source/frozen_glb_pose.py"
    # Blender can suffix appended material datablocks despite a clean r9 scene.
    # Preserve the loader's canonical GLB material lookup by normalizing only the
    # temporary Blender datablock suffix (POD_V8_glass.001 -> POD_V8_glass).
    frozen_source = frozen_path.read_text(encoding="utf-8").replace(
        "materials={m.name:m for m in dst.materials}",
        "materials={m.name.rsplit('.', 1)[0] if m.name.rsplit('.', 1)[-1].isdigit() else m.name:m for m in dst.materials}")
    scope = {"__file__": str(frozen_path), "__name__": "r19_frozen_pose"}
    exec(compile(frozen_source, str(frozen_path), "exec"), scope)
    helper = scope["load_frozen_pose"]
    pod_id = entry["id"]
    source = POD_ASSET / f"cryopod_standard_v8_{pose}.glb"
    anchor = godot_to_blender(entry["origin"])
    imported = helper(source, POD_SOURCE, anchor)
    # The first ten rows are Godot Y=180. Under Godot->Blender this is Z=180.
    yaw_pi = entry["basis_columns"][0][0] < 0.0
    if yaw_pi:
        pivot = Matrix.Translation(anchor) @ Matrix.Rotation(3.141592653589793, 4, "Z") @ Matrix.Translation(-anchor)
        for obj in imported:
            obj.matrix_world = pivot @ obj.matrix_world
    opaque = []
    bound_roles = set()
    for obj in imported:
        names = " ".join(m.name.lower() for m in obj.data.materials if m)
        obj.name = f"R19_{pod_id}_{obj.name.removeprefix('BakeV8_')}"
        if any(token in names for token in EXCLUDED):
            obj.hide_render = True
            continue
        for slot in obj.material_slots:
            if not slot.material:
                continue
            material_key = slot.material.name.rsplit(".", 1)[0] if slot.material.name.rsplit(".", 1)[-1].isdigit() else slot.material.name
            role = ROLE_FROM_MATERIAL.get(material_key)
            if not role:
                continue
            material = slot.material.copy()
            material.name = f"R19_{pod_id}_{role}"
            slot.material = material
            color_rel = entry["bake_color_maps"][role]
            set_image_nodes(material, image(REPO / color_rel), "UV_GODOT_0")
            bound_roles.add(role)
        opaque.append(obj)
    # Every v8 solid surface must use the exact Godot r16/numbered color map.
    expected_roles = {"lid", "shell_side", "shell_end", "interior", "mattress", "section"}
    assert expected_roles <= bound_roles, (pod_id, expected_roles - bound_roles)
    assert opaque, pod_id
    bpy.ops.object.select_all(action="DESELECT")
    for obj in opaque:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = opaque[0]
    bpy.ops.object.join()
    receiver = bpy.context.object
    receiver.name = f"R19_{pod_id}_{pose}_receiver"
    lm = receiver.data.uv_layers.get("LightmapUV")
    assert lm and len(receiver.data.uv_layers) >= 2, f"missing v8 UV2: {pod_id}"
    receiver.data.uv_layers.active = lm
    receiver["r19_pod_id"] = pod_id
    receiver["r19_pose"] = pose
    return receiver

def configure_cycles():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = int(os.environ.get("R19_SAMPLES", "1024"))
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.max_bounces = 3
    scene.cycles.diffuse_bounces = 2
    # Default is the shell-safe value.  Individual pod jobs override to 4px:
    # UV audit measured 11.92448px minimum island gap at 1k (2*4 + 2px
    # bilinear footprint = 10px), while shell uses 6px at 2k (14px <= 16.22897px).
    scene.render.bake.margin = 6
    scene.render.image_settings.file_format = "OPEN_EXR"
    scene.render.image_settings.color_depth = "32"
    scene.render.image_settings.exr_codec = "ZIP"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "OPTIX"; prefs.get_devices()
        devices = [d for d in prefs.devices if d.type == "OPTIX"]
        for d in prefs.devices: d.use = d.type == "OPTIX"
        if devices: scene.cycles.device = "GPU"
    except Exception as exc:
        print("R19_GPU_FALLBACK", repr(exc), flush=True)
    return scene

def attach_target(receiver, target):
    for material in receiver.data.materials:
        if not material or not material.use_nodes:
            continue
        node = material.node_tree.nodes.new("ShaderNodeTexImage")
        node.name = f"R19_BAKE_TARGET_{target.name}"
        node.image = target
        material.node_tree.nodes.active = node

def denoise_linear_hdr(raw, final, tag):
    """Blender-native OIDN compositor pass; preserves the raw EXR beside it."""
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"; scene.render.threads_mode = "FIXED"; scene.render.threads = 8
    scene.render.resolution_x = 16; scene.render.resolution_y = 16; scene.render.resolution_percentage = 100
    camera_data = bpy.data.cameras.new("R19_DenoiseCamera")
    camera = bpy.data.objects.new("R19_DenoiseCamera", camera_data); scene.collection.objects.link(camera); scene.camera = camera
    group = bpy.data.node_groups.new("R19_LinearHDRDenoise_" + tag, "CompositorNodeTree")
    scene.compositing_node_group = group
    source = group.nodes.new("CompositorNodeImage"); source.image = bpy.data.images.load(str(raw), check_existing=False)
    source.image.colorspace_settings.name = "Non-Color"
    denoise = group.nodes.new("CompositorNodeDenoise"); group.links.new(source.outputs["Image"], denoise.inputs["Image"])
    output = group.nodes.new("CompositorNodeOutputFile"); output.directory = str(OUT); output.file_name = tag + "_denoised"
    output.file_output_items.new("RGBA", "Irradiance")
    output.format.media_type = "IMAGE"; output.format.file_format = "OPEN_EXR"
    output.format.color_mode = "RGB"; output.format.color_depth = "32"; output.format.exr_codec = "ZIP"; output.save_as_render = False
    group.links.new(denoise.outputs["Image"], output.inputs[0]); bpy.ops.render.render()
    generated = OUT / f"{tag}_denoisedIrradiance.exr"
    assert generated.exists(), generated
    generated.replace(final)
    return "oidn_compositor"

def bake_receiver(receiver, output_name, size):
    output = OUT / f"{output_name}.exr"
    raw = OUT / f"{output_name}_raw.exr"
    if output.exists() and raw.exists() and os.environ.get("R19_REBAKE", "0") != "1":
        return {"name": output_name, "reused": True, "raw": str(raw), "final": str(output)}
    target = bpy.data.images.new(f"R19_{output_name}", width=size, height=size, alpha=False, float_buffer=True)
    configure_cycles()
    margin = 6 if output_name.startswith("room_") else 4
    bpy.context.scene.render.bake.margin = margin
    target.colorspace_settings.name = "Non-Color"
    attach_target(receiver, target)
    bpy.ops.object.select_all(action="DESELECT")
    receiver.select_set(True); bpy.context.view_layer.objects.active = receiver
    started = time.monotonic()
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, uv_layer="LightmapUV", use_clear=True, margin=margin)
    target.filepath_raw = str(raw); target.file_format = "OPEN_EXR"; target.save_render(str(raw), scene=bpy.context.scene)
    values = np.empty(len(target.pixels), dtype=np.float32); target.pixels.foreach_get(values)
    assert np.isfinite(values).all(), f"nonfinite lightmap {output_name}"
    # Native denoise is deliberately limited to HDR sample noise; no color/texture editing occurs here.
    denoise_mode = denoise_linear_hdr(raw, output, output_name)
    return {"name": output_name, "reused": False, "raw": str(raw), "final": str(output), "seconds": time.monotonic()-started,
            "size": size, "margin_px": margin, "denoise": denoise_mode, "rgb_range": [float(values.reshape(-1,4)[:,:3].min()), float(values.reshape(-1,4)[:,:3].max())]}

def shell_receiver():
    items = [bpy.data.objects.get(name) for name in SHELL]
    assert all(items), [name for name,obj in zip(SHELL,items) if not obj]
    items = [obj for obj in items if not obj.hide_render]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in items: obj.select_set(True)
    bpy.context.view_layer.objects.active = items[0]
    bpy.ops.object.join()
    receiver = bpy.context.object; receiver.name = "R19_shell_receiver"
    lm = receiver.data.uv_layers.get("LightmapUV")
    assert lm and len(receiver.data.uv_layers) >= 2
    receiver.data.uv_layers.active = lm
    return receiver

def shell_uv_hash():
    # Hash only geometry mapping data used at runtime; materials are separately recorded.
    rows = []
    for name in SHELL:
        obj = bpy.data.objects.get(name)
        if not obj: continue
        mesh = obj.data; layer = mesh.uv_layers.get("LightmapUV")
        rows.append({"name":name, "verts":[tuple(round(v,6) for v in x.co) for x in mesh.vertices],
                     "uv2":[tuple(round(v,6) for v in x.uv) for x in layer.data] if layer else None,
                     "polys":[tuple(p.vertices) for p in mesh.polygons]})
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(), rows

def build_endpoint(p12_pose, save_blend=False):
    bpy.ops.wm.open_mainfile(filepath=str(ROOM))
    remove_v3(); clear_stale_v8(); update_shell_textures(); replace_placeholder_door()
    layout = json.loads(LAYOUT_PATH.read_text(encoding="utf-8"))
    receivers = {}
    for entry in layout["pods"]:
        pose = p12_pose if entry["id"] == "P12" else "closed"
        receivers[entry["id"]] = add_pod(entry, pose)
    assert len(receivers) == 20
    assert not any("pod_v3" in obj.name for obj in bpy.data.objects)
    scene = configure_cycles()
    mapping_hash, mapping_rows = shell_uv_hash()
    shell = shell_receiver()
    if save_blend:
        scene["r19_endpoint"] = p12_pose
        scene["r19_lightmap_contract"] = "P12 closed/open endpoints; P01-P11 and P13-P20 remain closed; runtime interpolates only endpoint maps."
        bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_OUT), compress=True, check_existing=False)
    return receivers, shell, scene, mapping_hash, mapping_rows

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    requested = [x.strip() for x in os.environ.get("R19_ENDPOINTS", "closed,open").split(",") if x.strip()]
    only = {item.strip() for item in os.environ.get("R19_ONLY", "").split(",") if item.strip()}
    assert set(requested) <= {"closed", "open"}
    report = {"format":"room1-r19-static-irradiance-v1", "samples":int(os.environ.get("R19_SAMPLES", "1024")),
              "pod_resolution":1024, "shell_resolution":2048, "endpoints":{}, "inputs":{}}
    for path in [ROOM, POD_SOURCE, POD_ASSET/"cryopod_standard_v8_closed.glb", POD_ASSET/"cryopod_standard_v8_open.glb", DOOR_GLB, DOOR_PIXELS, LAYOUT_PATH]:
        report["inputs"][str(path.relative_to(REPO))] = sha(path)
    for endpoint in requested:
        receivers, shell, scene, mapping_hash, mapping_rows = build_endpoint(endpoint, save_blend=(endpoint == "closed"))
        if os.environ.get("R19_INSPECT_ONLY") == "1":
            report["endpoints"][endpoint] = {"p12_pose":endpoint, "other_pods":"closed", "shell_uv2_hash":mapping_hash,
                "shell_mapping_meshes": [r["name"] for r in mapping_rows], "receiver_count":len(receivers),
                "cycles_device":scene.cycles.device}
            continue
        jobs = []
        shell_name = "room_closed" if endpoint == "closed" else "room_open"
        if not only or shell_name in only:
            jobs.append(bake_receiver(shell, shell_name, 2048))
        if endpoint == "closed":
            jobs += [bake_receiver(receivers[f"P{n:02d}"], f"P{n:02d}_closed", 1024) for n in range(1,21)
                     if not only or f"P{n:02d}_closed" in only]
        else:
            if not only or "P12_open" in only:
                jobs += [bake_receiver(receivers["P12"], "P12_open", 1024)]
        report["endpoints"][endpoint] = {"p12_pose":endpoint, "other_pods":"closed", "shell_uv2_hash":mapping_hash,
            "shell_mapping_meshes": [r["name"] for r in mapping_rows], "jobs":jobs, "cycles_device":scene.cycles.device}
    (HERE / "bake_manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("R19_BAKE_COMPLETE", json.dumps(report, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    main()
