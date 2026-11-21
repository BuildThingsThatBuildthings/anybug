"""Earwig cuticle and hinged appendages. Local dimensions are millimetres."""

from math import cos, sin, pi
from mathutils import Vector
from geometry import group, mesh, oval, tube


def plate(name, parent, rows, mat, pigment=None, arc=None, thickness=0.055):
    """Loft elliptical cross sections; an open arc becomes a thin removable shell."""
    rows = sorted(rows)
    count = 32
    vertices, faces, colors = [], [], []
    for y, x, z, width, height in rows:
        if arc:
            start, end = arc
            rim = [(start + (end - start) * i / count, 0) for i in range(count + 1)]
            rim += [(a, thickness) for a, _ in reversed(rim)]
        else:
            rim = [(i * 2 * pi / count, 0) for i in range(count)]
        stride = len(rim)
        for a, inset in rim:
            vertices.append(
                (x + (width - inset) * cos(a), y, z + (height - inset) * sin(a))
            )
            if pigment:
                colors.append(pigment(y, a, inset))
    for row in range(len(rows) - 1):
        for i in range(stride):
            a = row * stride + i
            b = row * stride + (i + 1) % stride
            faces.append((a, a + stride, b + stride, b))
    faces.extend(
        [
            tuple(range(stride)),
            tuple(reversed(range(len(vertices) - stride, len(vertices)))),
        ]
    )
    obj = mesh("SM_" + name, parent, vertices, faces, mat)
    if colors:
        attr = obj.data.color_attributes.new(
            name="Cuticle pigment", type="BYTE_COLOR", domain="POINT"
        )
        for v, rgb in zip(attr.data, colors):
            v.color_srgb = (*rgb, 1)
    return obj


def pigmented(mat):
    color = mat.node_tree.nodes.new("ShaderNodeVertexColor")
    color.layer_name = "Cuticle pigment"
    mat.node_tree.links.new(
        color.outputs["Color"],
        mat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"],
    )


def spindle(name, parent, a, b, width, depth, mat):
    a, b = Vector(a), Vector(b)
    obj = oval(
        "SM_" + name,
        parent,
        (a + b) * 0.5,
        (width, depth, (b - a).length * 0.5),
        mat,
        16,
        10,
    )
    obj.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
    return obj


def hinge(node, origin, angle):
    # Mesh coordinates below are authored relative to the rest hinge.
    joint = group("Joint_" + node.name, node, origin)
    for frame, value in ((1, 0), (49, angle)):
        joint.rotation_euler.z = value
        joint.keyframe_insert(data_path="rotation_euler", frame=frame)
    joint.rotation_euler.z = 0
    return joint


