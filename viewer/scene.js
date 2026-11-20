import { makeAnnotations } from "./annotations.js?v=2";
import { makePortraits } from "./tray.js";
import * as THREE from "three";
import { GLTFLoader } from "../vendor/three/loaders/GLTFLoader.js";
import { OrbitControls } from "../vendor/three/controls/OrbitControls.js";
import { RoomEnvironment } from "../vendor/three/environments/RoomEnvironment.js";

const vector = (coords) => new THREE.Vector3(...coords);

// Pin each name to an actual surface vertex, including on folding membranes.
function surfaceAnchor(node, near, preferred) {
  const point = new THREE.Vector3();
  let closest = Infinity,
    result;
  node.traverse((mesh) => {
    if (!mesh.isMesh || (preferred && mesh !== preferred)) return;
    const count = mesh.geometry.attributes.position.count;
    for (let i = 0; i < count; i += Math.max(1, Math.floor(count / 240))) {
      mesh.getVertexPosition(i, point).applyMatrix4(mesh.matrixWorld);
      const d = point.distanceToSquared(near);
      if (d < closest) {
        closest = d;
        result = { mesh, index: i };
      }
    }
  });
  return () =>
    result.mesh
      .getVertexPosition(result.index, new THREE.Vector3())
      .applyMatrix4(result.mesh.matrixWorld);
}

