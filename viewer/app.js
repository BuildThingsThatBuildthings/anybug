import { makeTray } from "./tray.js";
import { makeScene } from "./scene.js";
import { icons } from "./icons.js";

const el = (id) => document.getElementById(id);
const escape = (s) =>
  String(s).replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const initial = () => ({
  view: "outside",
  palette: "atlas",
  system: "all",
  selected: null,
  open: {},
  moved: {},
  moveTool: false,
  labels: true,
  spread: false,
  opacity: 1,
  labelPage: 0,
});
let state = initial(),
  previous = [],
  scene,
  specimen,
  catalog,
  byId,
  showTray;
let gestureBefore = null;
function remember(before) {
  previous.push(before);
  if (previous.length > 60) previous.shift();
}
const icon = (name) => '<i data-icon="' + name + '"></i>';
icons();
const button = (label, action, style = "secondary") =>
  '<button class="' +
  style +
  '" data-action="' +
  action +
  '">' +
  escape(label) +
  "</button>";
function change(fn) {
  remember(structuredClone(state));
  fn(state);
  render();
}
function select(id, fromCanvas = false) {
  const p = byId.get(id);
  if (!p || state.selected === id) return;
  change((s) => {
    s.selected = id;
    if (p.system === "exterior" && s.opacity === 0) s.opacity = 1;
    if (!fromCanvas && !s.spread)
      s.view = p.system === "exterior" ? "outside" : "inside";
    s.moveTool = false;
    if (s.spread)
      s.labelPage = Math.max(
        0,
        Math.floor(labelParts(s).findIndex((p) => p.id === id) / 4),
      );
    if (s.system !== "all" && s.system !== p.system) s.system = p.system;
  });
}
function setView(view) {
  if (state.view === view && !state.spread) return;
  change((s) => {
    s.view = view;
    s.spread = false;
    s.selected = null;
    s.moveTool = false;
    s.system = "all";
  });
}
function controlFor(id) {
  return byId.get(id)?.control || id;
}
function openControl(s, id, value) {
  id = controlFor(id);
  const controls = specimen.controls;
  if (value && controls[id]?.requires)
    openControl(s, controls[id].requires, true);
  if (Number(value) < 1)
    for (const [key, c] of Object.entries(controls))
      if (c.requires === id) s.open[key] = false;
  s.open[id] = Number(value);
}
function labelParts(s) {
  return specimen.parts.filter((p) => s.opacity > 0 || p.system !== "exterior");
}
function render() {
  scene.apply(state);
  showTray?.(state);
  const count = labelParts(state).length;
  el("label-pages").hidden = !state.spread || !state.labels;
  el("label-range").textContent =
    1 +
    state.labelPage * 4 +
    "–" +
    Math.min(count, 4 + state.labelPage * 4) +
    " of " +
    count;
  el("labels-prev").disabled = state.labelPage === 0;
  el("labels-next").disabled = 4 + state.labelPage * 4 >= count;
  el("annotations").hidden = !state.labels;
  el("labels").setAttribute("aria-pressed", String(state.labels));
  el("spread").setAttribute("aria-pressed", String(state.spread));
  el("spread").querySelector("span").textContent = state.spread
    ? "Bring together"
    : "Break apart";
  el("translucent").setAttribute("aria-pressed", String(state.opacity < 1));
  el("opacity").value = Math.round(state.opacity * 100);
  el("opacity-value").textContent = el("opacity").value + "%";
  el("opacity").setAttribute(
    "aria-valuetext",
    el("opacity-value").textContent + " opaque",
  );
  const p = byId.get(state.selected),
    inside = state.view === "inside",
    notes = el("notes");
  el("outside").setAttribute("aria-pressed", String(!inside && !state.spread));
  el("inside").setAttribute("aria-pressed", String(inside && !state.spread));
  el("undo").disabled = !previous.length;
  el("palette").hidden =
    !inside &&
    !state.spread &&
    state.opacity === 1 &&
    (!p || p.system === "exterior");
  for (const key of ["atlas", "natural"])
    el(key).setAttribute("aria-pressed", String(state.palette === key));
  el("palette-note").textContent =
    state.palette === "atlas"
      ? "Each body system has its own color."
      : "Tissue colors are approximate reconstructions.";
  el("interaction-hint").textContent = state.moveTool
    ? "Drag the selected part to move it"
    : state.spread
      ? "Drag a part to move it · Drag empty space to orbit"
      : (specimen.dragHint || "Drag a cover up to open") +
        " · Drag empty space to orbit";
  if (!p && state.spread) {
    notes.innerHTML =
      '<p class="notes-kind">Dissection</p><h2 class="panel-title">Parts of the specimen</h2><p class="description">Drag any loose part to examine it. The anatomy key below names every piece.</p><button class="primary" data-action="key">See all ' +
      specimen.parts.length +
      " parts</button>";
  } else if (!p && !inside) {
    notes.innerHTML =
      '<p class="notes-kind">Explore the specimen</p><h2 class="panel-title">' +
      escape(specimen.title) +
      '</h2><p class="description">' +
      escape(specimen.overview) +
      '</p><div class="actions"><button class="primary" data-action="start">' +
      escape(specimen.controls[specimen.focus]?.open || "Inspect part") +
      icon("arrow") +
      '</button></div><div class="factline"><span>Specimen</span><strong>' +
      escape(specimen.stage) +
      '</strong></div><div class="factline"><span>Body length</span><strong>About ' +
      specimen.lengthMm +
      ' mm</strong></div><div class="factline"><span>Selectable parts</span><strong>' +
      specimen.parts.length +
      "</strong></div>";
  } else if (!p) {
    notes.innerHTML =
      '<p class="notes-kind">Inside the specimen</p><h2 class="panel-title">Body systems</h2><p class="description">Tap an organ to see its job. Choose a system to follow its path through the body.</p>';
  } else {
    const sys = specimen.systems[p.system],
      ctrl = specimen.controls[controlFor(p.id)];
    notes.innerHTML =
      '<p class="notes-kind"><span class="system-dot" style="--dot:' +
      escape(sys.color) +
      '"></span>' +
      escape(sys.name) +
      '</p><h2 class="panel-title">' +
      escape(p.name) +
      '</h2><p class="part-sub">' +
      escape(p.term) +
      '</p><p class="description">' +
      escape(p.short) +
      "</p>";
    let actions = "";
    if (ctrl)
      actions += button(
        state.open[controlFor(p.id)] ? ctrl.close : ctrl.open,
        "articulate",
        "primary",
      );
    const child = Object.keys(specimen.controls).find(
      (k) => specimen.controls[k].requires === p.id,
    );
    if (child && state.open[controlFor(p.id)])
      actions += button(
        "Explore " + byId.get(child).name.toLowerCase(),
        "next-wing",
      );
    if (ctrl) {
      const percent = Math.round((state.open[controlFor(p.id)] || 0) * 100);
      notes.insertAdjacentHTML(
        "beforeend",
        '<label class="joint-control">Opening <input id="joint" type="range" min="0" max="100" value="' +
          percent +
          '"><output id="joint-value">' +
          percent +
          "%</output></label>",
      );
      bindRange(el("joint"), (value) => openControl(state, p.id, value / 100));
    }
    if (actions)
      notes.insertAdjacentHTML(
        "beforeend",
        '<div class="actions">' + actions + "</div>",
      );
    const moved = Boolean(state.moved[p.id]);
    notes.insertAdjacentHTML(
      "beforeend",
      '<div class="tool-row">' +
        button(moved ? "Put back" : "Pull apart", "detach") +
        button("Move part", "move") +
        (moved ? button("Turn part", "turn") : "") +
        "</div>",
    );
    notes
      .querySelector('[data-action="move"]')
      .setAttribute("aria-pressed", String(state.moveTool));
    const [source, url] = specimen.sources[p.source];
    notes.insertAdjacentHTML(
      "beforeend",
      '<details class="read-more"><summary>Look closer</summary><p>' +
        escape(p.detail) +
        "</p><small>" +
        escape(p.evidence) +
        ' · <a target="_blank" rel="noopener noreferrer" href="' +
        escape(url) +
        '">' +
        escape(source) +
        "</a></small></details>",
    );
  }
  if (inside) {
    const options = Object.entries(specimen.systems)
      .filter(([key]) => key !== "exterior")
      .map(
        ([key, sys]) =>
          '<option value="' +
          escape(key) +
          '">' +
          escape(sys.name) +
          "</option>",
      )
      .join("");
    notes.insertAdjacentHTML(
      "beforeend",
      '<label class="small-label" for="system">Focus on a system</label><select id="system"><option value="all">All internal systems</option>' +
        options +
        "</select>",
    );
    el("system").value = state.system;
    el("system").onchange = (e) =>
      change((s) => {
        s.system = e.target.value;
        s.selected = null;
        s.moveTool = false;
      });
  }
  icons(notes);
}
el("notes").addEventListener("click", (e) => {
  const action = e.target.closest("[data-action]")?.dataset.action;
  if (!action) return;
  if (action === "key") {
    el("key-heading").focus({ preventScroll: true });
    el("anatomy-key").scrollIntoView({ block: "start" });
    return;
  }
  change((s) => {
    const id = s.selected;
    if (action === "start") {
      s.selected = specimen.focus;
      if (specimen.controls[s.selected]) openControl(s, s.selected, true);
    }
    if (action === "articulate") openControl(s, id, !s.open[controlFor(id)]);
    if (action === "next-wing")
      s.selected = Object.keys(specimen.controls).find(
        (k) => specimen.controls[k].requires === id,
      );
    if (action === "detach") {
      if (s.moved[id]) {
        delete s.moved[id];
        s.moveTool = false;
      } else {
        s.moved[id] = { offset: scene.detachVector(id), turn: 0 };
        s.moveTool = true;
      }
    }
    if (action === "turn") s.moved[id].turn += Math.PI / 6;
    if (action === "move") s.moveTool = !s.moveTool;
  });
});
// Inputs preview continuously. A complete slider stroke or 3D drag is one undo.
function preview() {
  scene.apply(state);
  const percent = Math.round(state.opacity * 100);
  el("opacity").value = percent;
  el("opacity-value").textContent = percent + "%";
  el("opacity").setAttribute("aria-valuetext", percent + "% opaque");
  el("translucent").setAttribute("aria-pressed", String(state.opacity < 1));
  if (el("joint")) {
    const value = Math.round(
      (state.open[controlFor(state.selected)] || 0) * 100,
    );
    el("joint").value = value;
    el("joint-value").textContent = value + "%";
  }
}
function commitRange(before) {
  if (before) {
    remember(before);
    render();
  }
}
function bindRange(input, update) {
  let before = null;
  input.oninput = () => {
    before ??= structuredClone(state);
    update(Number(input.value));
    preview();
  };
  input.onchange = () => {
    const snapshot = before;
    before = null;
    commitRange(snapshot);
  };
}
bindRange(el("opacity"), (value) => {
  state.opacity = value / 100;
  state.labelPage = Math.min(
    state.labelPage,
    Math.max(0, Math.ceil(labelParts(state).length / 4) - 1),
  );
  if (state.view === "inside") state.view = "outside";
});
el("translucent").onclick = () =>
  change((s) => {
    s.opacity = s.opacity < 1 ? 1 : 0.22;
    if (s.view === "inside") s.view = "outside";
  });
