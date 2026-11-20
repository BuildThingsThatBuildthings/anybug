"""Procedural adult female Coccinella septempunctata. Coordinates are millimetres."""

import sys
from pathlib import Path
from math import cos, sin, pi
import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).parent))
from brief import LANDMARKS, NOTES, SOURCES, SPREAD, SYSTEMS
from geometry import group, material, mesh, oval, smooth_path, tube


def shell_point(u, v, side):
    t = 0.62 + 2.505 * u
    f = sin(t) ** 0.78
    angle = 0.012 + v * 1.65
    return np.stack(
        (
            side * 2.28 * f * np.sin(angle),
            -0.59 + 3.08 * np.cos(t) + 0 * v,
            0.07 + 1.86 * f * np.cos(angle),
        ),
        axis=-1,
    )


def paint_shell():
    size = 768
    v, u = np.mgrid[0:size, 0:size] / (size - 1)
    t = 0.62 + 2.505 * u
    x = 2.28 * np.sin(t) ** 0.78 * np.sin(0.012 + v * 1.65)
    y = -0.59 + 3.08 * np.cos(t)
    rng = np.random.default_rng(7)
    grain = rng.normal(0, 0.007, (size, size))
    base = np.zeros((size, size, 3))
    warmth = 0.06 * np.sin(t) - 0.07 * v + grain
    for i, c in enumerate((0.70, 0.13, 0.048)):
        base[:, :, i] = c + warmth * (0.85, 0.55, 0.37)[i]

    def patch(cx, cy, rx, ry, color):
        distance = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
        alpha = np.clip((1 - distance) * 24, 0, 1)[:, :, None]
        base[:] = (
            base * (1 - alpha) + (np.array(color) + grain[:, :, None] * 0.45) * alpha
        )

    # Three lateral spots on each elytron, plus a basal spot shared across the suture.
    for spot in [
        (0, 1.55, 0.41, 0.47),
        (1.63, 0.60, 0.32, 0.51),
        (0.98, -1.08, 0.37, 0.46),
        (1.59, -2.05, 0.27, 0.39),
    ]:
        patch(*spot, (0.059, 0.055, 0.048))
    patch(0.60, 1.68, 0.19, 0.28, (0.89, 0.84, 0.68))
    # Minute punctures occur across the shell and through the markings.
    for py, px in rng.integers(2, size - 3, size=(2800, 2)):
        base[py : py + 2, px : px + 2] *= 0.86
        base[py + 2, px : px + 2] *= 1.025
    rgba = np.ones((size, size, 4), dtype=np.float32)
    rgba[:, :, :3] = np.clip(base, 0, 1)
    img = bpy.data.images.new("Elytral pigment and punctures", size, size, alpha=False)
    img.pixels.foreach_set(rgba.ravel())
    img.pack()
    mat = material("Lacquered red cuticle", "#b82d14", 0.38)
    bs = mat.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Coat Weight"].default_value = 0.12
    bs.inputs["Coat Roughness"].default_value = 0.33
    tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = img
    mat.node_tree.links.new(tex.outputs["Color"], bs.inputs["Base Color"])
    return mat


