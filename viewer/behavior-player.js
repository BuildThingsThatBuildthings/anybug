// The native GLB animation is sampled at an absolute time, including after a
// seek or a chapter replay. The dissection model keeps its pose throughout.
export function makeBehaviorPlayer(sequence, scene, restoreInspection) {
  const el = (id) => document.getElementById(id);
  const { actions, duration } = sequence;
  const seek = el("motion-seek");
  const play = el("motion-play");
  const viewport = el("viewport");
  const dissectionLabel = viewport.getAttribute("aria-label");
  let visible = false,
    playing = false,
    time = 0,
    start = 0,
    end = duration;
  let request = 0,
    previous = 0,
    current = -1;
  const buttons = actions.map((action, index) => {
    const li = document.createElement("li");
    const button = document.createElement("button");
    const name = document.createElement("strong"),
      note = document.createElement("span");
    name.textContent = action.name;
    note.textContent = action.note;
    button.append(name, note);
    li.append(button);
    el("motion-chapters").append(li);
    button.onclick = () =>
      run(action.start, actions[index + 1]?.start ?? duration);
    return button;
  });
  for (const [name, url] of sequence.references) {
    const li = document.createElement("li"),
      link = document.createElement("a");
    link.textContent = name;
    link.href = url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    li.append(link);
    el("motion-sources").append(li);
  }
  seek.max = duration;
  function paint() {
    scene.sampleBehavior(time);
    seek.value = time;
    // At the final frame of an individually selected action, keep its caption.
    const instant = time === end && end < duration ? time - 0.00001 : time;
    const index = Math.max(
      0,
      actions.findLastIndex((a) => a.start <= instant),
    );
    if (current !== index) {
      current = index;
      buttons.forEach((b, i) =>
        i === index
          ? b.setAttribute("aria-current", "step")
          : b.removeAttribute("aria-current"),
      );
      el("motion-caption").textContent = actions[index].name;
    }
    const label = time.toFixed(1) + " / " + duration + " s";
    el("motion-time").textContent = label;
    seek.setAttribute("aria-valuetext", actions[index].name + ", " + label);
  }
  function pause() {
    cancelAnimationFrame(request);
    playing = false;
    previous = 0;
    play.textContent = time >= end ? "Replay" : "Play";
  }
  function tick(now) {
    if (!playing) return;
    time = Math.min(end, time + (now - previous) / 1000);
    previous = now;
    paint();
    if (time >= end) pause();
    else request = requestAnimationFrame(tick);
  }
  function resume() {
    if (playing) return;
    if (time >= end) time = start;
    playing = true;
    previous = performance.now();
    play.textContent = "Pause";
    paint();
    request = requestAnimationFrame(tick);
  }
  function run(from, to) {
    pause();
    start = from;
    end = to;
    time = from;
    resume();
  }
  function setLink(active) {
    const url = new URL(location.href);
    if (active) url.searchParams.set("mode", "behavior");
    else url.searchParams.delete("mode");
    history.replaceState(history.state, "", url);
  }
  function open() {
    if (visible) return;
    visible = true;
    setLink(true);
    document.body.classList.add("behavior-mode");
    viewport.setAttribute(
      "aria-label",
      "Animated 3D specimen. Drag to orbit or pinch to zoom.",
    );
    el("motion-guide").hidden = false;
    el("transport").hidden = false;
    el("behavior").setAttribute("aria-pressed", "true");
    el("inside").setAttribute("aria-pressed", "false");
    el("outside").setAttribute("aria-pressed", "false");
    start = time = 0;
    end = duration;
    current = -1;
    paint();
    pause();
    if (!matchMedia("(prefers-reduced-motion: reduce)").matches) resume();
  }
  function close() {
    if (!visible) return;
    pause();
    visible = false;
    setLink(false);
    scene.sampleBehavior(null);
    document.body.classList.remove("behavior-mode");
    viewport.setAttribute("aria-label", dissectionLabel);
    el("motion-guide").hidden = true;
    el("transport").hidden = true;
    el("behavior").setAttribute("aria-pressed", "false");
    restoreInspection();
  }
  el("behavior").hidden = false;
  el("behavior").onclick = open;
  el("motion-exit").onclick = () => {
    close();
    el("behavior").focus();
  };
  play.onclick = () => (playing ? pause() : resume());
  el("motion-restart").onclick = () => run(0, duration);
  seek.oninput = () => {
    const wasPlaying = playing;
    pause();
    time = Number(seek.value);
    start = 0;
    end = duration;
    paint();
    if (wasPlaying && time < end) resume();
    else pause();
  };
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) pause();
  });
  return { open, close, pause };
}
