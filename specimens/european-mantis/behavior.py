"""Peering head turns, foreleg preparation, forward sweep and tibial closure."""

from math import radians

import bpy
from motion import ease, pulse

SEQUENCE = {
    "clip": "AN_Mantis_TrackAndGrasp",
    "duration": 8,
    "frameScale": 1.06,
    "actions": [
        {
            "name": "Scan",
            "start": 0,
            "note": "Watch the triangular head turn while the walking legs stay planted.",
        },
        {
            "name": "Take aim",
            "start": 3,
            "note": "The mantis faces forward and raises its folded grasping legs.",
        },
        {
            "name": "Reach and grasp",
            "start": 5,
            "note": "The forelegs sweep out. The spined shins close against the thighs before the legs draw back.",
        },
    ],
    "references": [
        [
            "Visual tracking in mantids · Behavioral Ecology",
            "https://doi.org/10.1093/beheco/araf107",
        ],
        [
            "Approach and sweep · Comparative mantis strike recordings",
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC7280040/",
        ],
    ],
}


def pose(rig, t):
    scan = (
        -0.54 * ease(t, 0.12, 0.88)
        + 1.10 * ease(t, 1.02, 2.26)
        - 0.53 * ease(t, 2.48, 3.55)
        - 0.03 * ease(t, 6.7, 7.65)
    )
    pitch = 0.085 * pulse(t, 0.35, 1.1, 1.85, 2.75) - 0.08 * pulse(t, 3, 4.5, 5.8, 7.35)
    head = ["head", "ocelli", "brain"] + [
        base + "_" + side
        for side in ("l", "r")
        for base in ("eye", "jaw", "palp", "antenna")
    ]
    rig.pivot(head, (0, 0.9 * 26.5, 4.5 + 0.9 * 18.2), (pitch, 0, scan))
    for side, tag in [(-1, "l"), (1, "r")]:
        delay = 0.045 if side > 0 else 0
        u = t - delay
        ready = pulse(u, 3.13, 4.59, 5.26, 5.77)
        reach = pulse(u, 5.12, 5.64, 6.03, 7.37)
        opened = (0.25 * ready + 0.99 * ease(u, 5.01, 5.62)) * (1 - ease(u, 5.67, 5.99))
        spread = 0.09 * pulse(u, 3.25, 4.52, 5.4, 6.34)
        parts = [
            kind + "_" + tag
            for kind in (
                "coxa",
                "trochanter",
                "femur",
                "tibia",
                "forefoot",
                "flexor",
                "femoral_spines",
                "tibial_spines",
            )
        ]
        rig.pivot(
            parts,
            (side * 2.1 * 0.9, 21.4 * 0.9, 20.1 * 0.9),
            (0.24 * ready + 0.34 * reach, 0, -side * spread),
        )
        for pid in parts:
            # The dissection builder supplies identical local pivots on each
            # cooperating structure. Keep the flexor, foot and spines attached.
            for joint in bpy.data.objects[pid].children_recursive:
                if joint.type == "EMPTY" and joint.name.startswith("Joint "):
                    degrees = 113 if joint.name.startswith("Joint Joint ") else 8
                    rig.key(joint, "rotation_euler", (radians(degrees) * opened, 0, 0))
