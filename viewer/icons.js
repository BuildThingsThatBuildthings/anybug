const paths = {
  book: "M3 5q5-2 9 1 4-3 9-1v14q-5-2-9 1-4-3-9-1z M12 6v14",
  bug: "M8 8q0-5 4-5t4 5 M7 9q5-5 10 0v5a5 6 0 0 1-10 0z M12 8v12 M7 11l-4-1m4 5-4 2m14-6 4-1m-4 5 4 2",
  layers: "m3 9 9-5 9 5-9 5z M3 13l9 5 9-5 M3 17l9 5 9-5",
  notes: "M5 3h13v18H5z M8 7h7 M8 11h7 M8 15h4",
  list: "M9 6h12M9 12h12M9 18h12 M3 6h1M3 12h1M3 18h1",
  rotate: "M5 9c-5 5 0 9 7 9s12-4 7-9 M14 5l4 1-2 4 M9 4a9 9 0 0 1 9 2",
  undo: "m8 5-5 5 5 5 M3 10h10c7 0 8 8 3 10",
  reset: "M4 6v5h5 M5 10a8 8 0 1 1 0 6",
  arrow: "M4 12h15m-6-6 6 6-6 6",
  swatch: "M4 6h7v12H4z M13 6h7v12h-7z",
  droplet: "M12 3c-2 4-7 8-7 12a7 7 0 0 0 14 0c0-4-5-8-7-12z",
};
export function icons(root = document) {
  root.querySelectorAll("i[data-icon]").forEach((i) => {
    if (i.firstChild) return;
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    const path = document.createElementNS(svg.namespaceURI, "path");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("aria-hidden", "true");
    path.setAttribute("d", paths[i.dataset.icon]);
    svg.append(path);
    i.append(svg);
  });
}