def pigmented_cap(part, name, center, radii, cheek=False):
    """Bake ivory patches onto a continuous curved surface."""
    size = 384
    v, u = np.mgrid[0:size, 0:size] / (size - 1)
    phi = 2 * pi * u
    theta = pi * (1 - v)
    xx = np.abs(np.sin(theta) * np.cos(phi))
    yy = np.sin(theta) * np.sin(phi)
    zz = np.cos(theta)
    rng = np.random.default_rng(19)
    field = ((xx - (0.57 if cheek else 0.75)) / 0.26) ** 2 + ((yy - 0.54) / 0.45) ** 2
    pigment = np.clip((1 - field) * 17, 0, 1) * np.clip((zz + 0.04) * 10, 0, 1)
    rgb = (
        np.array([0.095, 0.09, 0.072])
        + (np.array([0.91, 0.87, 0.72]) - np.array([0.095, 0.09, 0.072]))
        * pigment[:, :, None]
    )
    rgba = np.ones((size, size, 4), dtype=np.float32)
    rgba[:, :, :3] = np.clip(rgb + rng.normal(0, 0.006, (size, size, 1)), 0, 1)
    image = bpy.data.images.new(name + " pigment", size, size, alpha=False)
    image.pixels.foreach_set(rgba.ravel())
    image.pack()
    mat = material(name + " patterned cuticle", "#231f19", 0.35)
    tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = image
    mat.node_tree.links.new(
        tex.outputs["Color"],
        mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"],
    )
    rows, cols = 28, 64
    vertices = []
    faces = []
    for j in range(rows + 1):
        angle = pi * (1 - j / rows)
        for i in range(cols + 1):
            az = 2 * pi * i / cols
            vertices.append(
                (
                    center[0] + radii[0] * sin(angle) * cos(az),
                    center[1] + radii[1] * sin(angle) * sin(az),
                    center[2] + radii[2] * cos(angle),
                )
            )
            if j < rows and i < cols:
                a = j * (cols + 1) + i
                faces.append((a, a + 1, a + cols + 2, a + cols + 1))
    obj = mesh(name, part, vertices, faces, mat)
    uv = obj.data.uv_layers.new(name="Pigment coordinates")
    for loop in obj.data.loops:
        j, i = divmod(loop.vertex_index, cols + 1)
        uv.data[loop.index].uv = (i / cols, j / rows)


def elytron(part, side, mat):
    origin = Vector((side * 0.45, 1.69, 0.60))
    part.location = origin
    rows, cols = 62, 36
    positions, faces = [], []
    for i in range(rows + 1):
        for j in range(cols + 1):
            xyz = shell_point(i / rows, j / cols, side)
            positions.append(Vector(xyz) - origin)
            a = i * (cols + 1) + j
            if i < rows and j < cols:
                face = (a, a + cols + 1, a + cols + 2, a + 1)
                faces.append(face if side == 1 else face[::-1])
    skin = mesh("Curved spotted cuticle", part, positions, faces, mat)
    uv = skin.data.uv_layers.new(name="Pigment coordinates")
    for loop in skin.data.loops:
        i, j = divmod(loop.vertex_index, cols + 1)
        uv.data[loop.index].uv = (i / rows, j / cols)
    # A rounded lip around the open edge gives the forewing visible thickness.
    seam = [positions[i * (cols + 1)] for i in range(rows + 1)]
    tube(
        "Sutural edge", part, seam, 0.008, material("Suture " + str(side), "#4a251d"), 6
    )
    for frame, amount in [(1, 0), (49, 1)]:
        part.rotation_euler = (
            -0.89 * amount,
            -side * 0.23 * amount,
            side * 0.55 * amount,
        )
        part.keyframe_insert(data_path="rotation_euler", frame=frame)


def flight_wing(part, side):
    part.location = (side * 0.75, 1.09, 1.22)
    membrane = material("Amber membrane " + str(side), "#c5a77a", 0.36)
    membrane.diffuse_color = (0.66, 0.49, 0.28, 0.66)
    membrane.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.68
    vein = material("Sclerotized wing veins " + str(side), "#685039", 0.46)
    n, m = 40, 14

    def surface(openness):
        vertices = []
        x = y = 0
        for i in range(n + 1):
            t = i / n
            section = min(3, int(t * 4))
            closed = [0.12, 0.09, 2.93, -0.20][section]
            spread = [1.44, 1.32, 1.21, 1.03][section]
            angle = closed + (spread - closed) * openness
            if i:
                x += 0.14 * sin(angle)
                y -= 0.14 * cos(angle)
            width = (0.19 + 1.66 * sin(pi * t) ** 0.72) * (1 - 0.86 * t**8)
            for j in range(m + 1):
                q = j / m
                vertices.append(
                    (
                        side
                        * (
                            x
                            + 0.24 * width * (q - 0.45) * (1 - openness)
                            + cos(angle) * width * (q - 0.45) * openness
                        ),
                        y - sin(angle) * width * q * openness,
                        0.041 * section * (1 - openness)
                        + 0.075 * sin(pi * t)
                        + 0.07 * sin(q * pi)
                        + 0.54 * t * openness,
                    )
                )
        return vertices

    faces = []
    for i in range(n):
        for j in range(m):
            a = i * (m + 1) + j
            face = (a, a + m + 1, a + m + 2, a + 1)
            faces.append(face if side > 0 else face[::-1])
    wing = mesh("Pleated membrane", part, surface(0), faces, membrane)
    wing.data.materials.append(vein)
    for face in wing.data.polygons:
        i, j = divmod(face.index, m)
        if (
            j in (0, m - 1)
            or j == int(3 + i * 0.14) % m
            or (i > 17 and j == int(12 - (i - 17) * 0.31))
        ):
            face.material_index = 1
    wing.shape_key_add(name="Packed")
    for k in range(1, 9):
        key = wing.shape_key_add(name=f"Unfold {k}/8")
        for vertex, xyz in zip(key.data, surface(k / 8)):
            vertex.co = xyz
        for frame, value in [
            (1, 0),
            (1 + 6 * (k - 1), 0),
            (1 + 6 * k, 1),
            (min(49, 1 + 6 * (k + 1)), 0 if k < 8 else 1),
        ]:
            key.value = value
            key.keyframe_insert(data_path="value", frame=frame)


