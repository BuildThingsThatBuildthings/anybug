import * as THREE from "three";

// Draw original model geometry for each label. Pictures are made on demand,
// using one reusable render target and the same lighting as the specimen.
export function makePortraits(renderer, world, direction, pieces) {
  const size = 144;
  const target = new THREE.WebGLRenderTarget(size, size, { samples: 2 });
  target.texture.colorSpace = THREE.SRGBColorSpace;
  const studio = new THREE.Scene();
  studio.environment = world.environment;
  studio.environmentIntensity = world.environmentIntensity;
  for (const light of world.children.filter((o) => o.isLight)) {
    const copy = light.clone();
    copy.castShadow = false;
    studio.add(copy);
  }
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.01, 1000);
  const pixels = new Uint8Array(size * size * 4);
  const cache = new Map();
  return function portrait(id, palette) {
    const key = id + palette;
    if (cache.has(key)) return cache.get(key);
    const { node, meshes, p, atlasColor } = pieces.get(id);
    const group = node.clone(true);
    group.visible = true;
    group.position.set(0, 0, 0);
    group.rotation.set(0, 0, 0);
    const originals = meshes[Symbol.iterator](),
      materials = [];
    group.traverse((o) => {
      if (!o.isMesh) return;
      if (o.morphTargetInfluences) o.morphTargetInfluences.fill(0);
      const source = originals.next().value;
      const set = source.materials.map((m, i) => {
        const copy = m.clone(),
          d = source.defaults[i];
        copy.color.copy(d.color);
        if (p.system !== "exterior" && palette === "atlas")
          copy.color.set(atlasColor);
        copy.opacity = d.opacity;
        copy.transparent = d.transparent;
        copy.depthWrite = d.depthWrite;
        copy.emissive.setHex(0);
        materials.push(copy);
        return copy;
      });
      o.material = Array.isArray(o.material) ? set : set[0];
    });
    studio.add(group);
    const box = new THREE.Box3().setFromObject(group, true);
    const center = box.getCenter(new THREE.Vector3());
    const extent = Math.max(
      0.01,
      box.getSize(new THREE.Vector3()).length() * 0.5,
    );
    camera.position
      .copy(direction)
      .normalize()
      .multiplyScalar(extent * 4)
      .add(center);
    camera.lookAt(center);
    camera.top = camera.right = extent;
    camera.bottom = camera.left = -extent;
    camera.updateProjectionMatrix();
    const previous = renderer.getRenderTarget();
    renderer.setRenderTarget(target);
    renderer.clear();
    renderer.render(studio, camera);
    renderer.readRenderTargetPixels(target, 0, 0, size, size, pixels);
    renderer.setRenderTarget(previous);
    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = size;
    const ctx = canvas.getContext("2d"),
      img = ctx.createImageData(size, size);
    for (let y = 0; y < size; y++)
      img.data.set(
        pixels.subarray((size - y - 1) * size * 4, (size - y) * size * 4),
        y * size * 4,
      );
    ctx.putImageData(img, 0, 0);
    const url = canvas.toDataURL("image/png");
    studio.remove(group);
    materials.forEach((m) => m.dispose());
    cache.set(key, url);
    return url;
  };
}

export function makeTray(specimen, scene, onSelect) {
  const tray = document.getElementById("anatomy-key"),
    list = document.getElementById("key-parts"),
    filter = document.getElementById("key-system");
  filter.add(new Option("All " + specimen.parts.length + " parts", "all"));
  for (const [id, system] of Object.entries(specimen.systems))
    filter.add(new Option(system.name, id));
  let palette = "atlas";
  let batch = 0;
  const cards = specimen.parts.map((part, i) => {
    const b = document.createElement("button");
    b.className = "key-part";
    b.dataset.keyPart = part.id;
    b.style.setProperty("--part-color", specimen.systems[part.system].color);
    const img = document.createElement("img");
    img.alt = "";
    img.dataset.id = part.id;
    const number = document.createElement("small");
    number.textContent = String(i + 1).padStart(2, "0");
    const name = document.createElement("strong");
    name.textContent = part.name;
    const term = document.createElement("span");
    term.textContent = part.term;
    b.append(img, number, name, term);
    list.append(b);
    b.onclick = () => onSelect(part.id);
    return { part, b, img };
  });
  function fillPictures() {
    batch = 0;
    if (tray.hidden) return;
    const pending = cards.filter(
      (c) => !c.b.hidden && !c.img.hasAttribute("src"),
    );
    for (const { part, img } of pending.slice(0, 2))
      img.src = scene.portrait(part.id, palette);
    if (pending.length > 2) batch = requestAnimationFrame(fillPictures);
  }
  function applyFilter() {
    for (const { part, b } of cards)
      b.hidden = filter.value !== "all" && filter.value !== part.system;
    if (!tray.hidden && !batch) batch = requestAnimationFrame(fillPictures);
  }
  filter.onchange = applyFilter;
  return function show(state) {
    const changed = palette !== state.palette;
    palette = state.palette;
    tray.hidden = !state.spread;
    if (tray.hidden) filter.value = "all";
    for (const { part, b, img } of cards) {
      if (changed && part.system !== "exterior") img.removeAttribute("src");
      b.setAttribute("aria-pressed", String(state.selected === part.id));
    }
    applyFilter();
  };
}
