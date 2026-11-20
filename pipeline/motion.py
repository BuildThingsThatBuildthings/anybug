"""Author a named behavior alongside the existing independent dissection tracks."""

from pathlib import Path
from runpy import run_path

import bpy
from mathutils import Euler, Vector


def ease(t, start, end):
    x = max(0, min(1, (t - start) / (end - start)))
    return x * x * (3 - 2 * x)


def pulse(t, rise, peak, release, end):
    return ease(t, rise, peak) * (1 - ease(t, release, end))


def stash(owner, track_name, muted):
    data = owner.animation_data
    action, slot = data.action, data.action_slot
    data.action = None
    track = data.nla_tracks.new()
    track.name = track_name
    strip = track.strips.new(track_name, 1, action)
    strip.action_slot = slot
    track.mute = muted


class Poses:
    def __init__(self):
        self.owners = set()
        self.rest = {o.name: o.location.copy() for o in bpy.context.scene.objects}
        self.frame = 1

    def key(self, target, prop, value):
        setattr(target, prop, value)
        target.keyframe_insert(data_path=prop, frame=self.frame)
        self.owners.add(target.id_data)

    def pivot(self, names, origin, angles):
        """Turn sibling anatomy parts together about one anatomical attachment."""
        pivot = Vector(origin)
        rotation = Euler(angles).to_matrix()
        for name in names:
            obj = bpy.data.objects[name]
            self.key(obj, "location", pivot + rotation @ (self.rest[name] - pivot))
            self.key(obj, "rotation_euler", angles)


def build_behavior(folder, manifest):
    source = Path(folder) / "behavior.py"
    if not source.is_file():
        return False
    script = run_path(str(source))
    info = script["SEQUENCE"]
    manifest["behavior"] = info
    scene = bpy.context.scene
    scene.frame_set(1)
    for owner in [*scene.objects, *bpy.data.shape_keys]:
        data = owner.animation_data
        if data and data.action:
            stash(owner, "Articulation", True)
    poses = Poses()
    fps = scene.render.fps
    scene.frame_end = 1 + round(info["duration"] * fps)
    for frame in range(1, scene.frame_end + 1):
        poses.frame = frame
        script["pose"](poses, (frame - 1) / fps)
    for owner in sorted(poses.owners, key=lambda o: o.name):
        stash(owner, info["clip"], False)
    for chapter in info["actions"]:
        scene.timeline_markers.new(
            chapter["name"], frame=1 + round(chapter["start"] * fps)
        )
    scene.frame_set(1)
    return True
