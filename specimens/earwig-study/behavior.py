"""Independent NLA sequence, animated at 24 fps around the specimen's rest joints."""

from math import cos, pi, sin, sqrt
import bpy
from mathutils import Vector
from motion import ease, pulse

SEQUENCE = {
    "clip": "AN_Earwig_SenseWalkDisplay",
    "duration": 8,
    "frameScale": 1.15,
    "target": [0, 1.0, -1.15],
    "actions": [
        {
            "name": "Sweep the feelers",
            "start": 0,
            "note": "Follow the two antennae as their tips trace different arcs.",
        },
        {
            "name": "Walk forward",
            "start": 2.25,
            "note": "Watch one foot stay planted while the opposite group of legs swings forward.",
        },
        {
            "name": "Open the forceps",
            "start": 5.75,
            "note": "The paired pincers spread from their bases, pause and close again.",
        },
    ],
    "references": [
        [
            "Adult anatomy and forceps use · University of Florida",
            "https://ask.ifas.ufl.edu/publication/IN875",
        ],
        [
            "Observed use of the abdomen and pincers · Eisner",
            "https://groups.csail.mit.edu/mac/projects/psyche/67/67-062.html",
        ],
    ],
}


def leg_pose(rig, s, tag, index, phase, strength):
    """Two-bone inverse kinematics with the resting knee defining its bend plane."""
    name = "leg" + str(index + 1) + "_" + tag
    hip = bpy.data.objects["Hip_" + name]
    knee = bpy.data.objects["Knee_" + name]
    ankle = bpy.data.objects["Ankle_" + name]
    a = rig.rest[knee.name]
    b = rig.rest[ankle.name]
    if phase < 0.60:
        step = 0.5 - phase / 0.60
        height = 0
    else:
        f = (phase - 0.60) / 0.40
        step = -0.5 + f - sin(2 * pi * f) / (2 * pi)
        height = 0.37 * sin(pi * f) ** 2
    target = a + b + Vector((0, 0.91 * step * strength, height * strength))
    direction = target.normalized()
    bend = (a - direction * a.dot(direction)).normalized()
    reach = min(target.length, a.length + b.length - 0.00001)
    near = (a.length_squared - b.length_squared + reach * reach) / (2 * reach)
    desired_knee = direction * near + bend * sqrt(
        max(0, a.length_squared - near * near)
    )
    thigh = a.rotation_difference(desired_knee)
    shin = b.rotation_difference(target - desired_knee)
    for obj, q in [
        (hip, thigh),
        (knee, thigh.inverted() @ shin),
        (ankle, shin.inverted()),
    ]:
        obj.rotation_mode = "QUATERNION"
        rig.key(obj, "rotation_quaternion", q)


def pose(rig, t):
    progress = ease(t, 2.25, 5.75) * 3
    strength = pulse(t, 2.25, 2.59, 5.35, 5.75)
    rig.key(
        bpy.data.objects["Specimen"], "location", (0, progress * 0.91 / 0.60 * 0.001, 0)
    )
    for s, tag in [(-1, "l"), (1, "r")]:
        delay = 0.11 if s > 0 else 0
        scan = pulse(t - delay, 0, 0.36, 1.82, 2.3)
        rig.key(
            bpy.data.objects["Feeler_antenna_" + tag],
            "rotation_euler",
            (
                0.11 * scan * sin(3.9 * t + s * 0.27),
                0,
                s
                * (
                    scan * (0.07 + 0.23 * sin(4.2 * t + s * 0.53))
                    + 0.08 * strength * sin(2 * pi * progress)
                ),
            ),
        )
        display = pulse(t - delay, 5.84, 6.59, 7.03, 7.82)
        rig.key(
            bpy.data.objects["Joint_forceps_" + tag],
            "rotation_euler",
            (0, 0, s * 0.53 * display),
        )
        for j in range(3):
            leg_pose(
                rig,
                s,
                tag,
                j,
                (progress + (0.5 if (j + (s > 0)) % 2 else 0)) % 1,
                strength,
            )
