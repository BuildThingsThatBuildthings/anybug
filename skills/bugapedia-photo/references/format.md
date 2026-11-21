# Specimen source format

Use ordinary UTF-8 JSON. Start with a small authoring script or a JSON document. The earwig example prints a complete input with standard-library Python. For a different taxon choose new anatomy, source references, observations, proportions, markings, attachments and movements.

## Coordinates and shape construction

Work in millimetres. +X points to the animal's left or right according to your chosen observer orientation; keep that convention consistent throughout. +Y is up, the head faces −Z and the rear points toward +Z. All geometry coordinates and pivots use the same absolute model space. Each part is exported relative to its own pivot. No separate scaling step is needed. The GLB root converts millimetres to metres.

Each shape requires a natural sRGB hex `color` and may set `alpha` from above zero through one. Give a part several surfaces when its cuticle has spots, ridges, claws, spines or veins. A surface belongs to exactly one selectable part.

| kind | geometry fields |
| --- | --- |
| `ellipsoid` | `center: [x,y,z]` and three positive `radii` |
| `tube` | At least two distinct path `points` and a positive radius in `radii` per point. Keep adjacent points apart. Use multiple smoothly bent sections for antennae, ducts and limbs. |
| `loft` | `rings` is a sequence of equally sized polygon loops, at least three vertices each. Use the same vertex ordering around each ring, winding toward the next ring. The ends are capped. |
| `mesh` | `vertices` are 3D points and `faces` are outward-wound index triples. Avoid degenerate triangles or unused vertices. Use for wing membranes, noncircular shells or intricate markings. |

## Required records

* `id` is a lowercase hyphenated species or morphotype slug. Supply `name`, `scientific` at the supported rank, `stage`, positive `lengthMm` for **model** body length, and `scaleNote` stating measured, published range or illustrative. Never invent a measured length.
* `title`, `overview`, `focus` (an existing part), `dragHint` and `gestureGuide` introduce the signature manipulation. `view` needs a positive `radius`, `target` and oblique `direction`. Optional `floor` sits just under the foot contact points. Frame the longest appendages.
* `observation` contains four sentences or paragraphs named `identification`, `visible`, `reconstructed`, `unresolved`. `sources` maps short keys to `[descriptive title, https URL]`. Keep private observation details in prose. For a private photo, cite a public anatomical source relevant to each visible structure and identify photo evidence in the corresponding evidence label. `fieldNotes` contains `{topic,text,source}` entries for natural history.
* `systems` maps keys to `{name,color}` entries. The outer body uses `exterior`. Internals have meaningful system keys and distinguishable atlas colors. Natural colors are embedded in the GLB.
* Each `parts` item needs a unique lowercase underscore `id`, `name`, anatomical `term`, `system`, `parent` (attachment ID or null), `source`, `evidence`, child-friendly `short`, fuller `detail`, 3D `pivot` and nonempty `shapes`. Use “Visible in photograph,” “Species reference” or “Comparative reconstruction” with appropriate scope. Use separate selection units when learners should be able to remove two pieces independently. Group surface ornament on its carrier. Acyclic attachments move with their parent for performance and dissection.
* `controls` maps a part ID to `{open,close,angles:[x,y,z]}` (Euler degrees). The angles rotate that part's own mesh surfaces around its pivot. Model attached ornament on the same part for this hinge. A separately selectable descendant can set its part field `control` to the hinged ancestor ID. Its surfaces then follow the parent around the same pivot during dragging and retain their own label. For example, set a mantis tarsus to follow its hinged tibia. Give independent segments their own hinges or behavior tracks.
* Optional `landmarks` are a few part IDs visible in the intact pose. `spread` maps IDs to pull-apart offsets in mm. Set offsets that reveal overlapping organs.
* `behavior` contains a unique `clip` name, positive `duration` in seconds, positive `frameScale`, `sourceIds`, and `actions`. An action has `name`, inclusive `start` and a plain-language `note`. The first starts at zero. Chapters are consecutive and each needs visible movement.
* `behavior.tracks` maps each animated part ID to a list of `[seconds,[rx,ry,rz],[dx,dy,dz]]`. Rotations are degrees about its pivot, and offsets are mm in the unposed parent's axes. Ancestors' transforms are composed automatically. Mix rotations and translations for locomotion, contact, folding or hovering. Surround a local movement with explicit rest keys if it should only occur during one chapter. Start/end holds and piecewise-linear interpolation are supported; add intermediate poses for easing. No identification or animation is inferred by the encoder itself.

## Worked build

```sh
python3 references/earwig_example.py > earwig.json
python3 scripts/build_specimen.py earwig.json --out earwig-result
python3 scripts/check_specimen.py earwig-result
```

Open the downloaded `explore.html` in a modern WebGL 2 browser. It embeds the viewer, geometry, motion and licenses and works without a server. Field guide sources are ordinary outbound links. A local AnyBug library can consume the GLB and anatomy manifest directly. The source JSON recreates both using this skill.