def forceps(node, s, m):
    root = (s * 0.72, -5.53, 1.02)
    joint = hinge(node, root, s * 0.53)
    # Broad, compressed tooth-bearing base gives way to an acute hooked black tip.
    profile = [
        (0, 0, 0, 0.30, 0.18),
        (0.08, -0.25, 0, 0.31, 0.17),
        (0.18, -0.52, 0.025, 0.29, 0.15),
        (0.37, -0.87, 0.04, 0.235, 0.14),
        (0.59, -1.25, 0.07, 0.167, 0.12),
        (0.72, -1.65, 0.10, 0.122, 0.10),
        (0.73, -2.03, 0.12, 0.10, 0.082),
        (0.62, -2.36, 0.14, 0.08, 0.066),
        (0.39, -2.67, 0.18, 0.068, 0.057),
        (0.12, -2.88, 0.21, 0.05, 0.045),
        (-0.18, -2.98, 0.25, 0.035, 0.035),
        (-0.49, -2.97, 0.28, 0.008, 0.009),
    ]
    verts, faces = [], []
    for j, (x, y, z, w, h) in enumerate(profile):
        prev, nxt = profile[max(0, j - 1)], profile[min(len(profile) - 1, j + 1)]
        tangent = Vector((s * (nxt[0] - prev[0]), nxt[1] - prev[1], 0)).normalized()
        normal = Vector((-tangent.y, tangent.x, 0))
        for i in range(18):
            a = 2 * pi * i / 18
            verts.append(
                tuple(
                    Vector((s * x, y, z))
                    + normal * w * cos(a)
                    + Vector((0, 0, h * sin(a)))
                )
            )
            if j:
                k = (j - 1) * 18 + i
                n = (j - 1) * 18 + (i + 1) % 18
                faces.append((k, n, n + 18, k + 18))
    faces.extend(
        [tuple(reversed(range(18))), tuple(range(len(verts) - 18, len(verts)))]
    )
    blade = mesh("SM_Cercal_blade", joint, verts, faces, m["cercus"])
    attr = blade.data.color_attributes.new(
        name="Cuticle pigment", type="BYTE_COLOR", domain="POINT"
    )
    for i, item in enumerate(attr.data):
        t = (i // 18) / (len(profile) - 1)
        near = max(0, 1 - 2.8 * t)
        item.color_srgb = (
            0.12 + 0.27 * near,
            0.074 + 0.14 * near,
            0.065 + 0.065 * near,
            1,
        )
    for j in range(5):
        t = j / 5
        a = Vector((s * (-0.16 + 0.24 * t), -0.23 - 0.55 * t, 0.01))
        tube(
            "SM_Basal_tooth",
            joint,
            [
                a,
                a + Vector((-s * 0.10, -0.05, 0)),
                a + Vector((-s * (0.11 + 0.04 * t), -0.093, 0)),
            ],
            [0.054, 0.039, 0.006],
            m["brown"],
            8,
        )


def antenna(node, s, m):
    base = Vector((s * 0.67, 5.42, 1.38))
    joint = group("Feeler_" + node.name, node, base)
    for i in range(14):

        def point(t):
            return Vector(
                (
                    s * (2.22 * t + 0.32 * sin(pi * t)),
                    3.58 * t,
                    0.13 * t + 0.20 * sin(1.4 * pi * t),
                )
            )

        a, b = point(i / 14), point((i + 1) / 14)
        r = 0.108 * (1 - 0.61 * i / 14)
        tube(
            "SM_Antennomere",
            joint,
            [a, a.lerp(b, 0.13), a.lerp(b, 0.79), b],
            [r * 0.67, r, r * 0.88, r * 0.50],
            m["russet"] if i < 2 else m["amber"],
            10,
        )
        if i > 2:
            tip = a.lerp(b, 0.75)
            tube(
                "SM_Sensory_hair",
                joint,
                [tip, tip + Vector((s * 0.085, 0.027, 0.04))],
                [0.009, 0.0015],
                m["hair"],
                5,
            )


def tegmen(node, s, m):
    # Shallow longitudinal ridges and an exposed amber margin follow the wing surface.
    joint = group("Cover_" + node.name, node, (s * 0.617, 2.76, 1.645))
    for frame, t in ((1, 0), (49, 1)):
        joint.rotation_euler = (0.26 * t, -s * 0.89 * t, -s * 0.21 * t)
        joint.keyframe_insert(data_path="rotation_euler", frame=frame)
    joint.rotation_euler = (0, 0, 0)
    rows = [
        (-2.25, s * 0.01, -0.01, 0.42, 0.11),
        (-2.08, s * 0.01, 0.01, 0.60, 0.155),
        (-1.7, s * 0.01, 0.05, 0.633, 0.17),
        (-0.76, 0, 0.07, 0.635, 0.17),
        (-0.18, -s * 0.02, 0.06, 0.58, 0.16),
        (0, -s * 0.08, 0.02, 0.44, 0.11),
    ]

    def paint(y, a, inset):
        side = cos(a) * s
        edge = max(0, (side - 0.55) / 0.45)
        ridges = (0.5 + 0.5 * cos(side * 27 + y * 0.6)) * 0.025
        return (
            0.255 + 0.19 * edge + ridges,
            0.157 + 0.13 * edge + ridges,
            0.122 + 0.073 * edge + ridges,
        )

    plate("Leathery_forewing", joint, rows, m["wing"], paint)
    for lane in [-0.30, -0.08, 0.13, 0.32]:
        pts = []
        for j in range(13):
            t = j / 12
            x = s * (lane + 0.035 * sin(pi * t))
            pts.append(
                (
                    x,
                    -0.20 - 1.83 * t,
                    0.19 - 0.07 * t + 0.029 * sin(pi * t) - 0.10 * (lane / 0.58) ** 2,
                )
            )
        tube(
            "SM_Tegminal_stria",
            joint,
            pts,
            [0.010 + 0.006 * sin(pi * j / 12) for j in range(13)],
            m["vein"],
            5,
        )


def walking_leg(node, s, j, m):
    hip_y = [3.47, 2.18, 0.87][j]
    hip = Vector((s * 0.76, hip_y, 1.03))
    pivot = group("Hip_" + node.name, node, hip)
    knee = Vector((s * (1.43 + 0.08 * j), [0.8, 0.06, -0.93][j], -0.10))
    ankle = Vector((s * (2.12 + 0.15 * j), [1.40, -0.40, -1.83][j], -0.90))
    coxa = Vector((s * 0.43, [0.15, 0.04, -0.2][j], -0.12))
    spindle("Coxa", pivot, (0, 0, 0), coxa, 0.17, 0.14, m["amber"])
    spindle("Femur", pivot, coxa, knee, 0.15 if j < 2 else 0.19, 0.13, m["leg"])
    oval("SM_Trochanter", pivot, coxa, (0.117, 0.12, 0.102), m["amber"], 14, 8)
    oval("SM_Femoral_condyle", pivot, knee, (0.098, 0.117, 0.084), m["leg"], 14, 8)
    shin = group("Knee_" + node.name, pivot, knee)
    tip = ankle - knee
    tube(
        "SM_Tibia",
        shin,
        [Vector((0, 0, 0)), tip * 0.15, tip * 0.70, tip],
        [0.123, 0.114, 0.081, 0.063],
        m["leg"],
        12,
    )
    for k in range(1, 7):
        p = tip * (k / 8)
        tube(
            "SM_Tibial_bristle",
            shin,
            [p, p + Vector((s * 0.08, -0.055, -0.06))],
            [0.010, 0.002],
            m["hair"],
            5,
        )
    for side in [-1, 1]:
        tube(
            "SM_Apical_spur",
            shin,
            [tip * 0.88, tip + Vector((side * 0.036, 0.07, -0.045))],
            [0.026, 0.003],
            m["amber"],
            6,
        )
    foot = group("Ankle_" + node.name, shin, tip)
    last = Vector((0, 0, 0))
    for k, (x, y, z) in enumerate(
        [(0.18, 0.03, -0.036), (0.32, 0.07, -0.044), (0.54, 0.10, -0.066)]
    ):
        nxt = Vector((s * x, y, z))
        spindle(
            "Tarsomere", foot, last, nxt, 0.055 if k != 1 else 0.079, 0.04, m["amber"]
        )
        last = nxt
    for sign in [-1, 1]:
        tube(
            "SM_Pretarsal_claw",
            foot,
            [
                last,
                last + Vector((s * 0.072, sign * 0.052, 0.018)),
                last + Vector((s * 0.11, sign * 0.056, -0.023)),
            ],
            [0.021, 0.015, 0.002],
            m["brown"],
            7,
        )
