import assert from "node:assert/strict";
import { randomUUID, createHash } from "node:crypto";
import {
  readFile,
  mkdtemp,
  mkdir,
  copyFile,
  writeFile,
  stat,
  rm,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import jpeg from "jpeg-js";
const { chromium } = await import(
  process.env.PLAYWRIGHT_MODULE || "playwright"
);
const base = new URL(
  process.env.BUGAPEDIA_TEST_URL || "http://localhost:4191/",
);
assert.ok(
  ["localhost", "127.0.0.1"].includes(base.hostname),
  "Use a local test inbox.",
);
const key = process.env.BUGAPEDIA_OWNER_KEY;
assert.ok(key?.length >= 32, "Set the local owner's key first.");
const browser = await chromium.launch({
  args: ["--enable-unsafe-swiftshader"],
});
const temp = await mkdtemp(path.join(tmpdir(), "anybug-inbox-test-"));
const errors = [];
try {
  const page = await browser.newPage({
    viewport: { width: 1400, height: 960 },
    reducedMotion: "reduce",
  });
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(base.href);
  const catalog = await (
    await page.request.get(new URL("/specimens/catalog.json", base).href)
  ).json();
  assert.equal(await page.locator(".specimen-card").count(), catalog.length);
  for (const w of [1400, 390]) {
    await page.setViewportSize({ width: w, height: 900 });
    assert.ok(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    );
    assert.ok(
      await page
        .locator(".plate img")
        .evaluateAll((imgs) =>
          imgs.every((img) => img.complete && img.naturalWidth > 0),
        ),
    );
    if (process.env.REVIEW_DIR)
      await page.screenshot({
        path: path.join(process.env.REVIEW_DIR, "library-" + w + ".png"),
        fullPage: true,
      });
  }
  await page.getByRole("link", { name: /European praying mantis/i }).click();
  await page.locator('[data-ready="true"]').waitFor({ timeout: 60000 });
  await page.getByRole("button", { name: "See through" }).click();
  assert.ok(Number(await page.locator("#opacity").inputValue()) < 100);
  await page.getByRole("button", { name: "Break apart" }).click();
  assert.equal(await page.locator("[data-key-part]").count(), 59);
  await page.getByRole("button", { name: "Reassemble", exact: true }).click();
  await page.getByRole("button", { name: "Specimens", exact: true }).click();
  await page
    .getByRole("link", { name: "Seven-spotted ladybug", exact: true })
    .click();
  await page.locator('[data-ready="true"]').waitFor({ timeout: 60000 });
  assert.equal(new URL(page.url()).pathname, "/explore/");
  assert.equal(
    await page.locator("#name").textContent(),
    "Seven-spotted ladybug",
  );
  await page.getByRole("link", { name: "Back to Bugapedia" }).click();
  await page
    .getByRole("link", { name: /Suggest a bug/ })
    .first()
    .click();

  const specimen = "QA insect " + randomUUID().slice(0, 8);
  const image = jpeg.encode({
    width: 16,
    height: 12,
    data: Buffer.alloc(16 * 12 * 4, 160),
  }).data;
  await page
    .locator("#photo")
    .setInputFiles({
      name: "synthetic.jpg",
      mimeType: "image/jpeg",
      buffer: image,
    });
  await page.locator("#preview").waitFor();
  await page.locator("#name").fill(specimen);
  await page.locator("#note").fill("Inspect the hinge.");
  await page.locator("#permission").check();
  const submitted = page.waitForResponse(
    (r) => new URL(r.url()).pathname === "/api/requests",
  );
  await page.getByRole("button", { name: /Send bug request/ }).click();
  const response = await submitted;
  assert.equal(response.status(), 201, await response.text());
  const { id } = await response.json();
  await page.locator("#receipt").waitFor();
  const privatePath = new URL("/api/review?id=" + id, base);
  for (const suffix of ["", "&view=photo", "&view=brief"])
    assert.equal(
      (await page.request.get(privatePath.href + suffix)).status(),
      401,
    );
  await page.goto(new URL("/review/", base).href);
  await page.locator("#key").fill(key);
  await page.getByRole("button", { name: "Open review queue" }).click();
  const card = page
    .locator("article")
    .filter({ has: page.getByRole("heading", { name: specimen }) });
  await card.getByRole("button", { name: "View private photo" }).click();
  await card.locator("img").waitFor();
  await card.getByLabel("Species ID").fill("qa-insect");
  await card.getByRole("button", { name: "Approve for modeling" }).click();
  const download = page.waitForEvent("download");
  await card
    .getByRole("button", { name: "Download private build request" })
    .click();
  const packet = path.join(temp, "packet.json");
  await (await download).saveAs(packet);
  const data = JSON.parse(await readFile(packet, "utf8"));
  assert.equal(data.id, id);
  assert.equal(data.decision.status, "approved");
  assert.equal(data.decision.focus, "Inspect the hinge.");
  await mkdir(path.join(temp, "scripts"));
  await mkdir(path.join(temp, "specimens"));
  await copyFile(
    new URL("../scripts/import-request.py", import.meta.url),
    path.join(temp, "scripts/import-request.py"),
  );
  await writeFile(path.join(temp, "specimens/catalog.json"), "[]");
  for (let i = 0; i < 2; i++)
    execFileSync(process.env.PYTHON || "python3", [
      path.join(temp, "scripts/import-request.py"),
      packet,
    ]);
  const imported = path.join(temp, "private", "requests", id);
  assert.ok(
    (await readFile(path.join(imported, "brief.txt"), "utf8")).includes(
      "Inspect the hinge.",
    ),
  );
  const jpg = await readFile(path.join(imported, "reference.jpg"));
  assert.equal(jpeg.decode(jpg).width, 16);
  assert.equal(
    (await stat(path.join(imported, "reference.jpg"))).mode & 0o777,
    0o600,
  );
  assert.equal(
    createHash("sha256").update(jpg).digest("hex"),
    createHash("sha256")
      .update(Buffer.from(data.photo, "base64"))
      .digest("hex"),
  );
  await page.getByRole("button", { name: "Lock review" }).click();
  assert.equal(await page.locator("article").count(), 0);
  assert.deepEqual(errors, []);
  console.log(
    "Desktop and phone library, both interactive models, private photo submission, owner approval, download, repeatable private import and lock passed.",
  );
} finally {
  await browser.close();
  await rm(temp, { recursive: true, force: true });
}
