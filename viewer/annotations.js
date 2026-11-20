// Arrange readable names in two margins. Lines follow the projected 3D anchors.
export function makeAnnotations(
  host,
  parts,
  onSelect,
  narrowLabelRails = false,
) {
  const overlay = document.getElementById("annotations");
  const names = document.getElementById("callouts");
  const leaders = document.getElementById("leaders");
  const lookup = new Map(
    parts.map((p, i) => [p.id, { part: p, number: i + 1 }]),
  );
  const elements = new Map();
  function make(id) {
    const { part, number } = lookup.get(id);
    const button = document.createElement("button");
    button.className = "callout";
    button.dataset.label = id;
    button.setAttribute("aria-label", "Inspect " + part.name);
    const num = document.createElement("span");
    num.textContent = String(number).padStart(2, "0");
    button.append(num, document.createTextNode(part.name));
    button.onclick = () => onSelect(id);
    const line = document.createElementNS("http://www.w3.org/2000/svg", "path");
    const dot = document.createElementNS(line.namespaceURI, "circle");
    dot.setAttribute("r", "2.5");
    dot.dataset.anchor = id;
    names.append(button);
    leaders.append(line, dot);
    const entry = { button, line, dot };
    elements.set(id, entry);
    return entry;
  }
  return function draw(labels, selected, enabled) {
    overlay.hidden = !enabled;
    if (!enabled) return;
    const w = host.clientWidth,
      h = host.clientHeight;
    const narrow = w < 520;
    const max = narrow ? 4 : 6;
    const points = labels
      .filter((l) => l.x >= 0 && l.x <= w && l.y >= 0 && l.y <= h)
      .slice(0, max)
      .sort((a, b) => a.x - b.x);
    const active = new Set(points.map((p) => p.id));
    for (const [id, entry] of elements)
      if (!active.has(id)) {
        entry.button.remove();
        entry.line.remove();
        entry.dot.remove();
        elements.delete(id);
      }
    const split = Math.ceil(points.length / 2);
    const sides = [points.slice(0, split), points.slice(split)];
    sides.forEach((items, side) => {
      items.sort((a, b) => a.y - b.y);
      const top = 63,
        bottom = h - 63,
        gap = narrow ? 36 : 40;
      let last = -Infinity;
      items.forEach((p, i) => {
        const { button, line, dot } = elements.get(p.id) || make(p.id);
        const preferred =
          narrow && narrowLabelRails ? (i === 0 ? top + 14 : bottom - 14) : p.y;
        const target = Math.min(
          bottom - (items.length - i - 1) * gap,
          Math.max(top, preferred, last + gap),
        );
        last = target;
        button.style.top = target + "px";
        button.dataset.side = side ? "right" : "left";
        button.classList.toggle("current", p.id === selected);
        const margin = narrow ? 6 : 12;
        const rail = side
          ? w - margin - button.offsetWidth
          : margin + button.offsetWidth;
        const elbow = rail + (side ? -6 : 6);
        line.setAttribute(
          "d",
          `M${rail} ${target} L${elbow} ${target} L${p.x.toFixed(1)} ${p.y.toFixed(1)}`,
        );
        dot.setAttribute("cx", p.x);
        dot.setAttribute("cy", p.y);
      });
    });
  };
}
