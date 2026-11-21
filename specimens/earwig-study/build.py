"""Adult male earwig authored in Blender. X is lateral, Y headward and Z up, in mm."""

import sys
from pathlib import Path
from math import cos, sin, pi

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).parent))
from geometry import group, material, oval, smooth_path, tube
from surfaces import plate, pigmented, spindle, forceps, antenna, tegmen, walking_leg
from internal import build_interior, SPECIES, COMPARATIVE

PHOTO = "Visible in reference photograph"
SOURCES = {
    "photo": [
        "Jack Kelly Clark · UC IPM adult male on fruit",
        "https://ipm.ucanr.edu/PMG/F/I-DM-FAUR-AD.005.html",
    ],
    "adult": [
        "University of Florida · European earwig",
        "https://ask.ifas.ufl.edu/publication/IN875",
    ],
    "head": [
        "Neubert et al. · Head anatomy, figures 1–14",
        "https://www.senckenberg.de/wp-content/uploads/2019/07/04_asp_75_1_neubert_99-124.pdf",
    ],
    "gut": [
        "Lhoste · Dissected digestive tract, figure 1",
        "https://doi.org/10.3406/bsef.1941.15490",
    ],
    "air": [
        "Herhold et al. · Earwig tracheal CT, figures 47–49",
        "https://zenodo.org/records/7733234",
    ],
    "repro": [
        "Popham · Reproductive organs of the common earwig",
        "https://doi.org/10.1111/j.1469-7998.1965.tb05198.x",
    ],
    "male": [
        "Hudson · Male anatomy, figure 16",
        "https://doi.org/10.1080/03036758.1973.10430603",
    ],
    "glands": [
        "Eisner · Adult tergal gland location and outlets",
        "https://groups.csail.mit.edu/mac/projects/psyche/67/67-062.html",
    ],
    "nerve": [
        "NC State · Insect nervous system",
        "https://genent.cals.ncsu.edu/nervous/",
    ],
    "heart": [
        "NC State · Insect circulatory system",
        "https://genent.cals.ncsu.edu/bug-bytes/circulatory-system/",
    ],
    "fat": [
        "Arrese & Soulages · Insect fat body and storage",
        "https://doi.org/10.1146/annurev-ento-112408-085356",
    ],
}
SYSTEMS = {
    k: {"name": n, "color": c}
    for k, n, c in [
        ("exterior", "Exterior", "#795037"),
        ("digestive", "Digestion", "#e49b4c"),
        ("excretory", "Waste removal", "#ae9534"),
        ("respiratory", "Breathing", "#389c99"),
        ("circulatory", "Circulation", "#d45d64"),
        ("nervous", "Nerves and senses", "#9674b6"),
        ("muscular", "Muscles", "#ba7177"),
        ("reproductive", "Reproduction", "#779a5e"),
        ("storage", "Energy reserves", "#c8a150"),
        ("glandular", "Defensive glands", "#567ea8"),
        ("support", "Internal supports", "#b9a178"),
    ]
}


def consolidate(node):
    """Join trim within each hinge to keep the display mesh count per part low."""
    for holder in [node, *(o for o in node.children_recursive if o.type == "EMPTY")]:
        children = [o for o in holder.children if o.type == "MESH"]
        if len(children) < 2:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        for o in children:
            o.select_set(True)
        bpy.context.view_layer.objects.active = children[0]
        bpy.ops.object.join()


