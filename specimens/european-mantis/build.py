"""Build one adult European mantis. Coordinates are x, headward, up."""

from math import cos, pi, radians, sin
from pathlib import Path
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).parent))
from brief import NOTES, SOURCES, SYSTEMS
from geometry import group, material, mesh, oval, smooth_path, tube


def loft(name, parent, rings, mat, arc=(0, 2 * pi)):
    """Elliptical sections along the body, optionally open along the belly."""
    sides = 32
    verts, faces = [], []
    closed = arc == (0, 2 * pi)
    stride = sides if closed else sides + 1
    for row, (y, z, width, height) in enumerate(rings):
        for i in range(stride):
            a = arc[0] + (arc[1] - arc[0]) * i / sides
            verts.append((width * cos(a), y, z + height * sin(a)))
        if row:
            for i in range(sides):
                a = (row - 1) * stride + i
                b = (row - 1) * stride + (i + 1) % stride
                faces.append((a, a + stride, b + stride, b))
    if closed:
        faces.extend(
            [
                tuple(range(stride)),
                tuple(reversed(range(len(verts) - stride, len(verts)))),
            ]
        )
    return mesh(name, parent, verts, faces, mat)


def tapered(name, parent, start, end, widths, mat, sides=12):
    a, b = Vector(start), Vector(end)
    return tube(
        name,
        parent,
        [a.lerp(b, i / (len(widths) - 1)) for i in range(len(widths))],
        widths,
        mat,
        sides,
    )


def bead(name, parent, point, size, mat):
    return oval(name, parent, point, size, mat, 18, 10)


def surface(name, parent, f, rows, cols, mat):
    verts = [f(i / rows, j / cols) for i in range(rows + 1) for j in range(cols + 1)]
    faces = []
    for i in range(rows):
        for j in range(cols):
            a = i * (cols + 1) + j
            faces.append((a, a + 1, a + cols + 2, a + cols + 1))
    return mesh(name, parent, verts, faces, mat)


