"""Run inside Blender using rebuild.py at the repository root."""

import importlib.util
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
from motion import build_behavior
from geometry import group  # noqa: E402 - Blender starts outside the repository.

folder = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.frame_start, scene.frame_end = 1, 49
scene.render.fps = 24
root = group("Specimen")
root.scale = (0.001,) * 3

spec = importlib.util.spec_from_file_location("species_builder", folder / "build.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
manifest = builder.build(root)
parts = manifest["parts"]
identifiers = {p["id"] for p in parts}
assert len(parts) == len(identifiers)
for p in parts:
    obj = bpy.data.objects[p["id"]]
    assert obj.parent == root and any(
        o.type == "MESH" for o in obj.children_recursive
    ), p["id"]
    assert p["system"] in manifest["systems"] and p["source"] in manifest["sources"]
    assert p["parent"] in identifiers | {None}
    obj["partId"] = p["id"]


def verify_dependencies(links):
    for start in links:
        seen = set()
        current = start
        while current is not None:
            if current in seen or current not in links:
                raise ValueError(f"Invalid dependency at {current!r} from {start!r}")
            seen.add(current)
            current = links[current]


verify_dependencies({p["id"]: p["parent"] for p in parts})
controls = manifest["controls"]
if not controls.keys() <= identifiers:
    raise ValueError("Each articulation must belong to a selectable part")
verify_dependencies({pid: ctrl.get("requires") for pid, ctrl in controls.items()})
for part in parts:
    if "control" in part and part["control"] not in controls:
        raise ValueError(f"Unknown articulation for {part['id']}")
has_behavior = build_behavior(folder, manifest)
scene.frame_set(1)
scene.world = bpy.data.worlds.new("Studio")
# A useful starting view for anyone opening the editable master.

for screen in bpy.data.screens:
    for area in screen.areas:
        # Blender's default Shading workspace remembers the builder's home folder.
        for space in area.spaces:
            if space.type == "FILE_BROWSER" and space.params:
                # The RNA setter can retain bytes beyond the new terminating NUL.
                # Overwrite the previous path before shortening it to a relative one.
                capacity = space.params.bl_rna.properties["directory"].length_max
                space.params.directory = b"/" * (capacity - 1)
                space.params.directory = b"//"
        if area.type == "VIEW_3D":
            space = area.spaces.active
            space.clip_start = 0.00005
            space.region_3d.view_distance = manifest["view"]["radius"] * 0.00325
            space.region_3d.view_location = (
                0,
                0,
                manifest["view"]["target"][1] * 0.001,
            )
            space.region_3d.view_rotation = Vector((-0.55, -0.8, -0.95)).to_track_quat(
                "-Z", "Y"
            )
            space.shading.color_type = "MATERIAL"
            space.overlay.show_overlays = False
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.wm.save_as_mainfile(filepath=str(folder / "specimen.blend"), compress=True)
bpy.ops.export_scene.gltf(
    filepath=str(folder / "specimen.glb"),
    export_format="GLB",
    export_extras=True,
    export_animation_mode="NLA_TRACKS" if has_behavior else "SCENE",
    export_anim_slide_to_zero=True,
    export_anim_scene_split_object=False,
    export_frame_range=True,
    export_force_sampling=True,
    export_optimize_animation_size=True,
    export_morph=True,
    export_yup=True,
)
(folder / "anatomy.json").write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
)