def build(root):
    palette = {
        "cuticle": "#ffffff",
        "wing": "#ffffff",
        "cercus": "#ffffff",
        "brown": "#362321",
        "russet": "#603923",
        "rim": "#a47642",
        "vein": "#644935",
        "eye": "#231a1b",
        "facet": "#49342d",
        "amber": "#a47241",
        "leg": "#ccab74",
        "hair": "#9d7148",
        "membrane": "#c8af83",
        "joint": "#71543e",
        "gut": "#bc9071",
        "crop": "#d5b99a",
        "fold": "#c49d78",
        "gizzard": "#ab7a60",
        "stomach": "#c69868",
        "air": "#d8d6ba",
        "muscle": "#bb8275",
        "testis": "#d8c9ab",
        "duct": "#cdc0a5",
        "tubule": "#c5af74",
        "nerve": "#d7bd87",
        "fat": "#d3ba7a",
        "vessel": "#b48c85",
        "gland": "#b3ad82",
        "bone": "#ab8f67",
    }
    m = {
        k: material(
            k.title(), c, 0.30 if k in {"cuticle", "wing", "cercus", "eye"} else 0.53
        )
        for k, c in palette.items()
    }
    for key in ["cuticle", "wing", "cercus"]:
        pigmented(m[key])
    parts = []
    nodes = []
    spread = {}
    controls = {}

    def add(key, name, term, system, source, evidence, short, detail, parent, offset):
        node = group(key, root)
        nodes.append(node)
        spread[key] = offset
        parts.append(
            dict(
                id=key,
                name=name,
                term=term,
                system=system,
                source=source,
                evidence=evidence,
                short=short,
                detail=detail,
                parent=parent,
            )
        )
        return node

    def outer(
        key, name, term, source, evidence, short, detail, parent=None, offset=(0, 0, 0)
    ):
        return add(
            key,
            name,
            term,
            "exterior",
            source,
            evidence,
            short,
            detail,
            parent,
            list(offset),
        )

    def warm(y, a, inset):
        light = 0.023 * (1 + sin(8 * a + 0.6 * y)) + 0.010 * (1 + sin(15 * a + 3 * y))
        return (0.204 + light, 0.108 + light * 0.70, 0.078 + light * 0.5)

    head = outer(
        "head",
        "Head capsule",
        "Cranium",
        "head",
        SPECIES,
        "The jaws point forward from the head.",
        "The dorsal seams form a branching pattern. The eyes lie laterally and the antennae attach in front of them.",
        offset=(0, 1, -2.8),
    )
    plate(
        "Head_capsule",
        head,
        [
            (4.22, 0, 1.32, 0.52, 0.27),
            (4.40, 0, 1.36, 0.78, 0.36),
            (4.73, 0, 1.38, 0.99, 0.44),
            (5.18, 0, 1.39, 1.02, 0.47),
            (5.55, 0, 1.35, 0.88, 0.39),
            (5.90, 0, 1.27, 0.69, 0.31),
            (6.05, 0, 1.25, 0.47, 0.21),
        ],
        m["cuticle"],
        warm,
    )
    for s in [-1, 1]:
        smooth_path(
            "SM_Frontal_suture",
            head,
            [
                (0, 4.51, 1.72),
                (0, 4.84, 1.81),
                (s * 0.12, 5.05, 1.846),
                (s * 0.43, 5.30, 1.784),
                (s * 0.57, 5.53, 1.66),
            ],
            0.016,
            m["brown"],
            6,
        )
    lip = outer(
        "labrum",
        "Upper lip",
        "Labrum",
        "head",
        SPECIES,
        "The upper lip lies in front of the head.",
        "The broad plate sits above the cutting edges of the mandibles.",
        "head",
        (0, 0.4, -1.05),
    )
    plate(
        "Labrum",
        lip,
        [
            (5.81, 0, 1.28, 0.45, 0.12),
            (5.99, 0, 1.26, 0.56, 0.13),
            (6.19, 0, 1.24, 0.46, 0.095),
            (6.25, 0, 1.23, 0.27, 0.064),
        ],
        m["russet"],
    )
    chest = outer(
        "chest",
        "Leg-bearing thorax",
        "Thoracic cuticle",
        "adult",
        SPECIES,
        "The legs attach to three chest segments.",
        "The front shield and the short forewings lift or separate from this support.",
        offset=(0, -0.85, -0.6),
    )
    plate(
        "Thorax",
        chest,
        [
            (0.23, 0, 1.20, 1.10, 0.46),
            (0.83, 0, 1.22, 1.19, 0.49),
            (2.12, 0, 1.25, 1.16, 0.49),
            (3.45, 0, 1.26, 1.02, 0.47),
            (4.26, 0, 1.28, 0.75, 0.40),
            (4.42, 0, 1.32, 0.78, 0.40),
        ],
        m["brown"],
    )
    shield = outer(
        "shield",
        "Front shield",
        "Pronotum",
        "photo",
        PHOTO,
        "A pale rim outlines the shield behind the head.",
        "Its broad dark disc has rounded rear corners and a fine median line.",
        "chest",
        (0, 1.9, -0.8),
    )
    shield_rows = [
        (2.43, 0, 1.42, 0.66, 0.19),
        (2.54, 0, 1.44, 0.98, 0.27),
        (2.89, 0, 1.46, 1.08, 0.32),
        (3.73, 0, 1.43, 1.07, 0.33),
        (4.04, 0, 1.40, 1.0, 0.28),
        (4.12, 0, 1.39, 0.88, 0.23),
    ]

    def shield_color(y, a, i):
        edge = max(0, (abs(cos(a)) - 0.68) / 0.32)
        return (0.235 + 0.36 * edge, 0.147 + 0.27 * edge, 0.122 + 0.14 * edge)

    plate("Pronotal_disc", shield, shield_rows, m["cuticle"], shield_color)
    smooth_path(
        "SM_Pronotal_midline",
        shield,
        [(0, 2.61, 1.72), (0, 2.95, 1.79), (0, 3.72, 1.77), (0, 3.98, 1.71)],
        0.011,
        m["vein"],
        6,
    )

    belly = outer(
        "sternites",
        "Abdominal belly plates",
        "Sternites",
        "adult",
        SPECIES,
        "A row of plates protects the underside.",
        "The ventral plates meet flexible cuticle along the sides.",
        offset=(0, -2.5, 0.2),
    )
    for i in range(10):
        y = 1.15 - 0.685 * i
        width = 1.13 + 0.38 * sin(pi * (i + 0.6) / 11) - 0.19 * (i / 9) ** 5
        depth = 0.46 + 0.14 * sin(pi * (i + 0.6) / 11)
        z = 1.17 + 0.04 * sin(pi * i / 9)
        rows = [
            (y - 0.48, 0, z, width * 0.984, depth * 0.975),
            (y - 0.42, 0, z, width * 1.007, depth),
            (y - 0.22, 0, z, width, depth * 1.035),
            (y + 0.08, 0, z, width * 0.98, depth * 0.97),
            (y + 0.30, 0, z, width * 0.959, depth * 0.94),
        ]
        back = outer(
            "tergite_" + str(i + 1),
            "Abdominal back plate " + str(i + 1),
            "Abdominal tergite",
            "adult",
            SPECIES,
            "This plate overlaps the next section of abdomen.",
            "Its thin posterior lip and the flexible cuticle beneath allow the long abdomen to bend.",
            offset=(0, 1.1 + i * 0.11, (i - 4) * 0.34),
        )

        def band(ypos, a, inner):
            t = (ypos - y + 0.48) / 0.78
            edge = 0.12 * max(0, 1 - t * 6)
            flank = 0.033 * abs(cos(a)) ** 3
            return (
                0.128 + edge + flank + 0.014 * sin(i * 1.8),
                0.085 + edge * 0.53 + flank * 0.52,
                0.080 + edge * 0.31 + flank * 0.34,
            )

        plate("Tergal_shell", back, rows, m["cuticle"], band, arc=(-0.22, pi + 0.22))
        plate("Sternal_shell", belly, rows, m["russet"], arc=(pi + 0.10, 2 * pi - 0.10))
        for s in [-1, 1]:
            for k in range(3):
                p = Vector(
                    (
                        s * width * (0.82 + 0.05 * k),
                        y - 0.38 + 0.07 * k,
                        z + depth * (0.52 - 0.08 * k),
                    )
                )
                tube(
                    "SM_Marginal_seta",
                    back,
                    [p, p + Vector((s * 0.034, -0.095 - 0.02 * k, 0.052))],
                    [0.008, 0.0015],
                    m["hair"],
                    5,
                )
    tail = outer(
        "terminal",
        "Tail bearing plate",
        "Terminal abdominal plate",
        "male",
        SPECIES,
        "The curved pincers sit on either side of the tail.",
        "The broad basal sockets carry the forceps. Their dark margins frame the small central terminal structures.",
        offset=(0, 0.2, 1.6),
    )
    plate(
        "Terminal_sclerite",
        tail,
        [
            (-5.88, 0, 1.04, 0.48, 0.24),
            (-5.56, 0, 1.13, 0.87, 0.31),
            (-5.22, 0, 1.16, 0.99, 0.36),
        ],
        m["cuticle"],
        warm,
    )
    for s, side, tag in [(-1, "Left", "l"), (1, "Right", "r")]:

        def p(key, label, term, src, ev, short, detail, parent, off):
            return outer(
                key + "_" + tag,
                side + " " + label,
                term,
                src,
                ev,
                short,
                detail,
                parent,
                (s * off[0], off[1], off[2]),
            )

        eye = p(
            "eye",
            "compound eye",
            "Compound eye",
            "head",
            SPECIES,
            "Hundreds of facets sample the scene.",
            "The exposed surface is a small oval on the side of the head. Facet density is illustrative.",
            "head",
            (1.3, 0.5, -0.35),
        )
        center = Vector((s * 0.921, 5.12, 1.45))
        oval("SM_Corneal_dome", eye, center, (0.18, 0.34, 0.22), m["eye"], 22, 12)
        for row in range(-3, 4):
            for col in range(-4, 5):
                v = row / 3.9
                u = (col + 0.48 * (row % 2)) / 5.15
                if u * u + v * v > 0.87:
                    continue
                q = center + Vector(
                    (s * 0.18 * (1 - u * u - v * v) ** 0.5, u * 0.34, v * 0.22)
                )
                oval(
                    "SM_Ommatidial_facet",
                    eye,
                    q,
                    (0.018, 0.032, 0.028),
                    m["facet"] if (col + row) % 7 == 0 else m["eye"],
                    8,
                    5,
                )
        node = p(
            "antenna",
            "feeler",
            "Antenna",
            "adult",
            SPECIES,
            "The long feeler has fourteen jointed segments.",
            "The thick basal segment supports a slender flagellum with sensory hairs.",
            "head",
            (1.25, 0.55, -1.5),
        )
        antenna(node, s, m)
        jaw = p(
            "jaw",
            "jaw",
            "Mandible",
            "head",
            SPECIES,
            "The jaw grips and cuts food.",
            "The mesal edge bears teeth and the broader basal region processes food.",
            "head",
            (0.85, -0.55, -0.95),
        )
        tube(
            "SM_Mandible",
            jaw,
            [
                (s * 0.54, 5.70, 1.18),
                (s * 0.51, 6.02, 1.14),
                (s * 0.43, 6.22, 1.15),
                (s * 0.19, 6.38, 1.19),
            ],
            [0.168, 0.194, 0.124, 0.018],
            m["russet"],
            12,
        )
        for k in range(3):
            tube(
                "SM_Incisor",
                jaw,
                [
                    (s * (0.42 - 0.043 * k), 6.15 + 0.057 * k, 1.16),
                    (s * (0.28 - 0.044 * k), 6.23 + 0.052 * k, 1.18),
                ],
                [0.051, 0.006],
                m["brown"],
                7,
            )
        palp = p(
            "palp",
            "mouth feeler",
            "Maxillary palp",
            "head",
            SPECIES,
            "This small feeler explores food near the jaws.",
            "The terminal segment carries sensory structures. Segments are grouped as one selectable palp.",
            "head",
            (0.9, -0.75, -1.15),
        )
        points = [
            (s * 0.48, 5.62, 1.11),
            (s * 0.74, 5.72, 1.07),
            (s * 0.87, 5.94, 1.04),
            (s * 0.99, 6.17, 1.04),
            (s * 0.91, 6.42, 1.08),
        ]
        for a, b in zip(points, points[1:]):
            spindle("Palpomere", palp, a, b, 0.063, 0.058, m["amber"])
        cover = p(
            "cover",
            "short forewing",
            "Tegmen",
            "photo",
            PHOTO,
            "Drag the leathery forewing to reveal the folded flight wing.",
            "The darker disc and the paler outer edge follow the photographed adult. Its surface has shallow lengthwise ridges.",
            "chest",
            (1.6, 2, 0.4),
        )
        tegmen(cover, s, m)
        controls["cover_" + tag] = {"open": "Lift forewing", "close": "Lower forewing"}
        wing = p(
            "wing",
            "folded flight wing",
            "Hindwing",
            "adult",
            SPECIES,
            "A thin hindwing folds into a small packet.",
            "Pleats and radiating veins suggest the folded membrane. The crease pattern is simplified; this view shows the resting packet.",
            "chest",
            (1.8, 1.25, 0.6),
        )
        plate(
            "Folded_hindwing",
            wing,
            [
                (0.35, s * 0.69, 1.58, 0.33, 0.050),
                (0.53, s * 0.68, 1.60, 0.45, 0.068),
                (1.47, s * 0.65, 1.62, 0.49, 0.072),
                (2.56, s * 0.62, 1.60, 0.33, 0.056),
            ],
            m["membrane"],
        )
        for j in range(6):
            t = j / 5
            smooth_path(
                "SM_Pleat",
                wing,
                [
                    (s * 0.60, 2.47, 1.637),
                    (s * (0.38 + 0.43 * t), 1.73, 1.665),
                    (s * (0.28 + 0.77 * t), 0.61, 1.65),
                ],
                0.013,
                m["vein"],
                6,
            )
        for j, position in enumerate(["front", "middle", "hind"]):
            leg = p(
                "leg" + str(j + 1),
                position + " leg",
                "Thoracic walking leg",
                "adult",
                SPECIES,
                "The leg bends at the knee and sets its foot on the ground.",
                "The coxa, femur, tibia and tarsus move about separate pivots. Two claws sit at the tip. The walking sequence illustrates contact and recovery.",
                "chest",
                (1.8, -1.2, j - 1),
            )
            walking_leg(leg, s, j, m)
        pin = p(
            "forceps",
            "pincer",
            "Forceps-like cercus",
            "photo",
            PHOTO,
            "Drag the curved pincer open and examine its toothed base.",
            "The stout, flattened root narrows to a curved dark tip. The tooth row lies near the base on the inner margin.",
            "terminal",
            (1.6, 0.4, 2.0),
        )
        forceps(pin, s, m)
        controls["forceps_" + tag] = {"open": "Open pincer", "close": "Close pincer"}
    build_interior(add, m)
    for node in nodes:
        consolidate(node)
    return dict(
        id="earwig-study",
        name="European earwig",
        scientific="Forficula auricularia",
        stage="Adult male",
        lengthMm=12,
        scaleNote="Approx. 12 mm model body length, excluding forceps; the reference photograph has no scale.",
        model="specimen.glb",
        focus="forceps_l",
        title="Inside an earwig",
        overview="Open one rear pincer, or switch to Interior and find the large food-storage sac beneath the short forewings.",
        dragHint="Drag a pincer or a short forewing upward",
        gestureGuide="Drag a pincer up to open it. Lift a short forewing to see the folded wing underneath.",
        landmarks=["forceps_l", "shield", "antenna_r", "leg1_l"],
        controls=controls,
        spread=spread,
        systems=SYSTEMS,
        sources=SOURCES,
        parts=parts,
        view={
            "radius": 8.9,
            "target": [0, 1.0, -0.35],
            "floor": 0,
            "direction": [-1.2, 1.27, -0.57],
            "interiorFrameScale": 0.73,
            "openingMargin": 0.16,
            "narrowLabelRails": True,
        },
        observation={
            "identification": "The UC IPM reference is labeled an adult male European earwig. This example uses the same animal as the earlier comparison.",
            "visible": "The photograph shows paired curved forceps, exposed abdominal plates, abbreviated forewings and pale legs.",
            "reconstructed": "Dissections inform the digestive and reproductive organs, head structures and gland locations. Airway routes follow published micro-CT descriptions.",
            "unresolved": "Organ shape and placement are illustrative. No internal scan of the photographed individual exists in this build. Fine branches, full muscle inventory, tubule counts and the complete genital apparatus remain unresolved.",
        },
        fieldNotes=[
            {
                "topic": "Anatomy review",
                "text": "Reference-based educational reconstruction. Individual dimensions, complete anatomical coverage and expert acceptance remain unverified.",
                "source": "gut",
            },
            {
                "topic": "Behavior",
                "text": "Earwigs shelter in crevices and forage at night. The forceps can be opened in defense; the sequence slows the movements for observation.",
                "source": "adult",
            },
        ],
    )
