import {
  cp,
  mkdir,
  readFile,
  writeFile,
  access,
  mkdtemp,
  rm,
  rename,
} from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = fileURLToPath(new URL("../", import.meta.url));
const output = path.join(root, "dist");
const staging = await mkdtemp(path.join(root, ".site-build-"));
const escape = (value) =>
  String(value).replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const read = (f) => readFile(path.join(root, f), "utf8");
try {
  const copyPublic = {
    recursive: true,
    filter: (source) => !path.basename(source).startsWith("."),
  };
  await cp(path.join(root, "site"), staging, copyPublic);
  for (const dir of ["viewer", "vendor"]) {
    await cp(path.join(root, dir), path.join(staging, dir), copyPublic);
  }
  await mkdir(path.join(staging, "explore"));
  const viewer = (await read("index.html"))
    .replace("<head>", '<head>\n    <base href="/" />')
    .replace('aria-label="AnyBug home"', 'aria-label="Back to Bugapedia"')
    .replace(
      "</main>",
      '<p><button type="button" class="guide-link" data-share="specimen">Share this specimen ↗</button></p></main><script type="module" src="/assets/share.js"></script>',
    )
    .replace(
      'src="viewer/mark.svg" />AnyBug',
      'src="viewer/mark.svg" />Bugapedia',
    );
  await writeFile(path.join(staging, "explore/index.html"), viewer);
  const catalog = JSON.parse(await read("specimens/catalog.json"));
  await mkdir(path.join(staging, "specimens"));
  await writeFile(
    path.join(staging, "specimens/catalog.json"),
    JSON.stringify(catalog),
  );
  const cards = [];
  for (const { id } of catalog) {
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id))
      throw Error("Invalid catalog ID");
    const dir = "specimens/" + id;
    const specimen = JSON.parse(await read(dir + "/anatomy.json"));
    const destination = path.join(staging, dir);
    await mkdir(destination);
    for (const file of ["anatomy.json", "specimen.glb"]) {
      await cp(path.join(root, dir, file), path.join(destination, file));
    }
    let plate = "";
    try {
      await access(path.join(root, dir, "plate.webp"));
      plate = "/" + dir + "/plate.webp";
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
    }
    if (plate)
      await cp(
        path.join(root, dir, "plate.webp"),
        path.join(destination, "plate.webp"),
      );
    cards.push(`<a class="specimen-card" href="/explore/?specimen=${id}">
      <div class="plate plate-${id}">${plate ? `<img src="${plate}" alt="" />` : "<span>Open 3D specimen</span>"}</div>
      <div class="card-notes"><div><i>${escape(specimen.scientific)}</i><h2>${escape(specimen.name)}</h2><p>${escape(specimen.lengthMm)} mm <span>·</span> ${specimen.parts.length} labeled parts</p></div><span class="open-arrow" aria-hidden="true">↗</span></div></a>`);
  }
  const library = (await read("site/index.html")).replace(
    "<!-- specimen cards -->",
    cards.join("\n"),
  );
  await writeFile(path.join(staging, "index.html"), library);
  // Only this dedicated generated directory is ever replaced.
  await rm(output, { recursive: true, force: true });
  await rename(staging, output);
  console.log("Built Bugapedia with " + catalog.length + " specimens.");
} finally {
  await rm(staging, { recursive: true, force: true });
}
