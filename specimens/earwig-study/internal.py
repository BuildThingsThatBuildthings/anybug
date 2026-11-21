"""Macroscopic anatomy reconstructed from the studies cited in the field record."""

from math import cos, pi, sin
from geometry import oval, smooth_path, tube
from surfaces import plate, spindle

SPECIES = "Species reference"
COMPARATIVE = "Comparative reconstruction"


def build_interior(add, m):
    def organ(
        key, name, term, system, source, short, detail, offset, comparative=False
    ):
        return add(
            key,
            name,
            term,
            system,
            source,
            COMPARATIVE if comparative else SPECIES,
            short,
            detail,
            None,
            offset,
        )

    g = organ(
        "foregut",
        "Throat and food passage",
        "Pharynx and oesophagus",
        "digestive",
        "gut",
        "Food travels back from the mouth into the crop.",
        "The narrow passage runs under the brain. The specimen study describes a continuous transition between pharynx and oesophagus.",
        [-1.1, 0.4, -2.0],
    )
    smooth_path(
        "SM_Foregut",
        g,
        [(0, 5.94, 1.15), (0, 5.50, 1.26), (0, 4.90, 1.29), (0, 4.05, 1.25)],
        0.101,
        m["gut"],
        12,
    )
    g = organ(
        "crop",
        "Food-storage sac",
        "Crop",
        "digestive",
        "gut",
        "This large pouch can hold a meal.",
        "Lhoste describes it spanning the thorax and first visible abdominal ring. Its fullness changes; the model shows an illustrative state.",
        [-2.3, 0.9, -1.0],
    )
    plate(
        "Distensible_crop",
        g,
        [
            (-0.44, 0, 1.20, 0.23, 0.15),
            (-0.19, 0, 1.24, 0.56, 0.31),
            (0.65, -0.03, 1.26, 0.70, 0.34),
            (1.65, -0.045, 1.28, 0.72, 0.34),
            (2.60, -0.03, 1.27, 0.63, 0.31),
            (3.46, 0, 1.25, 0.49, 0.23),
            (4.05, 0, 1.25, 0.115, 0.105),
        ],
        m["crop"],
    )
    for lane in [-0.65, -0.27, 0.13, 0.5]:
        smooth_path(
            "SM_Crop_fold",
            g,
            [
                (lane * 0.28, 3.40, 1.45),
                (lane * 0.62, 2.65, 1.53 - 0.12 * lane**2),
                (lane * 0.76, 1.7, 1.605 - 0.16 * lane**2),
                (lane * 0.73, 0.6, 1.57 - 0.16 * lane**2),
                (lane * 0.5, -0.08, 1.49 - 0.12 * lane**2),
            ],
            0.012,
            m["fold"],
            6,
        )
    g = organ(
        "gizzard",
        "Food grinder",
        "Proventriculus",
        "digestive",
        "gut",
        "A muscular chamber works food before it enters the midgut.",
        "The proventriculus lies directly behind the crop and helps keep material moving toward the midgut.",
        [-1.2, 1.3, 0.0],
    )
    oval("SM_Proventriculus", g, (0, -0.62, 1.20), (0.32, 0.36, 0.27), m["gizzard"])
    for j in range(6):
        a = 2 * pi * j / 6
        spindle(
            "Gizzard_ridge",
            g,
            (0.21 * cos(a), -0.40, 1.2 + 0.17 * sin(a)),
            (0.22 * cos(a), -0.83, 1.20 + 0.18 * sin(a)),
            0.055,
            0.056,
            m["fold"],
        )
    g = organ(
        "midgut",
        "Digestive stomach",
        "Midgut",
        "digestive",
        "gut",
        "This stretch of gut absorbs nutrients.",
        "Its tapered outline follows the horn-like stomach described in the dissection. This species lacks gastric caeca.",
        [-1.85, 0.45, 1.3],
    )
    plate(
        "Ventriculus",
        g,
        [
            (-2.91, -0.13, 1.19, 0.18, 0.15),
            (-2.57, -0.08, 1.20, 0.28, 0.22),
            (-1.97, 0.07, 1.24, 0.36, 0.26),
            (-1.40, 0.09, 1.25, 0.40, 0.27),
            (-0.92, 0.035, 1.21, 0.30, 0.21),
        ],
        m["stomach"],
    )
    g = organ(
        "pylorus",
        "Gut junction",
        "Pyloric region",
        "digestive",
        "gut",
        "Waste-filtering tubes meet the gut here.",
        "A constriction marks the boundary with the hindgut. The fine tubules are represented separately.",
        [0.65, -0.8, 0.6],
    )
    oval("SM_Pyloric_ring", g, (-0.13, -2.94, 1.19), (0.20, 0.12, 0.16), m["gizzard"])
    g = organ(
        "hindgut",
        "Hindgut loop",
        "Ileum and colon",
        "digestive",
        "gut",
        "Follow the bend behind the stomach.",
        "The digestive tract runs mostly straight until this posterior convolution. The study found the ileum and colon difficult to distinguish externally.",
        [1.2, -0.7, 1.45],
    )
    smooth_path(
        "SM_Hindgut_loop",
        g,
        [
            (-0.13, -2.95, 1.19),
            (-0.36, -3.39, 1.10),
            (-0.42, -3.88, 1.14),
            (-0.17, -4.02, 1.26),
            (0.14, -3.83, 1.33),
            (0.25, -3.71, 1.25),
            (0.19, -4.10, 1.15),
            (0.1, -4.54, 1.13),
        ],
        0.13,
        m["gut"],
        12,
    )
    g = organ(
        "rectum",
        "Rectal chamber and pads",
        "Rectal ampulla and rectum",
        "digestive",
        "gut",
        "Six pads line the last enlarged chamber.",
        "Lhoste described six ovoid glands before the short terminal rectum. They are grouped with the chamber here.",
        [0.4, -0.55, 2.45],
    )
    oval("SM_Rectal_ampulla", g, (0.06, -4.83, 1.15), (0.29, 0.45, 0.20), m["crop"])
    for j in range(6):
        a = 2 * pi * j / 6
        oval(
            "SM_Rectal_pad",
            g,
            (0.06 + 0.255 * cos(a), -4.83, 1.15 + 0.174 * sin(a)),
            (0.064, 0.18, 0.054),
            m["fold"],
            14,
            8,
        )
    smooth_path(
        "SM_Rectum",
        g,
        [(0.06, -5.2, 1.15), (0, -5.55, 1.08), (0, -5.76, 0.98)],
        0.084,
        m["gut"],
        10,
    )

    for s, side, tag in [(-1, "Left", "l"), (1, "Right", "r")]:

        def paired(
            key, label, term, system, ref, short, detail, offset, comparative=False
        ):
            return organ(
                key + "_" + tag,
                side + " " + label,
                term,
                system,
                ref,
                short,
                detail,
                offset,
                comparative,
            )

        g = paired(
            "tubules",
            "waste tubules",
            "Malpighian tubules",
            "excretory",
            "gut",
            "These fine tubes empty into the digestive tract.",
            "Several representative paths show where waste fluid enters the gut. Exact tubule counts and coils are unresolved in this reconstruction.",
            [s * 2.7, 0.1, 1.1],
        )
        for j in range(4):
            length = [2.6, 3.6, -1.1, -1.75][j]
            points = [(-0.13, -2.94, 1.19)]
            for k in range(1, 29):
                t = k / 28
                x = s * (0.45 + 0.30 * sin(pi * t) + 0.20 * sin(2 * pi * t + j))
                points.append(
                    (
                        x,
                        -2.94 + length * t + 0.14 * sin(3 * pi * t),
                        1.26 + 0.12 * sin(3 * pi * t + j),
                    )
                )
            tube(
                "SM_Excretory_tubule",
                g,
                points,
                [0.033 - 0.011 * k / 28 for k in range(29)],
                m["tubule"],
                7,
            )
        g = paired(
            "trachea",
            "body airways",
            "Thoracic and abdominal tracheae",
            "respiratory",
            "air",
            "Air follows branching trunks to the organs and the pincer muscles.",
            "Herhold and colleagues traced these airways by micro-CT. Anterior and posterior branches run in different directions; the left posterior loop extends farther. Only major routes are shown.",
            [s * 2.5, 1.2, 0.6],
        )
        for h, z in enumerate([1.38, 1.03]):
            pts = [
                (
                    s * x * 0.88,
                    y,
                    (1.46 if h == 0 else 1.16) if y == 4.32 else z + 0.035 * sin(y),
                )
                for x, y in [
                    (0.49, 4.32),
                    (0.76, 3.3),
                    (0.91, 2.25),
                    (1.0, 0.9),
                    (1.13, -0.6),
                    (1.19, -2.35),
                    (1.13, -3.55),
                    (0.91, -4.7),
                    (0.63, -5.34),
                ]
            ]
            smooth_path(
                "SM_Longitudinal_trunk", g, pts, 0.047 if h == 0 else 0.039, m["air"], 8
            )
        for j in range(8):
            y = 0.53 - 0.75 * j
            x = 0.96 + 0.105 * sin((j + 1) * pi / 10)
            dx = 0.22 if s == 1 else 0.28
            enddir = 0.56 if j < 5 else -0.48
            smooth_path(
                "SM_Visceral_airway",
                g,
                [
                    (s * x, y, 1.11),
                    (s * (x - 0.17), y + 0.09, 1.10),
                    (s * (x - 0.27), y + enddir * 0.63, 1.06),
                    (s * dx, y + enddir, 1.11),
                ],
                0.026,
                m["air"],
                6,
            )
            smooth_path(
                "SM_Spiracular_branch",
                g,
                [
                    (s * x, y, 1.08),
                    (s * (x + 0.06), y, 1.22),
                    (s * (x + 0.12), y, 1.30),
                ],
                0.033,
                m["air"],
                7,
            )
        length = 2.95 if s < 0 else 1.05
        smooth_path(
            "SM_Posterior_visceral_loop",
            g,
            [
                (s * 0.91, -1.72, 1.40),
                (s * 0.61, -2.12, 1.41),
                (s * 0.48, -1.85 - length, 1.28),
                (s * 0.68, -1.98 - length, 1.21),
                (s * 0.80, -1.78 - length, 1.24),
            ],
            0.031,
            m["air"],
            7,
        )
        g = paired(
            "head_air",
            "head airways",
            "Cervical and cephalic tracheae",
            "respiratory",
            "air",
            "Two main air routes enter each side of the head.",
            "The dorsal cervical trunks approach one another at the neck, then turn outward. Selected branches continue to the eyes, mouth and antennal bases.",
            [s * 1.6, 1.0, -2.3],
        )
        for z in [1.16, 1.46]:
            smooth_path(
                "SM_Cervical_trunk",
                g,
                [
                    (s * 0.43, 4.32, z),
                    (s * (0.16 if z > 1.4 else 0.50), 4.53, z),
                    (s * 0.52, 4.91, z),
                    (s * 0.74, 5.18, z),
                ],
                0.046,
                m["air"],
                8,
            )
        for j, (x, y, z) in enumerate(
            [(0.96, 5.16, 1.49), (0.65, 5.63, 1.45), (0.38, 5.85, 1.17)]
        ):
            smooth_path(
                "SM_Cephalic_branch",
                g,
                [(s * 0.55, 4.97, 1.4), (s * 0.63, 5.16, 1.48), (s * x, y, z)],
                0.028,
                m["air"],
                7,
            )
        g = paired(
            "testis",
            "testis",
            "Bilobed testis",
            "reproductive",
            "male",
            "This paired organ makes sperm.",
            "Hudson describes spindle-shaped testes with two lobes. Relative position and fullness are reconstructed rather than measured in the photographed individual.",
            [s * 2.1, -0.7, 1.6],
        )
        for j in [-1, 1]:
            spindle(
                "Testis_lobe",
                g,
                (s * (0.47 + j * 0.10), -2.45, 1.04),
                (s * (0.74 + j * 0.10), -3.96, 0.98),
                0.135,
                0.112,
                m["testis"],
            )
        g = paired(
            "sperm_duct",
            "sperm duct",
            "Vas deferens",
            "reproductive",
            "repro",
            "This duct carries sperm away from the testis.",
            "The paired ducts converge toward the storage organ. The exact course of each duct is illustrative.",
            [s * 1.35, -1.15, 1.55],
        )
        smooth_path(
            "SM_Vas_deferens",
            g,
            [
                (s * 0.73, -3.84, 0.99),
                (s * 0.65, -4.10, 1.00),
                (s * 0.47, -3.92, 0.95),
                (s * 0.34, -4.01, 0.90),
                (s * 0.18, -4.30, 0.87),
            ],
            0.042,
            m["duct"],
            8,
        )
        g = paired(
            "adductor",
            "jaw-closing muscle",
            "Craniomandibularis internus",
            "muscular",
            "head",
            "This muscle pulls the jaw inward.",
            "Bundles run from the head capsule toward the mandibular tendon. The bundles stand for the larger attachment field shown by Neubert and colleagues.",
            [s * 1.5, 0.65, -1.5],
        )
        for j in range(4):
            spindle(
                "Mandibular_bundle",
                g,
                (s * (0.30 + 0.13 * j), 4.85, 1.54 + 0.035 * j),
                (s * 0.44, 5.66, 1.20),
                0.083,
                0.082,
                m["muscle"],
            )
        g = paired(
            "cercal_muscle",
            "pincer muscle group",
            "Cercal musculature",
            "muscular",
            "air",
            "Muscles inside the tail pull on the pincer base.",
            "The scan describes dense air supply to the cercal muscles in posterior segments. Fiber paths and bundle thickness here are comparative.",
            [s * 1.8, 0.65, 2.35],
            True,
        )
        for j in range(4):
            spindle(
                "Cercal_bundle",
                g,
                (s * (0.51 + 0.14 * j), -3.91 - 0.07 * j, 1.25 + 0.045 * j),
                (s * 0.68, -5.49, 1.12),
                0.095,
                0.072,
                m["muscle"],
            )
        g = paired(
            "glands",
            "defensive gland sacs",
            "Tergal gland reservoirs",
            "glandular",
            "glands",
            "Two little sacs on this side open along the back plates.",
            "Adult dissections locate one pair of sacs beneath each of the third and fourth tergites, with outlets at their rear margins.",
            [s * 1.8, 1.6, 0.1],
        )
        for y in [-0.58, -1.30]:
            oval(
                "SM_Tergal_sac",
                g,
                (s * 0.89, y, 1.42),
                (0.135, 0.225, 0.105),
                m["gland"],
                16,
                10,
            )
            smooth_path(
                "SM_Tergal_duct",
                g,
                [
                    (s * 0.92, y - 0.09, 1.42),
                    (s * 1.02, y - 0.19, 1.43),
                    (s * 1.07, y - 0.25, 1.44),
                ],
                0.028,
                m["duct"],
                7,
            )
        g = paired(
            "fat",
            "fat body",
            "Peripheral fat body",
            "storage",
            "fat",
            "These lobes store reserves for growth and activity.",
            "Their dispersed position under the body wall follows general insect anatomy. Their individual sizes and arrangement are schematic.",
            [s * 1.5, -1.5, 0.2],
            True,
        )
        for j in range(11):
            y = 0.5 - 0.37 * j
            oval(
                "SM_Fat_body_lobule",
                g,
                (s * (0.94 + 0.07 * sin(2 * j)), y, 0.97 + 0.045 * cos(j)),
                (0.13 + 0.02 * sin(j), 0.18, 0.082),
                m["fat"],
                14,
                8,
            )
    g = organ(
        "vesicle",
        "Sperm-storage sac",
        "Seminal vesicle",
        "reproductive",
        "repro",
        "Sperm can be held here before transfer.",
        "The storage organ is connected to the ducts. Its volume and fill state are illustrative.",
        [0.25, -1.6, 1.7],
    )
    oval("SM_Seminal_vesicle", g, (0, -4.34, 0.86), (0.22, 0.26, 0.13), m["testis"])
    g = organ(
        "ejaculatory_duct",
        "Terminal sperm duct",
        "Ejaculatory duct",
        "reproductive",
        "male",
        "This duct runs toward the terminal reproductive structures.",
        "The posterior passage is represented as one connection. The detailed copulatory apparatus is outside this reconstruction.",
        [-0.5, -1.2, 2.15],
    )
    smooth_path(
        "SM_Ejaculatory_duct",
        g,
        [
            (0, -4.46, 0.86),
            (-0.13, -4.67, 0.84),
            (-0.04, -4.98, 0.86),
            (0, -5.48, 0.90),
        ],
        0.049,
        m["duct"],
        8,
    )
    g = organ(
        "heart",
        "Dorsal heart and aorta",
        "Dorsal vessel",
        "circulatory",
        "heart",
        "This long vessel moves hemolymph forward.",
        "The abdominal heart lies dorsally and continues as a narrower aorta toward the head. Chamber boundaries are schematic.",
        [0, 2.0, 0.6],
        True,
    )
    pts = [
        (0, y, 1.515 + 0.035 * sin(y * 0.7))
        for y in [-5.16, -4.3, -3.4, -2.5, -1.6, -0.7, 0.2, 1.3, 2.5, 3.6, 4.60]
    ]
    tube(
        "SM_Dorsal_vessel",
        g,
        pts,
        [0.048, 0.085, 0.095, 0.095, 0.092, 0.087, 0.067, 0.058, 0.048, 0.047, 0.036],
        m["vessel"],
        10,
    )
    for j in range(6):
        y = -4.64 + j * 0.75
        spindle(
            "Heart_chamber",
            g,
            (0, y - 0.25, 1.515 + 0.035 * sin((y - 0.25) * 0.7)),
            (0, y + 0.24, 1.515 + 0.035 * sin((y + 0.24) * 0.7)),
            0.103,
            0.088,
            m["vessel"],
        )
    g = organ(
        "brain",
        "Brain and visual lobes",
        "Supraoesophageal ganglion",
        "nervous",
        "head",
        "Signals from the eyes and feelers reach the brain.",
        "The central brain lies above the front of the gut. The optic lobes extend toward the compound eyes.",
        [0, 1.5, -2.0],
    )
    for s in [-1, 1]:
        oval("SM_Brain_lobe", g, (s * 0.19, 5.21, 1.53), (0.24, 0.23, 0.15), m["nerve"])
        spindle(
            "Optic_lobe",
            g,
            (s * 0.28, 5.22, 1.51),
            (s * 0.85, 5.15, 1.47),
            0.12,
            0.095,
            m["nerve"],
        )
        smooth_path(
            "SM_Perioesophageal_connective",
            g,
            [(s * 0.25, 5.28, 1.50), (s * 0.33, 5.32, 1.27), (s * 0.21, 5.24, 1.085)],
            0.038,
            m["nerve"],
            8,
        )
    g = organ(
        "subbrain",
        "Lower head ganglion",
        "Suboesophageal ganglion",
        "nervous",
        "head",
        "This nerve center sits below the food passage.",
        "Connections pass down around the oesophagus and link the brain with the lower ganglion and the ventral nervous system.",
        [0, -1.2, -1.8],
    )
    oval(
        "SM_Suboesophageal_ganglion",
        g,
        (0, 5.19, 1.085),
        (0.25, 0.24, 0.12),
        m["nerve"],
    )
    g = organ(
        "cord",
        "Ventral nerve cord",
        "Ventral connectives and ganglia",
        "nervous",
        "nerve",
        "These connections run along the underside of the body.",
        "The enlarged thoracic ganglia represent nerve centers associated with the legs. Posterior spacing and branches are a comparative reconstruction.",
        [0, -1.8, 0.5],
        True,
    )
    for s in [-1, 1]:
        smooth_path(
            "SM_Nerve_connective",
            g,
            [
                (
                    s * 0.075,
                    y,
                    (1.12 if y > 3.7 else (1.02 if y > 1 else 0.91))
                    + 0.035 * cos(y * 0.8),
                )
                for y in [5.03, 4.52, 4.1, 3.25, 2.2, 1.05, 0, -1.5, -2.8, -4.3, -4.92]
            ],
            0.033,
            m["nerve"],
            8,
        )
    for j, y in enumerate([3.25, 2.12, 0.98, -0.61, -1.8, -2.94, -4.62]):
        oval(
            "SM_Segmental_ganglion",
            g,
            (0, y, (1.0 if y > 1 else 0.88) + 0.04 * cos(y * 0.8)),
            (0.15, 0.18, 0.085),
            m["nerve"],
            16,
            10,
        )
        for s in [-1, 1]:
            smooth_path(
                "SM_Peripheral_nerve",
                g,
                [
                    (s * 0.09, y, 0.88),
                    (s * 0.34, y + 0.05, 0.89),
                    (s * 0.65, y + 0.12, 0.95),
                ],
                0.022,
                m["nerve"],
                6,
            )
    g = organ(
        "tentorium",
        "Inner head brace",
        "Tentorium",
        "support",
        "head",
        "A cuticular frame inside the head anchors muscles.",
        "The anterior and posterior arms meet at the corpotentorium. This model simplifies the arms documented in figure 3.",
        [0, -1.15, -2.4],
    )
    for s in [-1, 1]:
        smooth_path(
            "SM_Tentorial_arm",
            g,
            [
                (s * 0.49, 5.67, 1.28),
                (s * 0.28, 5.15, 1.14),
                (s * 0.27, 4.91, 1.16),
                (s * 0.60, 4.72, 1.22),
            ],
            0.053,
            m["bone"],
            8,
        )
    tube(
        "SM_Corpotentorium",
        g,
        [(-0.28, 4.92, 1.16), (0.28, 4.92, 1.16)],
        0.058,
        m["bone"],
        8,
    )