def build(root):
    parts = []
    outer = material("Obsidian cuticle", "#211e19", 0.32)
    limb = material("Dark warm limbs", "#3b291d", 0.40)
    claw = material("Amber joints", "#93623c", 0.42)
    eye_mat = material("Faceted eyes", "#19191a", 0.32)
    chitin = material("Chestnut abdominal cuticle", "#594029", 0.48)
    paint = paint_shell()

    def part(pid, kind, side="", parent=None):
        label, term, system, source, short, deep = NOTES[kind]
        name = f"{side} {label.lower()}" if side else label
        evidence = (
            "Species reference"
            if source in ("uc", "fold", "bell", "gut")
            else "Comparative reconstruction"
        )
        if kind == "muscle":
            evidence = "Comparative reconstruction"
        parts.append(
            dict(
                id=pid,
                name=name,
                term=term,
                system=system,
                parent=parent,
                source=source,
                evidence=evidence,
                short=short,
                detail=deep,
            )
        )
        return group(pid, root)

    head = part("head", "head")
    pigmented_cap(head, "Cranium", (0, 2.50, 0.46), (0.88, 0.70, 0.50), True)
    shield = part("pronotum", "thorax")
    pigmented_cap(shield, "Pronotal shield", (0, 1.67, 0.60), (1.58, 0.90, 0.76))
    back = part("tergites", "back")
    belly = part("sternites", "belly")
    # Separate thin dorsal and ventral arcs leave an actual open body cavity.
    for j in range(7):
        y = 0.76 - 0.59 * j
        width = 1.86 * max(0.32, sin(pi * (j + 1) / 8.9) ** 0.38)
        for obj, sgn, base, h, mat in (
            (back, 1, 0.16, 1.00, chitin),
            (belly, -1, 0.05, 0.46, limb),
        ):
            verts, faces = [], []
            for k in range(4):
                for i in range(25):
                    a = pi * i / 24
                    verts.append(
                        (
                            width * cos(a),
                            y + k * 0.172,
                            base
                            + sgn * h * sin(a) * width / 1.86
                            + 0.025 * sin(k * pi / 3),
                        )
                    )
                    if k and i:
                        b = k * 25 + i
                        faces.append((b - 26, b - 25, b, b - 1))
            mesh("Overlapping abdominal plate", obj, verts, faces, mat)
    for s, word, key in [(-1, "Left", "l"), (1, "Right", "r")]:
        elytron(part("cover_" + key, "cover", word), s, paint)
        flight_wing(part("wing_" + key, "wing", word), s)
        eye = part("eye_" + key, "eye", word, "head")
        oval(
            "Eye dome",
            eye,
            (s * 0.77, 2.65, 0.60),
            (0.245, 0.365, 0.277),
            eye_mat,
            32,
            20,
        )
        for row in range(6):
            for col in range(8):
                a = 0.38 + row * 0.38
                b = -1.12 + col * 0.31 + (row % 2) * 0.09
                loc = (
                    s * (0.77 + 0.258 * sin(a) * cos(b)),
                    2.65 + 0.378 * sin(a) * sin(b),
                    0.60 + 0.289 * cos(a),
                )
                oval("Ommatidial facet", eye, loc, (0.018, 0.021, 0.019), eye_mat, 8, 4)
        antenna = part("antenna_" + key, "antenna", word, "head")
        for i in range(11):
            t = i / 10
            loc = (
                s * (0.55 + 0.71 * t),
                3.00 + 0.91 * t - 0.20 * t * t,
                0.46 + 0.27 * t - 0.13 * sin(pi * t),
            )
            radius = 0.068 + 0.049 * max(0, (t - 0.64) / 0.36)
            oval(
                "Antennal article",
                antenna,
                loc,
                (radius, 0.093, radius * 0.83),
                claw if i in (0, 1) else limb,
                14,
                8,
            )
        jaw = part("jaw_" + key, "jaw", word, "head")
        tube(
            "Curved mandible",
            jaw,
            [
                (s * 0.31, 3.04, 0.26),
                (s * 0.34, 3.31, 0.20),
                (s * 0.22, 3.41, 0.18),
                (s * 0.12, 3.39, 0.17),
            ],
            [0.13, 0.12, 0.07, 0.013],
            limb,
        )
        palp = part("palp_" + key, "palp", word, "head")
        tube(
            "Palpal shaft",
            palp,
            [(s * 0.45, 2.96, 0.19), (s * 0.63, 3.28, 0.12), (s * 0.66, 3.48, 0.16)],
            [0.07, 0.065, 0.045],
            claw,
        )
        oval("Palp tip", palp, (s * 0.67, 3.50, 0.16), (0.08, 0.115, 0.065), limb)
        for n, (at, offset, label) in enumerate(
            [(1.57, 0.70, "front"), (0.71, -0.05, "middle"), (-0.26, -0.90, "rear")]
        ):
            legid = f"leg_{key}{n}"
            leg = part(legid, "leg", word + " " + label)
            foot = part(f"foot_{key}{n}", "foot", word + " " + label, legid)
            hip = (s * 0.86, at, -0.03)
            knee = (s * (1.91 + 0.11 * n), at + offset * 0.52, 0.10)
            ankle = (s * (2.35 + 0.13 * n), at + offset - 0.13, -0.41)
            toe = (s * (2.72 + 0.12 * n), at + offset + 0.03, -0.48)
            tube(
                "Muscular femur",
                leg,
                [hip, ((hip[0] + knee[0]) * 0.5, (hip[1] + knee[1]) * 0.5, 0.02), knee],
                [0.10, 0.165, 0.10],
                limb,
                12,
            )
            tube("Tapered tibia", leg, [knee, ankle], [0.078, 0.054], limb)
            oval("Knee articulation", leg, knee, (0.117, 0.11, 0.10), outer, 14, 8)
            for k in range(4):
                p = Vector(ankle).lerp(Vector(toe), k / 4)
                q = Vector(ankle).lerp(Vector(toe), (k + 1) / 4)
                tube("Tarsal article", foot, [p, q], [0.072 - k * 0.006, 0.052], claw)
            for d in (-1, 1):
                tube(
                    "Terminal claw",
                    foot,
                    [
                        toe,
                        (toe[0] + s * 0.105, toe[1] + d * 0.05, -0.45),
                        (toe[0] + s * 0.14, toe[1] + d * 0.08, -0.51),
                    ],
                    [0.032, 0.024, 0.006],
                    limb,
                )
    internals(root, part)
    return dict(
        id="seven-spot",
        name="Seven-spotted ladybug",
        scientific="Coccinella septempunctata",
        stage="Adult female",
        lengthMm=7,
        model="specimen.glb",
        focus="cover_l",
        landmarks=LANDMARKS,
        spread=SPREAD,
        title="Beneath the spots",
        overview="Lift a spotted wing cover to discover the folded flight wing underneath.",
        controls={
            f"cover_{s}": {"open": "Lift cover", "close": "Lower cover"}
            for s in ("l", "r")
        }
        | {
            f"wing_{s}": {
                "open": "Unfold wing",
                "close": "Fold wing",
                "requires": f"cover_{s}",
            }
            for s in ("l", "r")
        },
        systems={k: {"name": v[0], "color": v[1]} for k, v in SYSTEMS.items()},
        sources=SOURCES,
        parts=parts,
        view=dict(radius=4, target=[0, 0.50, 0], direction=[-0.81, 0.93, -1.20]),
    )