export async function makeScene(host, url, manifest, events) {
  const renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true,
    powerPreference: "low-power",
  });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setClearColor(0, 0);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.92;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  host.append(renderer.domElement);
  const world = new THREE.Scene();
  const sceneScale = manifest.view.radius / 4;
  const pmrem = new THREE.PMREMGenerator(renderer);
  const studio = new RoomEnvironment();
  const illumination = pmrem.fromScene(studio, 0.035);
  world.environment = illumination.texture;
  world.environmentIntensity = 0.52;
  pmrem.dispose();
  studio.dispose();
  world.add(new THREE.HemisphereLight(0xfff8de, 0x827a62, 0.87));
  const light = new THREE.DirectionalLight(0xfff1d8, 1.85);
  light.position.set(-5, 11, -5).multiplyScalar(sceneScale);
  light.castShadow = true;
  Object.assign(light.shadow.camera, {
    left: -9 * sceneScale,
    right: 9 * sceneScale,
    top: 9 * sceneScale,
    bottom: -9 * sceneScale,
    near: 0.1,
    far: 30 * sceneScale,
  });
  light.shadow.mapSize.set(1024, 1024);
  light.shadow.normalBias = 0.025 * sceneScale;
  light.shadow.bias = -0.0004;
  light.shadow.radius = 3;
  world.add(light);
  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(80 * sceneScale, 80 * sceneScale),
    new THREE.ShadowMaterial({ opacity: 0.16, depthWrite: false }),
  );
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = manifest.view.floor ?? -0.55;
  floor.receiveShadow = true;
  world.add(floor);

  const camera = new THREE.OrthographicCamera(
    -5,
    5,
    5,
    -5,
    0.02 * sceneScale,
    150 * sceneScale,
  );
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enablePan = false;
  controls.minZoom = 0.45;
  controls.maxZoom = 6;
  controls.rotateSpeed = 0.8;
  const target = vector(manifest.view.target);
  function home() {
    camera.position.copy(
      vector(manifest.view.direction)
        .normalize()
        .multiplyScalar(manifest.view.radius * 4)
        .add(target),
    );
    camera.zoom = 1;
    controls.target.copy(target);
    camera.updateProjectionMatrix();
    controls.update();
  }
  home();
  const gltf = await new GLTFLoader().loadAsync(url);
  const scale = new THREE.Group();
  scale.scale.setScalar(1000);
  scale.add(gltf.scene);
  world.add(scale);
  scale.updateMatrixWorld(true);
  const pieces = new Map();
  const mixer = new THREE.AnimationMixer(gltf.scene);
  for (const p of manifest.parts) {
    const node = gltf.scene.getObjectByName(p.id);
    if (!node || node.userData.partId !== p.id)
      throw Error("Missing part " + p.id);
    const bounds = new THREE.Box3().setFromObject(node, true);
    const center = bounds.getCenter(new THREE.Vector3());
    const holder = new THREE.Group();
    const parent = node.parent;
    parent.add(holder);
    holder.position.copy(parent.worldToLocal(center.clone()));
    holder.updateWorldMatrix(true, false);
    holder.attach(node);
    const meshes = [];
    const animationTargets = new Set();
    node.traverse((o) => {
      animationTargets.add(o.name);
      if (!o.isMesh) return;
      o.userData.pick = p.id;
      o.castShadow = true;
      const source = Array.isArray(o.material) ? o.material : [o.material];
      const materials = source.map((m) => m.clone());
      o.material = Array.isArray(o.material) ? materials : materials[0];
      meshes.push({
        object: o,
        materials,
        defaults: materials.map((m) => ({
          color: m.color.clone(),
          opacity: m.opacity,
          transparent: m.transparent,
          depthWrite: m.depthWrite,
        })),
      });
    });
    const tipMesh = node.children.find((child) =>
      child.name.startsWith("Tapered_tibia"),
    );
    const labelCenter = tipMesh
      ? new THREE.Box3()
          .setFromObject(tipMesh, true)
          .getCenter(new THREE.Vector3())
      : center.clone();
    const tracks = gltf.animations
      .flatMap((a) => a.tracks)
      .filter((t) =>
        animationTargets.has(
          THREE.PropertyBinding.parseTrackName(t.name).nodeName,
        ),
      );
    let action;
    if (tracks.length) {
      const clip = new THREE.AnimationClip(p.id, -1, tracks);
      action = mixer.clipAction(clip);
      action.setLoop(THREE.LoopOnce, 1);
      action.clampWhenFinished = true;
      action.play();
      action.paused = true;
    }
    pieces.set(p.id, {
      p,
      node,
      holder,
      meshes,
      action,
      center,
      anchor: surfaceAnchor(node, labelCenter, tipMesh),
      atlasColor: manifest.systems[p.system].color,
      spread: manifest.spread?.[p.id]
        ? vector(manifest.spread[p.id])
        : center
            .clone()
            .sub(target)
            .normalize()
            .multiplyScalar(manifest.view.radius * 0.9),
      value: 0,
      goal: 0,
    });
  }
  for (const piece of pieces.values()) {
    if (piece.p.parent) pieces.get(piece.p.parent).holder.attach(piece.holder);
    piece.rest = piece.holder.position.clone();
  }
  const drawLabels = makeAnnotations(
    host,
    manifest.parts,
    events.select,
    manifest.view.narrowLabelRails,
  );
  const portrait = makePortraits(
    renderer,
    world,
    vector(manifest.view.direction),
    pieces,
  );
  let spreadAmount = 0;
  let current = null,
    dirty = true;
  const invalidate = () => {
    dirty = true;
  };
  controls.addEventListener("change", invalidate);
  document.fonts.ready.then(invalidate);
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  function resize() {
    const { width, height } = host.getBoundingClientRect();
    const aspect = width / height;
    const opening =
      current?.view === "outside"
        ? Math.max(0, ...Object.values(current.open).map(Number))
        : 0;
    const half =
      manifest.view.radius *
      Math.max(manifest.view.minFrame ?? 0.87, 1.05 / aspect) *
      (1 +
        (manifest.view.openingMargin ?? 0.37) * opening +
        1.05 * spreadAmount);
    camera.top = half;
    camera.bottom = -half;
    camera.right = half * aspect;
    camera.left = -camera.right;
    camera.updateProjectionMatrix();
    if (
      renderer.domElement.clientWidth &&
      (renderer.domElement.width !==
        Math.floor(width * renderer.getPixelRatio()) ||
        renderer.domElement.height !==
          Math.floor(height * renderer.getPixelRatio()))
    )
      renderer.setSize(width, height, false);
    invalidate();
  }
  new ResizeObserver(resize).observe(host);
  resize();
  function place(entry, state) {
    const { holder, p } = entry;
    holder.position
      .copy(entry.rest)
      .addScaledVector(entry.spread, spreadAmount);
    const displaced = state.moved[p.id];
    holder.rotation.set(0, displaced?.turn || 0, 0);
    if (displaced) holder.position.add(vector(displaced.offset));
  }
  function apply(state) {
    current = state;
    resize();
    for (const entry of pieces.values()) {
      const { p, meshes } = entry;
      const isOutside = p.system === "exterior";
      const isFocus = state.system === "all" || state.system === p.system;
      const ghost = state.view === "inside" && !isOutside && !isFocus;
      // Keep each holder active so a visible child can be inspected independently.
      entry.node.visible =
        !isOutside ||
        ((state.spread || state.view === "outside") && state.opacity > 0);
      const alpha = isOutside ? state.opacity : 1;
      const fading = alpha < 1;
      for (const { object, materials, defaults } of meshes) {
        object.castShadow = !ghost && !fading;
        materials.forEach((m, i) => {
          const d = defaults[i];
          m.color.copy(d.color);
          if (!isOutside && state.palette === "atlas")
            m.color.set(manifest.systems[p.system].color);
          const transparent = ghost || fading || d.transparent;
          if (m.transparent !== transparent) {
            m.transparent = transparent;
            m.needsUpdate = true;
          }
          m.opacity = ghost ? 0.09 : d.opacity * alpha;
          m.depthWrite = ghost || fading ? false : d.depthWrite;
          m.emissive.setHex(p.id === state.selected ? 0x20190c : 0);
          m.emissiveIntensity = 0.28;
        });
      }
      place(entry, state);
      entry.goal = Number(state.open[p.control || p.id] || 0);
    }
    invalidate();
  }
  let gesture = null;
  function draw() {
    requestAnimationFrame(draw);
    if (!current || document.hidden) return;
    let moving = false;
    const desired = Number(current.spread);
    if (spreadAmount !== desired) {
      const step = reduced ? 1 : 0.095;
      spreadAmount +=
        Math.sign(desired - spreadAmount) *
        Math.min(step, Math.abs(desired - spreadAmount));
      for (const entry of pieces.values()) place(entry, current);
      floor.visible = spreadAmount < 0.01;
      resize();
      moving = true;
    }
    for (const entry of pieces.values()) {
      if (!entry.action || entry.value === entry.goal) continue;
      const step = reduced || gesture?.active ? 1 : 0.072;
      entry.value +=
        Math.sign(entry.goal - entry.value) *
        Math.min(step, Math.abs(entry.goal - entry.value));
      entry.action.time = entry.value * entry.action.getClip().duration;
      moving = true;
    }
    if (!dirty && !moving) return;
    mixer.update(0);
    world.updateMatrixWorld(true);
    const selected = pieces.get(current.selected);
    const pin = document.getElementById("pin");
    pin.hidden = !selected || !selected.node.visible;
    if (!pin.hidden) {
      const pt = new THREE.Box3()
        .setFromObject(selected.node, true)
        .getCenter(new THREE.Vector3())
        .project(camera);
      pin.style.left = (pt.x + 1) * 50 + "%";
      pin.style.top = (1 - pt.y) * 50 + "%";
    }
    if (current.labels) {
      const landmarks = current.spread
        ? manifest.parts
            .filter((p) => pieces.get(p.id).node.visible)
            .slice(current.labelPage * 4, current.labelPage * 4 + 4)
            .map((p) => p.id)
        : current.view === "inside" || current.opacity < 0.5
          ? manifest.parts
              .filter((p) => p.system !== "exterior")
              .filter(
                (p, i, a) => a.findIndex((q) => q.system === p.system) === i,
              )
              .map((p) => p.id)
          : manifest.landmarks || [manifest.focus];
      const ids = new Set([
        current.selected,
        ...(current.spread ? [] : Object.keys(current.moved).reverse()),
        ...landmarks,
      ]);
      const visible = [];
      for (const id of ids) {
        const entry = pieces.get(id);
        if (
          !entry?.node.visible ||
          (current.view === "inside" &&
            current.system !== "all" &&
            entry.p.system !== current.system)
        )
          continue;
        const pt = entry.anchor();
        pt.project(camera);
        visible.push({
          id,
          x: ((pt.x + 1) * host.clientWidth) / 2,
          y: ((1 - pt.y) * host.clientHeight) / 2,
        });
      }
      drawLabels(visible, current.selected, true);
    } else drawLabels([], null, false);
    const px = (host.clientWidth * camera.zoom) / (camera.right - camera.left);
    const units =
      [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100].find((n) => n * px >= 30) ??
      100;
    document.getElementById("scale-bar").style.width = units * px + "px";
    document.getElementById("scale-text").textContent = units + " mm";
    renderer.render(world, camera);
    dirty = false;
  }
  draw();
  document.addEventListener("visibilitychange", invalidate);
  const ray = new THREE.Raycaster();
  function rayAt(e) {
    const r = host.getBoundingClientRect();
    ray.setFromCamera(
      new THREE.Vector2(
        ((e.clientX - r.left) / r.width) * 2 - 1,
        1 - ((e.clientY - r.top) / r.height) * 2,
      ),
      camera,
    );
  }
  function pick(e) {
    rayAt(e);
    const candidates = [];
    for (const item of pieces.values()) {
      if (
        !item.node.visible ||
        (current.view === "inside" &&
          current.system !== "all" &&
          current.system !== item.p.system)
      )
        continue;
      for (const m of item.meshes) candidates.push(m.object);
    }
    const hits = ray.intersectObjects(candidates, false);
    if (current.opacity <= 0.35 && !current.spread) {
      const organ = hits.find(
        (h) => pieces.get(h.object.userData.pick).p.system !== "exterior",
      );
      if (organ) return organ.object.userData.pick;
    }
    return hits[0]?.object.userData.pick;
  }
  const pointers = new Set();
  let tap = null;
  function stopGesture(cancel) {
    if (gesture?.active) events.endGesture(cancel);
    gesture = null;
    controls.enableRotate = true;
  }
  function beginPointer(e) {
    if (e.button !== 0 && e.pointerType === "mouse") return;
    pointers.add(e.pointerId);
    if (pointers.size > 1) {
      stopGesture(true);
      tap = null;
      return;
    }
    if (!current) return;
    const label = e.target.closest?.("[data-label]");
    rayAt(e);
    const id = label?.dataset.label || pick(e);
    tap = { x: e.clientX, y: e.clientY, id: e.pointerId, part: id };
    if (!id) return;
    const entry = pieces.get(id);
    const plane = new THREE.Plane().setFromNormalAndCoplanarPoint(
      camera.getWorldDirection(new THREE.Vector3()),
      entry.holder.getWorldPosition(new THREE.Vector3()),
    );
    const point = ray.ray.intersectPlane(plane, new THREE.Vector3());
    const center = entry.holder
      .getWorldPosition(new THREE.Vector3())
      .project(camera);
    const origin = target.clone().project(camera);
    const articulate =
      !current.spread &&
      entry.p.system === "exterior" &&
      manifest.controls[entry.p.control || id] &&
      !(current.moveTool && current.selected === id) &&
      !current.moved[id];
    gesture = {
      id,
      pointer: e.pointerId,
      x: e.clientX,
      y: e.clientY,
      point,
      plane,
      active: false,
      articulate,
      side: center.x >= origin.x ? 1 : -1,
      base: Number(current.open[entry.p.control || id] || 0),
      offset: vector(current.moved[id]?.offset || [0, 0, 0]),
    };
    controls.enableRotate = false;
    // OrbitControls still receives the first finger so a second can start a pinch.
    (label || renderer.domElement).setPointerCapture(e.pointerId);
  }
  function movePointer(e) {
    if (!gesture || gesture.pointer !== e.pointerId) return;
    const g = gesture,
      dx = e.clientX - g.x,
      dy = e.clientY - g.y;
    if (!g.active) {
      if (Math.hypot(dx, dy) < 5) return;
      g.active = true;
      tap = null;
      g.axis = Math.abs(dy) >= Math.abs(dx) * 0.7 ? "vertical" : "lateral";
      events.beginGesture(g.id);
    }
    if (g.articulate) {
      const distance = g.axis === "vertical" ? -dy : dx * g.side;
      const travel = THREE.MathUtils.clamp(host.clientHeight * 0.32, 76, 150);
      events.pose(
        g.id,
        THREE.MathUtils.clamp(g.base + distance / travel, 0, 1),
      );
    } else {
      rayAt(e);
      const end = ray.ray.intersectPlane(g.plane, new THREE.Vector3());
      if (!end || !g.point) return;
      const parent = pieces.get(g.id).holder.parent;
      const delta = parent
        .worldToLocal(end)
        .sub(parent.worldToLocal(g.point.clone()));
      events.place(g.id, g.offset.clone().add(delta).toArray());
    }
  }
  function finish(e) {
    if (!pointers.delete(e.pointerId)) return;
    const click =
      tap?.id === e.pointerId &&
      Math.hypot(e.clientX - tap.x, e.clientY - tap.y) < 5;
    if (gesture?.pointer === e.pointerId) stopGesture(e.type !== "pointerup");
    if (click && e.type === "pointerup" && tap.part) events.select(tap.part);
    tap = null;
  }
  for (const surface of [host, document.getElementById("callouts")]) {
    surface.addEventListener("pointerdown", beginPointer, true);
    surface.addEventListener("pointermove", movePointer);
    surface.addEventListener("pointerup", finish);
    surface.addEventListener("pointercancel", finish);
    surface.addEventListener("lostpointercapture", finish);
  }
  return {
    apply,
    portrait,
    home,
    zoom(factor) {
      camera.zoom = THREE.MathUtils.clamp(camera.zoom * factor, 0.45, 6);
      camera.updateProjectionMatrix();
      invalidate();
    },
    detachVector(id) {
      const p = pieces.get(id),
        v = p.center.clone().sub(target);
      if (v.length() < 0.2) v.set(-1, 0.5, 0);
      return v
        .normalize()
        .multiplyScalar(manifest.view.radius * 0.56)
        .toArray();
    },
  };
}