def wing(parent, side, hind, m):
    # The tegmen is a pitched, tapering leaf. Its costal edge wraps the flank.
    def point(u, v):
        envelope = max(0.015, sin(pi * u) ** 0.66)
        y = 3.8 - 36 * u
        z = 11.25 - 3.0 * u + 0.95 * sin(pi * u)
        x = 0.15 + 1.15 * (1 - u) ** 4 + 0.62 * u + 6.05 * envelope * v
        z += envelope * (0.22 + 0.85 * sin(pi * v) - 2.95 * v * v)
        if hind:
            x = 0.92 * x
            z -= 1.05 + 0.38 * v
            z += 0.16 * cos(8 * pi * v) * envelope
        return Vector((side * x, y, z))

    skin = m["membrane"] if hind else m["wing"]
    blade = surface(
        "Pleated hindwing" if hind else "Tegmen blade", parent, point, 36, 12, skin
    )
    if side == 1:
        blade.data.flip_normals()
    if not hind:
        # Smooth pigment bands follow the veins. Vertex colors travel inside the GLB.
        pigments = blade.data.color_attributes.new(
            name="Wing pigment", type="BYTE_COLOR", domain="POINT"
        )
        for i, value in enumerate(pigments.data):
            u, v = (i // 13) / 36, (i % 13) / 12
            light = 0.5 + 0.5 * sin(11 * u + 6 * v) * cos(15 * v - 3 * u)
            edge = max(0, (v - 0.72) / 0.28)
            value.color_srgb = (
                0.37 + 0.14 * light + 0.15 * edge,
                0.53 + 0.12 * light + 0.09 * edge,
                0.24 + 0.09 * light,
                1,
            )
        if not skin.node_tree.nodes.get("Wing pigment"):
            pigment = skin.node_tree.nodes.new("ShaderNodeVertexColor")
            pigment.name = pigment.layer_name = "Wing pigment"
            shader = skin.node_tree.nodes.get("Principled BSDF")
            skin.node_tree.links.new(
                pigment.outputs["Color"], shader.inputs["Base Color"]
            )
    # Closed resting membranes are visible from below when removed.
    skin.use_backface_culling = False
    for v in [0.08, 0.26, 0.46, 0.65, 0.86] if hind else [0.035, 0.36, 0.81, 0.985]:
        points = [point(i / 28, v) + Vector((0, 0, 0.06)) for i in range(29)]
        tube(
            "Longitudinal vein",
            parent,
            points,
            [0.025 + 0.055 * sin(pi * i / 28) for i in range(29)],
            m["vein"],
            6,
        )
    if not hind:
        for i in range(1, 15):
            u = i / 17
            for va, vb in ((0.36, 0.05), (0.36, 0.78), (0.78, 0.97)):
                us = min(0.98, u + 0.10 * abs(va - vb) / 0.4)
                path = [
                    point(u + (us - u) * j / 5, va + (vb - va) * j / 5)
                    + Vector((0, 0, 0.045))
                    for j in range(6)
                ]
                tube("Crossvein", parent, path, 0.035, m["vein"], 5)
        bead(
            "Pale wing stigma",
            parent,
            point(0.46, 0.68) + Vector((0, 0, 0.10)),
            (0.24, 0.83, 0.10),
            m["straw"],
        )


def foreleg(add, s, side, m):
    """Sibling selectable pieces use copies of the same two local joint axes."""
    tag = "l" if s < 0 else "r"
    control = "tibia_" + tag
    shoulder = Vector((s * 2.1, 21.4, 20.1))
    hip = Vector((s * 6.7, 15.6, 7.6))
    knee = Vector((s * 9.6, 29.0, 18.1))
    ankle = Vector((s * 10.0, 19.2, 7.35))

    def part(kind, parent=None):
        return add(kind + "_" + tag, kind, side, parent, control)

    def pivot(node, origin, angle):
        joint = group("Joint " + node.name, node, origin)
        for frame, factor in ((1, 0), (49, 1)):
            joint.rotation_euler.x = radians(angle) * factor
            joint.keyframe_insert(data_path="rotation_euler", frame=frame)
        joint.rotation_euler.x = 0
        return joint

    def moving(part_node, shin=False):
        thigh = pivot(part_node, hip, 8)
        if shin:
            return pivot(thigh, knee - hip, 113), knee
        return thigh, hip

    coxa = part("coxa")
    tapered("Long coxa", coxa, shoulder, hip, [0.82, 1.16, 1.04, 0.76, 0.65], m["jade"])
    mark = shoulder.lerp(hip, 0.37)
    mark.x -= s * 0.90
    patch = bead("Coxal eyespot", coxa, mark, (0.28, 0.91, 1.45), m["smoke"])
    patch.rotation_euler.x = -0.42
    bead(
        "Ivory eyespot center",
        coxa,
        mark - Vector((s * 0.20, 0, 0)),
        (0.15, 0.38, 0.58),
        m["ivory"],
    )
    connector = part("trochanter", "coxa_" + tag)
    bead("Trochanter", connector, hip, (0.92, 1.1, 1.0), m["lime"])
    femur = part("femur", "trochanter_" + tag)
    thigh, base = moving(femur)
    tapered(
        "Fusiform femur",
        thigh,
        Vector((0, 0, 0)),
        knee - base,
        [0.72, 1.35, 1.55, 1.58, 1.32, 0.91, 0.62],
        m["jade"],
        18,
    )
    bead("Knee condyle", thigh, knee - base, (0.82, 0.83, 0.75), m["lime"])
    tibia = part("tibia", "femur_" + tag)
    shin, base = moving(tibia, True)
    tapered(
        "Tibial blade",
        shin,
        (0, 0, 0),
        ankle - base,
        [0.66, 0.84, 0.71, 0.50, 0.26],
        m["lime"],
        14,
    )
    # Spines lean into the gap between the opposed segments.
    for kind, lower, start, end, count in (
        ("femoral_spines", False, hip, knee, 10),
        ("tibial_spines", True, knee, ankle, 12),
    ):
        spines = part(kind, ("tibia_" if lower else "femur_") + tag)
        holder, base = moving(spines, lower)
        for row in (-1, 1):
            for i in range(count):
                t = 0.14 + 0.75 * i / (count - 1)
                offset = Vector(
                    (
                        s * (0.36 * row + (0.0 if lower else 0.32)),
                        (-0.22 if lower else 0.34),
                        -0.75 if not lower else 0.45,
                    )
                )
                a = start.lerp(end, t) - base + offset
                reach = (0.60 if lower else 1.0) * (1.4 if i % 3 == 0 else 0.83)
                b = a + Vector(
                    (
                        s * 0.16,
                        (-0.38 if lower else 0.58) * reach,
                        (1 if lower else -1) * reach,
                    )
                )
                tapered(
                    "Cuticular spine", holder, a, b, [0.19, 0.13, 0.018], m["umber"], 6
                )
        if lower:
            a = ankle - base
            tube(
                "Apical spur",
                holder,
                [
                    a,
                    a + Vector((s * 0.14, -0.64, 0.14)),
                    a + Vector((s * 0.22, -1.05, 0.92)),
                ],
                [0.26, 0.18, 0.025],
                m["umber"],
            )
    foot = part("forefoot", "tibia_" + tag)
    holder, base = moving(foot, True)
    a = ankle - base
    tarsus(holder, a, a + Vector((s * 1, -3, -3.0)), s, m)
    muscle = add("flexor_" + tag, "muscle", side, "femur_" + tag, control)
    holder, base = moving(muscle)
    a = Vector((0, 0, 0)).lerp(knee - base, 0.15)
    b = (knee - base) * 0.79
    tapered("Flexor belly", holder, a, b, [0.18, 0.70, 0.80, 0.58, 0.22], m["muscle"])
    tapered("Flexor tendon", holder, b, (knee - base) * 0.98, [0.19, 0.08], m["silk"])


def tarsus(parent, start, end, s, m):
    a, b = Vector(start), Vector(end)
    for i in range(5):
        tapered(
            "Tarsomere",
            parent,
            a.lerp(b, i / 5),
            a.lerp(b, (i + 1) / 5),
            [0.20, 0.17, 0.115],
            m["straw"],
            8,
        )
    for side in (-1, 1):
        tube(
            "Claw",
            parent,
            [
                b,
                b + Vector((s * 0.15, 0.24 * side, 0.12)),
                b + Vector((s * 0.39, 0.40 * side, -0.04)),
            ],
            [0.11, 0.08, 0.015],
            m["umber"],
            6,
        )


def walking(add, s, side, hind, m):
    name = "hind" if hind else "middle"
    tag = name + ("_l" if s < 0 else "_r")
    h = Vector((s * 2.8, -3.1 if hind else 1.4, 7.2))
    k = Vector(
        (s * (12.4 if hind else 10.8), -17.0 if hind else 7.0, 13.0 if hind else 12.4)
    )
    a = Vector((s * (18.0 if hind else 16.2), -26.0 if hind else -0.8, 0.22))
    leg = add(tag, "walk", side + " " + name)
    tapered("Walking coxa", leg, h, h.lerp(k, 0.15), [0.72, 0.87, 0.59], m["jade"])
    tapered(
        "Walking femur",
        leg,
        h.lerp(k, 0.15),
        k,
        [0.55, 0.86, 0.73, 0.55, 0.38],
        m["jade"],
    )
    bead("Walking knee", leg, k, (0.50, 0.50, 0.53), m["straw"])
    tapered("Walking tibia", leg, k, a, [0.42, 0.46, 0.35, 0.27, 0.17], m["lime"])
    foot = add("foot_" + tag, "foot", side + " " + name, tag)
    tarsus(foot, a, a + Vector((s * 3.6, 2.4, 0)), s, m)


def abdomen(add, m):
    back = add("back", "back")
    belly = add("belly", "belly")

    def ring(t, bulge):
        return (
            -31 + 29 * t,
            7.35 + 0.48 * t,
            (0.42 + 5.25 * sin(pi * t) ** 0.65 + 1.65 * t) * bulge,
            (0.46 + 2.22 * sin(pi * t) ** 0.65 + 0.78 * t) * bulge,
        )

    for parent, arc, n in ((back, (0, pi), 8), (belly, (pi, 2 * pi), 6)):
        for i in range(n):
            rings = [
                ring((i + v) / n, b)
                for v, b in ((0, 0.95), (0.1, 1.01), (0.39, 1.035), (1, 0.998))
            ]
            loft(
                "Abdominal cuticle",
                parent,
                rings,
                m["abdomen"] if parent == back else m["belly"],
                arc,
            )
            loft(
                "Plate lip",
                parent,
                [ring(i / n, 0.968), ring((i + 0.055) / n, 1.006)],
                m["straw"],
                arc,
            )


def head_and_thorax(add, m):
    head = add("head", "head")
    # Stacked horizontal sections form a broad triangular face, tapering to the mouth.
    sections = [
        (16.4, 27.9, 1.1, 0.86),
        (17.0, 28.0, 1.9, 1.13),
        (18.4, 27.7, 3.1, 1.70),
        (20.2, 27.1, 4.0, 1.88),
        (21.6, 26.7, 3.8, 1.48),
        (22.3, 26.7, 2.6, 0.97),
        (22.6, 26.7, 0.28, 0.2),
    ]
    verts = []
    faces = []
    for row, (z, y, w, d) in enumerate(sections):
        for j in range(32):
            a = 2 * pi * j / 32
            verts.append((w * cos(a), y + d * sin(a), z))
            if row:
                b = (row - 1) * 32 + j
                c = (row - 1) * 32 + (j + 1) % 32
                faces.append((b, c, c + 32, b + 32))
    faces.extend(
        [tuple(reversed(range(32))), tuple(range(len(verts) - 32, len(verts)))]
    )
    mesh("Triangular head", head, verts, faces, m["jade"])
    shield = add("pronotum", "pronotum")
    rings = [
        (2.0, 9.5, 2.45, 1.65),
        (4.4, 10.2, 2.35, 1.62),
        (9, 11.7, 1.7, 1.35),
        (15.3, 14, 1.55, 1.2),
        (19.6, 15.5, 2.45, 1.38),
        (21.3, 16.2, 3.03, 1.55),
        (23.8, 17.4, 2.1, 1.4),
        (25.8, 18.1, 1.35, 1.12),
    ]
    rings = [(y, z + max(0, y - 3) * 0.22, w, h) for y, z, w, h in rings]
    loft("Long pronotum", shield, rings, m["jade"])
    for side in (-1, 1):
        tube(
            "Pale pronotal margin",
            shield,
            [(side * w * 0.96, y, z + h * 0.24) for y, z, w, h in rings],
            [0.05, 0.12, 0.12, 0.10, 0.15, 0.16, 0.10, 0.05],
            m["straw"],
            7,
        )
    for side in (-1, 1):
        smooth_path(
            "Facial ridge",
            head,
            [
                (side * 3.0, 28.33, 20.15),
                (side * 2.0, 29.07, 19.66),
                (side * 1.1, 29.40, 18.60),
                (side * 0.30, 29.34, 18.25),
            ],
            0.09,
            m["straw"],
        )

    loft(
        "Wing-bearing thorax",
        add("chest", "chest"),
        [
            (-5.4, 8, 3.1, 2.1),
            (-3.1, 8.2, 4.0, 2.6),
            (0, 8.3, 3.9, 2.55),
            (3.1, 8.8, 3.0, 2.15),
            (4.8, 9.6, 2, 1.35),
        ],
        m["abdomen"],
    )
    eyes = add("ocelli", "ocelli", parent="head")
    for x, z in ((-0.67, 20.3), (0.67, 20.3), (0, 19.7)):
        bead("Simple lens", eyes, (x, 28.88, z), (0.28, 0.20, 0.27), m["ocellus"])
    for s, tag, side in ((-1, "l", "Left"), (1, "r", "Right")):
        eye = add("eye_" + tag, "eye", side, "head")
        bead("Compound lens", eye, (s * 3.53, 27.0, 20.50), (1.95, 1.98, 2.0), m["eye"])
        bead(
            "Pseudopupil", eye, (s * 4.98, 28.07, 21.07), (0.40, 0.38, 0.36), m["smoke"]
        )
        antenna = add("antenna_" + tag, "antenna", side, "head")
        points = [
            (s * 1.84, 28.2, 21.3),
            (s * 2.7, 30.3, 23),
            (s * 4.5, 33.9, 25.8),
            (s * 6.3, 38, 28.0),
            (s * 7.6, 42.8, 28.8),
        ]
        tube(
            "Flagellum",
            antenna,
            points,
            [0.28, 0.20, 0.16, 0.105, 0.028],
            m["umber"],
            9,
        )
        bead("Antennal scape", antenna, points[0], (0.47, 0.41, 0.41), m["straw"])
        jaw = add("jaw_" + tag, "jaw", side, "head")
        tube(
            "Mandibular edge",
            jaw,
            [
                (s * 1.45, 28.27, 17.45),
                (s * 1.2, 29.05, 16.46),
                (s * 0.32, 29.44, 16.30),
            ],
            [0.6, 0.56, 0.14],
            m["umber"],
            12,
        )
        palp = add("palp_" + tag, "palp", side, "head")
        tube(
            "Segmented palp",
            palp,
            [
                (s * 1.65, 27.95, 17),
                (s * 2.18, 29.10, 16.3),
                (s * 2.0, 29.92, 15.69),
                (s * 2.4, 30.75, 15.31),
            ],
            [0.22, 0.25, 0.15, 0.22],
            m["straw"],
            8,
        )


def internal_organs(add, m):
    brain = add("brain", "brain")
    bead("Brain center", brain, (0, 26.9, 19.75), (1.44, 0.94, 0.87), m["nerve"])
    cord = add("cord", "cord")
    cord_points = [
        (0, 27.2, 22.7),
        (0, 23.5, 20.9),
        (0, 14, 15.2),
        (0, 4.0, 8.7),
        (0, -4, 6.9),
        (0, -16, 5.95),
        (0, -28, 6.55),
    ]
    smooth_path("Ventral connectives", cord, cord_points, 0.21, m["nerve"])
    for x, y, z in cord_points[1:]:
        bead("Ganglion", cord, (x, y, z), (0.56, 0.73, 0.31), m["nerve"])
    oesophagus = add("oesophagus", "oesophagus")
    smooth_path(
        "Foregut tube",
        oesophagus,
        [
            (0, 28.2, 22.1),
            (0, 24.3, 21.6),
            (0, 17, 17.4),
            (0, 7.3, 11.55),
            (0, 2.3, 8.85),
        ],
        0.36,
        m["tissue"],
    )
    crop = add("crop", "crop")
    loft(
        "Crop sac",
        crop,
        [
            (-9, 8, 0.46, 0.55),
            (-7.6, 8, 1.38, 1.38),
            (-4.3, 8.2, 2.06, 1.65),
            (-0.9, 8.6, 1.68, 1.31),
            (2.7, 8.9, 0.35, 0.44),
        ],
        m["tissue"],
    )
    valve = add("valve", "valve")
    bead("Proventricular bulb", valve, (0, -9.75, 8), (1.03, 1.11, 0.91), m["muscle"])
    gut = add("midgut", "midgut")
    tube(
        "Midgut",
        gut,
        [(0, -10.4, 8), (0.3, -12.7, 8.1), (-0.18, -15.8, 7.9), (0.28, -20.1, 7.6)],
        [0.73, 1.28, 1.13, 0.67],
        m["tissue"],
        14,
    )
    caeca = add("caeca", "caeca")
    for i in range(6):
        a = 2 * pi * i / 6
        smooth_path(
            "Gastric caecum",
            caeca,
            [
                (0.7 * cos(a), -10.7, 8 + 0.6 * sin(a)),
                (1.57 * cos(a), -12.5, 8 + 1.1 * sin(a)),
                (1.43 * cos(a), -15.4, 8 + 1.05 * sin(a)),
                (1.21 * cos(a), -17.6, 7.9 + sin(a)),
            ],
            0.27,
            m["tissue"],
        )
    hindgut = add("hindgut", "hindgut")
    smooth_path(
        "Hindgut coil",
        hindgut,
        [
            (0.28, -19.9, 7.6),
            (-1.1, -21.3, 7.3),
            (-0.9, -23.5, 7.1),
            (1.4, -23.2, 7.5),
            (1.1, -25, 7.7),
            (0, -27.2, 7.4),
            (0, -30.4, 7.1),
        ],
        0.48,
        m["tissue"],
    )
    tubules = add("tubules", "tubules")
    for i in range(6):
        s = -1 if i % 2 else 1
        reach = 3.1 + i * 0.31
        smooth_path(
            "Malpighian tubule",
            tubules,
            [
                (0, -19.9, 7.5),
                (s * 2, -19 - i * 0.27, 7.4),
                (s * reach, -16 + i * 0.7, 7.2),
                (s * (reach - 0.4), -12 + i * 0.87, 7.5),
                (s * 2.6, -15 + i * 0.8, 7.7),
            ],
            0.115,
            m["straw"],
        )
    heart = add("heart", "heart")
    smooth_path(
        "Dorsal vessel",
        heart,
        [
            (0, -28.8, 8.18),
            (0, -23, 9.46),
            (0, -15, 10.1),
            (0, -6, 9.6),
            (0, 0, 10.0),
            (0, 9, 13.4),
            (0, 20, 20.0),
            (0, 25, 23.45),
        ],
        0.24,
        m["muscle"],
    )
    duct = add("oviduct", "oviduct")
    for s, tag, side in ((-1, "l", "Left"), (1, "r", "Right")):
        bead("Optic lobe", brain, (s * 1.60, 27, 20.0), (1.0, 0.6, 0.63), m["nerve"])
        trachea = add("trachea_" + tag, "trachea", side)
        trunk = [
            (s * x, y, z)
            for x, y, z in [
                (2.6, -26, 7.6),
                (4.05, -19, 7.8),
                (4.25, -12, 7.8),
                (3.43, -5, 7.8),
                (2.5, 1.0, 8.5),
                (1.28, 11, 14.36),
                (1.05, 21.2, 20.3),
            ]
        ]
        smooth_path("Air trunk", trachea, trunk, 0.20, m["silk"])
        for x, y, z in trunk[1:-1]:
            for delta in (-1, 1):
                smooth_path(
                    "Air branch",
                    trachea,
                    [
                        (x, y, z),
                        (x * 0.80, y + delta * 0.8, z + 0.37),
                        (x * 0.44, y + delta * 1.65, z + 0.45),
                    ],
                    0.095,
                    m["silk"],
                    6,
                )
        ovary = add("ovary_" + tag, "ovary", side)
        for i in range(4):
            x = s * (1.74 + 0.44 * i)
            smooth_path(
                "Ovariole",
                ovary,
                [
                    (s * 2.1, -24.3, 7.44),
                    (x, -20, 8.05),
                    (x, -14, 8.65),
                    (x * 0.9, -9.3, 8.67),
                ],
                0.18,
                m["yolk"],
            )
            for j in range(5):
                y = -21 + j * 2.1 + i * 0.25
                size = 0.54 - 0.057 * j
                bead(
                    "Developing egg",
                    ovary,
                    (x, y, 8.10 + j * 0.11),
                    (size, 0.84 - 0.07 * j, size),
                    m["yolk"],
                )
        smooth_path(
            "Lateral egg duct",
            duct,
            [(s * 2.13, -23.6, 7.55), (s * 1.8, -25.5, 7.35), (0, -27.3, 6.95)],
            0.25,
            m["tissue"],
        )
    tapered(
        "Common duct",
        duct,
        (0, -27.3, 6.95),
        (0, -30.1, 6.95),
        [0.42, 0.27],
        m["tissue"],
    )


def consolidate(node):
    """Bake static trim into its labelled part, retaining every animated hinge."""
    for holder in [node, *(o for o in node.children_recursive if o.type == "EMPTY")]:
        children = [child for child in holder.children if child.type == "MESH"]
        if len(children) < 2:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        for child in children:
            child.select_set(True)
        bpy.context.view_layer.objects.active = children[0]
        bpy.ops.object.join()


def build(root):
    palette = {
        "jade": "#7eaa49",
        "lime": "#a8bd65",
        "wing": "#85a64e",
        "vein": "#bace83",
        "membrane": "#d0cb9f",
        "abdomen": "#86a45d",
        "belly": "#bdc993",
        "straw": "#cdba77",
        "eye": "#a7ad60",
        "ocellus": "#dec985",
        "smoke": "#343725",
        "ivory": "#e6e5bd",
        "umber": "#735336",
        "tissue": "#d5a889",
        "muscle": "#b97970",
        "silk": "#ddd8b9",
        "nerve": "#dbcaa0",
        "yolk": "#d7b568",
    }
    m = {
        name: material(
            name.title(), color, 0.43 if name in ("wing", "eye", "ocellus") else 0.55
        )
        for name, color in palette.items()
    }
    parts = []
    nodes = []

    def add(pid, kind, side="", parent=None, control=None):
        label, term, system, source, short, detail = NOTES[kind]
        name = side + " " + label.lower() if side else label
        evidence = (
            "Species reference"
            if source in {"museum", "leg", "wing", "mark"}
            else "Comparative reconstruction"
        )
        record = dict(
            id=pid,
            name=name,
            term=term,
            system=system,
            parent=parent,
            source=source,
            evidence=evidence,
            short=short,
            detail=detail,
        )
        if control:
            record["control"] = control
        parts.append(record)
        node = group(pid, root)
        node.scale = (0.90,) * 3
        if kind in {"head", "eye", "ocelli", "antenna", "jaw", "palp", "brain"}:
            node.location.z = 4.5
        nodes.append(node)
        return node

    head_and_thorax(add, m)
    abdomen(add, m)
    for s, tag, side in ((-1, "l", "Left"), (1, "r", "Right")):
        foreleg(add, s, side, m)
        walking(add, s, side, False, m)
        walking(add, s, side, True, m)
        for hind in (False, True):
            kind = "hindwing" if hind else "forewing"
            wing(add(kind + "_" + tag, kind, side), s, hind, m)
        cercus = add("cercus_" + tag, "cercus", side)
        tapered(
            "Tapered cercus",
            cercus,
            (s * 0.90, -28.9, 7.35),
            (s * 1.73, -32.4, 7.6),
            [0.41, 0.33, 0.22, 0.14, 0.04],
            m["straw"],
        )
    internal_organs(add, m)
    for node in nodes:
        consolidate(node)
    # Offsets are relative to the anatomical parent in viewer axes (x, up, rear).
    spread = {
        "head": [0, 8, -8],
        "ocelli": [0, 5, -3],
        "pronotum": [0, 12, -2],
        "chest": [0, 13, 4],
        "back": [0, 17, 5],
        "belly": [0, -14, 4],
        "brain": [0, 4, -6],
        "cord": [0, -8, 0],
        "oesophagus": [-7, 1, -3],
        "crop": [-8, 3, 2],
        "valve": [-4, 2, 4],
        "midgut": [-8, 2, 10],
        "caeca": [-16, 1, 8],
        "hindgut": [-7, -2, 13],
        "tubules": [-16, -5, 13],
        "heart": [0, 8, 4],
        "oviduct": [0, -6, 12],
    }
    for tag, s in (("l", -1), ("r", 1)):
        for name, dx, up, rear in [
            ("eye", 5, 3, -2),
            ("antenna", 5, 6, -2),
            ("jaw", 3, -3, -4),
            ("palp", 6, -2, -5),
            ("coxa", 8, 0, -4),
            ("trochanter", 3, -2, 0),
            ("femur", 4, 2, -2),
            ("tibia", 3, 5, -2),
            ("femoral_spines", 2, -4, 0),
            ("tibial_spines", 2, 4, 0),
            ("forefoot", 2, -4, 0),
            ("flexor", 2, -3, 4),
            ("forewing", 13, 13, 8),
            ("hindwing", 15, 6, 12),
            ("middle", 10, -3, -3),
            ("hind", 11, -3, 5),
            ("cercus", 5, 2, 12),
            ("trachea", 12, 3, 0),
            ("ovary", 10, -2, 9),
        ]:
            spread[name + "_" + tag] = [s * dx, up, rear]
        for kind in ("middle", "hind"):
            spread["foot_" + kind + "_" + tag] = [s * 4, -3, 0]
    return dict(
        id="european-mantis",
        name="European praying mantis",
        scientific="Mantis religiosa",
        stage="Adult female",
        lengthMm=55,
        model="specimen.glb",
        focus="tibia_l",
        title="A leg that folds like a pocketknife",
        overview="Open a grasping leg slowly. Watch the two rows of spines separate as the shin swings away from the thigh.",
        dragHint="Drag a front leg up to open it",
        gestureGuide="Drag either front leg up or outward to open it, then reverse your drag to fold it. Each leg holds its own position.",
        landmarks=["tibia_l", "tibia_r", "head", "forewing_l"],
        spread=spread,
        controls={
            f"tibia_{tag}": {
                "open": f"Open {side} front leg",
                "close": f"Fold {side} front leg",
            }
            for tag, side in (("l", "left"), ("r", "right"))
        },
        systems={k: {"name": v[0], "color": v[1]} for k, v in SYSTEMS.items()},
        parts=parts,
        sources=SOURCES,
        view=dict(
            radius=33,
            target=[0, 11, -2],
            direction=[-1.05, 0.65, -0.77],
            floor=-0.07,
            openingMargin=0.14,
            minFrame=0.75,
            narrowLabelRails=True,
        ),
    )
