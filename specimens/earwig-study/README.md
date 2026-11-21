# Earwig reference study

An adult male *Forficula auricularia* based on the UC IPM photograph by Jack Kelly Clark. The same named reference was used in the earlier portable example. There was no family photograph for this build. The illustrative body length is about 12 mm, excluding the forceps. The photo has no scale.

## Compare the exterior

Inspect the dark exposed abdominal tergites, the pale margins of the pronotum and short forewings, and the shape of the cerci. The pincers broaden into toothed, flattened bases and taper to curved dark tips. Drag either one independently. Lift a forewing to see the packed hindwing, or follow the hinge and knee of one walking leg in Behavior. The step sequence uses inverse kinematics for foot contact. Joint timing is illustrative. [UC IPM photograph](https://ipm.ucanr.edu/PMG/F/I-DM-FAUR-AD.005.html) · [UF species account](https://ask.ifas.ufl.edu/publication/IN875)

## Inside the body

| Region | Basis for geometry | Limits |
| --- | --- | --- |
| Digestive and excretory organs | Lhoste's dissection describes the large crop, gizzard, tapered midgut, terminal convolution, Malpighian tubules and six rectal pads. | A representative fill state and subset of tubule paths. [Species dissection, figure 1](https://doi.org/10.3406/bsef.1941.15490) |
| Head, nerves and muscles | The tentorium, mandibular attachments, brain, optic lobes and lower ganglion use Neubert and colleagues' head study. | Fine muscles, nerve branches and sense organs are incomplete. [Head figures and anatomical descriptions](https://www.senckenberg.de/wp-content/uploads/2019/07/04_asp_75_1_neubert_99-124.pdf) |
| Tracheae | Curved cervical trunks, branches to the eyes and antennae, abdominal branches and asymmetric posterior loops follow Herhold and colleagues' CT description. | An original interpretation of major routes, with larger branch diameters for viewing. [CT description and figures 47–49](https://zenodo.org/records/7733234) |
| Reproduction | Paired bilobed testes, ducts, storage and a terminal duct follow the male literature. | Position, fullness and fine duct routing are illustrative. The complete terminal genital apparatus is absent. [Hudson](https://doi.org/10.1080/03036758.1973.10430603) · [Popham](https://doi.org/10.1111/j.1469-7998.1965.tb05198.x) |
| Glands | Two paired dorsal reservoirs open at the third and fourth tergites. | Geometry illustrates the sacs and short outlets. [Adult gland observations](https://groups.csail.mit.edu/mac/projects/psyche/67/67-062.html) |
| Other tissues | Heart, postcephalic cord, cercal muscle bundles and peripheral fat body show comparative arrangements. | Chamber dimensions, fibers, lobule counts and tissue colors are schematic. |

The model has not been registered to a whole-body scan of the reference individual or independently accepted as anatomically complete. Individual part records give the supporting reference and evidence level. Original geometry and animation are MIT-licensed. Source images and published figures are linked only.

Run `python3 rebuild.py earwig-study` from the repository root. The command creates the Blender master, native behavior and articulation clips, packed GLB and anatomy manifest, then reimports the GLB in a fresh Blender process.