for (const [id, step] of [
  ["labels-next", 1],
  ["labels-prev", -1],
])
  el(id).onclick = () =>
    change((s) => {
      s.labelPage += step;
      s.selected = null;
      s.moveTool = false;
    });
el("labels").onclick = () =>
  change((s) => {
    s.labels = !s.labels;
  });
el("spread").onclick = () =>
  change((s) => {
    s.spread = !s.spread;
    s.view = "outside";
    s.system = "all";
    if (s.spread) {
      s.labels = true;
      s.opacity = 1;
    }
  });
el("outside").onclick = () => setView("outside");
el("inside").onclick = () => setView("inside");
for (const mode of ["atlas", "natural"])
  el(mode).onclick = () => {
    if (state.palette !== mode) change((s) => (s.palette = mode));
  };
el("undo").onclick = () => {
  if (previous.length) {
    state = previous.pop();
    render();
  }
};
el("reset").onclick = () => {
  change((s) => Object.assign(s, initial()));
  scene.home();
};
el("zoom-out").onclick = () => scene.zoom(0.82);
el("zoom-in").onclick = () => scene.zoom(1.22);
const dialog = el("dialog");
el("close").onclick = () => dialog.close();
dialog.addEventListener("click", (e) => {
  if (e.target === dialog) dialog.close();
});
function showDialog(title) {
  el("dialog-title").textContent = title;
  dialog.showModal();
}
function listParts(query = "") {
  const field = el("part-list");
  field.replaceChildren();
  for (const [key, sys] of Object.entries(specimen.systems)) {
    const group = specimen.parts.filter(
      (p) =>
        p.system === key &&
        (p.name + " " + p.term + " " + sys.name)
          .toLowerCase()
          .includes(query.toLowerCase()),
    );
    if (!group.length) continue;
    const h = document.createElement("h3");
    h.textContent = sys.name;
    field.append(h);
    for (const p of group) {
      const b = document.createElement("button");
      b.className = "part-link";
      b.textContent = p.name;
      b.dataset.part = p.id;
      b.insertAdjacentHTML("beforeend", icon("arrow"));
      b.onclick = () => {
        dialog.close();
        select(p.id);
      };
      field.append(b);
    }
  }
  if (!field.childElementCount)
    field.textContent =
      "No matching parts. Try a body system or a shorter name.";
  icons(field);
}
el("browse").onclick = () => {
  el("dialog-body").innerHTML =
    '<input id="search" type="search" placeholder="Find a part or body system" aria-label="Search anatomical parts"><div id="part-list"></div>';
  listParts();
  showDialog("Browse parts");
  el("search").oninput = (e) => listParts(e.target.value);
};
el("species").onclick = () => {
  const body = el("dialog-body");
  body.replaceChildren();
  for (const item of catalog) {
    const link = document.createElement("a");
    link.href = "?specimen=" + encodeURIComponent(item.id);
    link.className = "part-link";
    link.textContent = item.name;
    if (item.id === specimen.id) link.setAttribute("aria-current", "page");
    body.append(link);
  }
  showDialog("Choose a specimen");
};
el("guide").onclick = () => {
  el("dialog-body").innerHTML =
    "<p>" +
    escape(
      specimen.gestureGuide ||
        "Drag a spotted cover up to lift it, or down to close it. A flight wing unfolds the same way.",
    ) +
    " Drag other structures away directly. Drag empty space to turn the specimen, and pinch to zoom.</p><p><b>Break apart</b> spreads the structures and reveals a labeled anatomy key. <b>See through</b> fades the exterior. Adjust the slider to trace the organs inside. Undo retraces one gesture at a time.</p><h3>Reading the model</h3><p>Each specimen is an educational reconstruction. “Species reference” identifies structures informed by studies of the featured species. “Comparative reconstruction” identifies details based on a related species or general insect anatomy. Natural tissue colors are approximate.</p><h3>Specimen references</h3><ul>" +
    Object.values(specimen.sources)
      .map(
        ([name, url]) =>
          '<li><a target="_blank" rel="noopener noreferrer" href="' +
          escape(url) +
          '">' +
          escape(name) +
          "</a></li>",
      )
      .join("") +
    "</ul>";
  showDialog("Field guide");
};
async function json(url) {
  const response = await fetch(url);
  if (!response.ok) throw Error("Could not load " + url);
  return response.json();
}
async function start() {
  catalog = await json("./specimens/catalog.json");
  const id =
    new URLSearchParams(location.search).get("specimen") || catalog[0].id;
  if (!catalog.some((s) => s.id === id)) throw Error("Unknown specimen");
  const base = "./specimens/" + encodeURIComponent(id) + "/";
  specimen = await json(base + "anatomy.json");
  if (specimen.gestureGuide) {
    el("viewport").setAttribute(
      "aria-label",
      "3D specimen. " +
        specimen.gestureGuide +
        " Drag empty space to orbit. Use Browse parts for keyboard selection.",
    );
    el("opacity").setAttribute("aria-label", "Body opacity");
    document.querySelector('label[for="opacity"]').textContent = "Body opacity";
  }
  byId = new Map(specimen.parts.map((p) => [p.id, p]));
  document.title = specimen.name + " · AnyBug";
  el("name").textContent = specimen.name;
  el("scientific").textContent = specimen.scientific;
  el("stage-label").textContent =
    specimen.stage + "  ·  " + specimen.lengthMm + " mm body length";
  scene = await makeScene(el("viewport"), base + specimen.model, specimen, {
    select: (id) => select(id, true),
    beginGesture(id) {
      gestureBefore = structuredClone(state);
      if (state.selected !== id) state.moveTool = false;
      state.selected = id;
      render();
    },
    pose(id, value) {
      openControl(state, id, value);
      preview();
    },
    place(id, offset) {
      state.moved[id] = { offset, turn: state.moved[id]?.turn || 0 };
      preview();
    },
    endGesture(cancel) {
      if (!gestureBefore) return;
      if (cancel) state = gestureBefore;
      else remember(gestureBefore);
      gestureBefore = null;
      render();
    },
  });
  showTray = makeTray(specimen, scene, (id) => {
    select(id, true);
    el("stage").scrollIntoView({ block: "center" });
  });
  el("status").hidden = true;
  el("stage").dataset.ready = "true";
  render();
}
const interactive = document.querySelectorAll("body button");
interactive.forEach((b) => (b.disabled = true));
start()
  .then(() => {
    interactive.forEach((b) => (b.disabled = false));
    render();
  })
  .catch((error) => {
    console.error(error);
    el("status").className = "error";
    el("status").textContent =
      "The specimen could not open. Use the local server and a browser with WebGL 2, then reload.";
  });