def internals(root, part):
    def tissue(pid, kind, color, side=""):
        return part(pid, kind, side), material("Natural " + pid, color, 0.51)

    obj, mat = tissue("foregut", "foregut", "#c9ab80")
    smooth_path(
        "Oesophagus",
        obj,
        [
            (0, 3.19, 0.30),
            (0, 2.49, 0.47),
            (0, 1.70, 0.37),
            (0.15, 0.96, 0.44),
            (0.22, 0.57, 0.49),
        ],
        0.108,
        mat,
    )
    obj, mat = tissue("gizzard", "gizzard", "#d3bc85")
    oval("Muscular proventriculus", obj, (0.22, 0.57, 0.49), (0.19, 0.24, 0.18), mat)
    obj, mat = tissue("midgut", "midgut", "#c1a465")
    smooth_path(
        "Midgut loop",
        obj,
        [
            (0.22, 0.57, 0.49),
            (0.68, 0.11, 0.51),
            (0.69, -0.65, 0.48),
            (0.16, -1.06, 0.44),
            (-0.51, -1.37, 0.52),
            (-0.56, -2.09, 0.46),
            (0.14, -2.38, 0.39),
            (0.56, -1.88, 0.41),
        ],
        0.193,
        mat,
        12,
    )
    obj, mat = tissue("hindgut", "hindgut", "#b89a74")
    smooth_path(
        "Hindgut to rectum",
        obj,
        [
            (0.56, -1.88, 0.41),
            (0.33, -1.50, 0.48),
            (-0.06, -1.66, 0.34),
            (-0.13, -2.35, 0.22),
            (0, -3.11, 0.16),
        ],
        0.111,
        mat,
    )
    obj, mat = tissue("rectum", "rectum", "#c1ad8b")
    oval("Rectal chamber", obj, (-0.025, -2.95, 0.18), (0.15, 0.23, 0.114), mat)
    obj, mat = tissue("malpighian", "tubules", "#dbc89b")
    for s in (-1, 1):
        for j in range(3):
            w = 0.72 + j * 0.14
            smooth_path(
                "Tubule loop",
                obj,
                [
                    (0.54, -1.86, 0.4),
                    (s * w, -1.08, 0.31 + j * 0.09),
                    (s * (w + 0.20), -0.79, 0.41 + j * 0.09),
                    (s * (w + 0.3), -1.58, 0.51),
                    (s * w, -2.58, 0.37),
                    (s * 0.16, -2.80, 0.20),
                ],
                0.031,
                mat,
            )
    air, mat = tissue("airways", "tracheae", "#d9cdb3")
    pores, pmat = tissue("spiracles", "spiracles", "#745036")
    for s in (-1, 1):
        anchors = []
        for i in range(7):
            y = 1.38 - i * 0.63
            x = s * (0.98 + 0.44 * sin(pi * i / 7))
            anchors.append((x, y, 0.26))
            end = (x * 1.18, y, 0.12)
            tube("Spiracular connection", air, [(x, y, 0.26), end], [0.035, 0.045], mat)
            oval("Spiracular rim", pores, end, (0.065, 0.105, 0.065), pmat, 14, 8)
            for j in (-1, 1):
                smooth_path(
                    "Tracheal branch",
                    air,
                    [
                        (x, y, 0.26),
                        (x * 0.80, y + 0.08 * j, 0.44),
                        (x * 0.58, y + 0.21 * j, 0.52),
                    ],
                    0.023,
                    mat,
                    6,
                )
        smooth_path("Lateral tracheal trunk", air, anchors, 0.059, mat)
    obj, mat = tissue("dorsal_vessel", "heart", "#bc9d83")
    pts = [
        (0, 2.33, 0.86),
        (0, 1.1, 1.03),
        (0, 0.28, 1.08),
        (0, -0.57, 1.12),
        (0, -1.30, 1.02),
        (0, -2.02, 0.88),
        (0, -2.71, 0.61),
    ]
    smooth_path("Aorta and heart", obj, pts, 0.068, mat)
    for i in range(2, len(pts)):
        oval("Abdominal heart chamber", obj, pts[i], (0.101, 0.20, 0.088), mat, 16, 10)
    obj, mat = tissue("brain", "brain", "#cbbca2")
    for s in (-1, 1):
        oval("Brain hemisphere", obj, (s * 0.19, 2.46, 0.65), (0.28, 0.31, 0.22), mat)
        oval("Optic lobe", obj, (s * 0.49, 2.48, 0.62), (0.18, 0.19, 0.15), mat)
        smooth_path(
            "Peri-oesophageal connective",
            obj,
            [(s * 0.18, 2.53, 0.57), (s * 0.23, 2.58, 0.35), (s * 0.10, 2.41, 0.19)],
            0.045,
            mat,
        )
    obj, mat = tissue("nerve_cord", "cord", "#d8c9a9")
    for s in (-1, 1):
        smooth_path(
            "Longitudinal connective",
            obj,
            [
                (s * 0.04, 2.44, 0.17),
                (s * 0.045, 1.38, 0.08),
                (s * 0.05, 0.20, -0.06),
                (s * 0.04, -1.10, -0.13),
                (s * 0.04, -2.42, -0.04),
            ],
            0.032,
            mat,
        )
    for y, z in [
        (2.38, 0.16),
        (1.36, 0.075),
        (0.50, -0.02),
        (-0.44, -0.09),
        (-1.36, -0.12),
        (-2.25, -0.05),
    ]:
        oval("Ganglion", obj, (0, y, z), (0.14, 0.17, 0.08), mat, 18, 10)
    obj, mat = tissue("flight_muscles", "muscle", "#ad785e")
    for s in (-1, 1):
        for j in range(5):
            o = oval(
                "Longitudinal flight bundle",
                obj,
                (s * (0.45 + j * 0.17), 0.87, 0.66),
                (0.103, 0.61 - j * 0.035, 0.18),
                mat,
                18,
                12,
            )
            o.rotation_euler = (0.15, s * 0.18, s * 0.08)
    for s, word, k in [(-1, "Left", "l"), (1, "Right", "r")]:
        obj, mat = tissue("ovary_" + k, "ovary", "#d3b576", word)
        for j in range(4):
            x = s * (0.51 + j * 0.16)
            smooth_path(
                "Ovariole",
                obj,
                [(x, -0.57, 0.45), (x, -1.23, 0.66), (s * 0.70, -2.05, 0.42)],
                0.039,
                mat,
            )
            for i in range(3):
                oval(
                    "Developing follicle",
                    obj,
                    (x, -0.74 - i * 0.34, 0.55 + 0.065 * sin(j)),
                    (0.071 + i * 0.018, 0.13 + i * 0.019, 0.087 + i * 0.009),
                    mat,
                    16,
                    10,
                )
    obj, mat = tissue("oviduct", "oviduct", "#c6b49a")
    for s in (-1, 1):
        smooth_path(
            "Lateral oviduct",
            obj,
            [(s * 0.72, -1.95, 0.43), (s * 0.57, -2.40, 0.32), (0, -2.76, 0.10)],
            0.057,
            mat,
        )
    tube(
        "Common oviduct", obj, [(0, -2.76, 0.10), (0, -3.04, 0.03)], [0.078, 0.06], mat
    )
    obj, mat = tissue("fat_body", "fat", "#dbc69b")
    for s in (-1, 1):
        for i in range(13):
            t = i / 12
            oval(
                "Fat body lobule",
                obj,
                (
                    s * (1.00 + 0.38 * sin(pi * t)),
                    -0.43 - 2.12 * t,
                    0.39 + 0.10 * sin(2 * i),
                ),
                (0.175, 0.17, 0.105),
                mat,
                14,
                9,
            )
