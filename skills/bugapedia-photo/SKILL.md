---
name: bugapedia-photo
description: Turn an uploaded arthropod photograph into an AnyBug educational specimen using the original reference-led Blender workflow, editable master, native animation and interactive dissection. Prepare a runnable private Blender project when a chat cannot run Blender.
---

# Bugapedia Photo

Use the same geometry, animation and export pipeline as the original AnyBug ladybug and mantis. A photo starts research. The deliverable is a species-authored Blender model with independently movable joints and cited anatomical structures.

## Identify the animal in the upload

Inspect the actual supplied view. Record the diagnostic features, supported taxon, life stage and any supported sex. If a species is unresolved, model at the supported rank or ask for the specific missing view. Never select a geographic variant by default. The worked earwig is a named reference study. It is never a substitute for identifying the user's animal. If there is no image and the user specifically asks what their photograph shows, request the attachment.

Keep personal photos, EXIF, precise location and identifying filenames outside the project, searches and upload queue. Use original geometry. Link public reference illustrations and scans in the brief. Do not bundle or silently transmit the user's photo.

## Research and author in Blender

1. Read `references/ADDING-A-SPECIES.md` and inspect the species builders in `references/specimens/`. In a source checkout these live under `docs/` and `specimens/`. Compare the actual reference image with the earlier model at the same angles before revising. Preserve its source and a rendered baseline.
2. For each applicable major system list structures modeled, evidence level, paper/figure or scan, source taxon and remaining gaps in `README.md`. Check digestive regions, excretion, respiratory pathways, circulation, nerves, musculature, reproduction, storage and taxon-specific specializations. Body plan, sex and life stage matter. Separate observed exterior characters, species-specific anatomical evidence, comparative structures and unknowns. A generic tube network cannot satisfy a request for full internal anatomy.
3. Implement species-specific `build.py` and `behavior.py` using the original geometry and motion helpers. Build in mm with +Y forward and +Z upward. Model silhouette, markings, cuticle, articulations and spatial relationships in the shell. Put a uniquely named part group directly below the metric root for each removable or independently labeled structure. Include natural and atlas materials, anchored joints, exploded offsets and two reading levels. Use a drawable natural resting pose, preserve recognizable features at phone scale and group trim by moving part for efficient rendering.
4. Animate at least two documented or explicitly illustrative actions using actual pivots, contact and recovery. Keep behavior and interactive dissection independent. Provide touch and keyboard alternatives. Keep difficult motions such as folding wings within the range supported by the evidence.
5. Save original Python sources and the research brief together. The stock examples are references. For a new taxon author a new model. Include the papers and limitations in its own field guide.

## Build the files

In an AnyBug checkout, register the specimen in its local catalog and run `python3 rebuild.py SPECIES-ID`. The original build saves the editable .blend and the GLB and performs a fresh Blender reimport. In any other file-enabled chat use the packaged project helper:

```sh
python3 scripts/prepare_project.py authored-species-folder --id species-id --name "Specimen name" --out private-project
python3 private-project/finish.py
```

The second command needs Blender 5.2 (or the executable named by BLENDER). When available, run it and return the resulting explorer, Blender master, GLB and source project. If the chat lacks Blender, still author the species files, run the first command and return the generated project ZIP for the local Blender workflow. Clearly identify it as awaiting a Blender build. Do not generate a replacement mesh with a portable encoder or present an unbuilt project as ready to dissect. File generation takes place in the private workspace.

## Decide what is ready

Check the exported model's part IDs, mesh ownership, native joint travel, clip duration and chapter transitions. Compare the closed, translucent, interior and exploded views with sources and exercise drag, reassembly, palette switching and behavior return on desktop and phone. Check for organs showing through a closed shell, misplaced muscle attachments and limbs sliding or separating during movement. Capture the actual rendered result and name any checks that could not run.

Biological acceptance is separate from a working export. When the request requires a fully accurate interior, compare each required organ's shape, attachment and position against the target taxon's evidence, including cross-sections or scans where available. List unresolved anatomy explicitly. A partial model remains a review specimen. Never mark it complete based on part counts, rendering, or a passed script.

Return the evidence for identification, main interaction, native animation and the private comparison. Keep family photographs private and obtain approval for the exact version before publishing a specimen or changing an installed skill.
