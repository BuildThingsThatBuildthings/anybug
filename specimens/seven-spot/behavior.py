"""A forward walk followed by wing deployment, a short flight and landing."""

from math import cos, pi, sin

import bpy
from motion import ease, pulse

SEQUENCE = {
    "clip": "AN_Ladybug_WalkToFlight",
    "duration": 10,
    "frameScale": 1.48,
    "target": [0, 1.8, -1.15],
    "actions": [
        {
            "name": "Walk",
            "start": 0,
            "note": "Follow one foot as it lifts, swings forward and touches down.",
        },
        {
            "name": "Unfold wings",
            "start": 3.5,
            "note": "The spotted covers lift first. The thin flight wings unfold beneath them.",
        },
        {
            "name": "Fly and land",
            "start": 6,
            "note": "Watch the hindwings beat, then fold back beneath the covers after landing.",
        },
    ],
    "references": [
        [
            "Walking feet · Mercer and Hosoda",
            "https://doi.org/10.3390/biomimetics9030184",
        ],
        [
            "Wing folding · Saito and colleagues",
            "https://doi.org/10.1073/pnas.1620612114",
        ],
    ],
}


def pose(rig, t):
    stride = ease(t, 0.12, 3.25)
    phase = 2 * pi * 2.5 * stride
    walking = pulse(t, 0, 0.46, 2.97, 3.44)
    flight = pulse(t, 6.15, 6.85, 7.85, 8.55)
    beat = pulse(t, 5.98, 6.37, 8.19, 8.61) * sin(2 * pi * 2.55 * (t - 6))
    # Coordinates of the specimen root are metres; articulated geometry is in mm.
    root = bpy.data.objects["Specimen"]
    rig.key(
        root,
        "location",
        (
            0,
            0.001 * (2.15 * stride + 0.38 * ease(t, 6.4, 8.45)),
            0.001 * (1.23 * flight + 0.035 * walking * sin(phase) ** 2),
        ),
    )
    rig.key(root, "rotation_euler", (0.09 * flight, 0, 0))
    for side, tag in [(-1, "l"), (1, "r")]:
        for index, hip_y in enumerate([1.57, 0.71, -0.26]):
            step = phase + pi * ((index + (side > 0)) % 2)
            lift = max(0, cos(step)) ** 2
            angles = (
                0,
                -side * (0.24 * walking * lift + 0.13 * flight),
                side * 0.25 * walking * sin(step),
            )
            rig.pivot(
                [f"leg_{tag}{index}", f"foot_{tag}{index}"],
                (side * 0.86, hip_y, -0.03),
                angles,
            )
        survey = walking * sin(phase * 0.8 + side * 0.7)
        rig.pivot(
            ["antenna_" + tag],
            (side * 0.55, 3, 0.46),
            (0.13 * survey, 0, side * 0.38 * survey),
        )
        delayed = t - (0.07 if side > 0 else 0)
        cover = ease(delayed, 3.5, 4.7) * (
            1 - 0.28 * ease(delayed, 8.57, 9.05) - 0.72 * ease(delayed, 9.31, 9.91)
        )
        rig.key(
            bpy.data.objects["cover_" + tag],
            "rotation_euler",
            (-0.89 * cover, -side * 0.23 * cover, side * 0.55 * cover),
        )
        unfold = ease(delayed, 4.41, 5.91) * (1 - ease(delayed, 8.68, 9.62))
        wing = bpy.data.objects["wing_" + tag]
        rig.key(wing, "rotation_euler", (0, -side * 0.52 * beat, 0))
        membrane = next(
            o for o in wing.children if o.type == "MESH" and o.data.shape_keys
        )
        for index, key in enumerate(
            list(membrane.data.shape_keys.key_blocks)[1:], start=1
        ):
            rig.key(key, "value", max(0, 1 - abs(8 * unfold - index)))
