import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdir } from "node:fs/promises";
import { once } from "node:events";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
import { checkBehaviors } from "./behavior.mjs";
import { checkMantis } from "./mantis.mjs";
const { chromium, webkit } = await import(
  process.env.PLAYWRIGHT_MODULE || "playwright"
);
const engine = process.env.BROWSER || "chromium";
const root = fileURLToPath(new URL("../", import.meta.url));
const server = spawn(
  process.env.PYTHON || "python3",
  ["serve.py", "--port", "0"],
  { cwd: root, stdio: ["ignore", "pipe", "ignore"] },
);
let browser;
const results = process.env.REVIEW_DIR;
const digest = (b) => createHash("sha256").update(b).digest("hex");
try {
  const [data] = await once(server.stdout, "data");
  const base = data.toString().match(/http:\/\/127\.0\.0\.1:\d+\//)[0];
  const profiles = {
    desktop: { width: 1360, height: 880 },
    phone: { width: 390, height: 790 },
    tablet: { width: 820, height: 1050 },
  };
  if (results) await mkdir(results, { recursive: true });
  browser = await { chromium, webkit }[engine].launch(
    engine === "chromium" ? { args: ["--enable-unsafe-swiftshader"] } : {},
  );
  for (const name of process.env.PROFILE
    ? [process.env.PROFILE]
    : Object.keys(profiles)) {
    const touch = name !== "desktop";
    const page = await browser.newPage({
      viewport: profiles[name],
      deviceScaleFactor: 1,
      hasTouch: touch,
      isMobile: touch,
      reducedMotion: "reduce",
    });
    const errors = [],
      remote = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("request", (r) => {
      if (
        !r.url().startsWith(base) &&
        !r.url().startsWith("data:") &&
        !r.url().startsWith("blob:")
      )
        remote.push(r.url());
    });
    const shot = async (suffix) => {
      if (results)
        await page.screenshot({
          path: results + "/" + name + "-" + suffix + ".png",
          fullPage: true,
        });
    };
    const press = async (label) => {
      const btn = page.getByRole("button", { name: label, exact: true });
      if (touch) await btn.tap();
      else await btn.click();
    };
    const frames = () =>
      page.evaluate(
        () =>
          new Promise((resolve) =>
            requestAnimationFrame(() => requestAnimationFrame(resolve)),
          ),
      );
    const canvas = page.locator("canvas");
    const geometryImage = () =>
      canvas.screenshot({
        style:
          "#annotations,#pin,.scale,.view-switch,.zoom{visibility:hidden!important}",
      });
    const capture = async () => {
      await frames();
      return digest(await geometryImage());
    };
    async function assertReassembled(reference) {
      const restored = await geometryImage();
      const changed = await page.evaluate(
        async ([first, last]) => {
          async function pixels(data) {
            const img = new Image();
            img.src = "data:image/png;base64," + data;
            await img.decode();
            const c = document.createElement("canvas");
            c.width = img.width;
            c.height = img.height;
            const ctx = c.getContext("2d");
            ctx.drawImage(img, 0, 0);
            return ctx.getImageData(0, 0, c.width, c.height).data;
          }
          const [a, b] = await Promise.all([pixels(first), pixels(last)]);
          let count = 0;
          for (let i = 0; i < a.length; i += 4)
            if (
              Math.max(...[0, 1, 2].map((j) => Math.abs(a[i + j] - b[i + j]))) >
              8
            )
              count++;
          return count / (a.length / 4);
        },
        [reference.toString("base64"), restored.toString("base64")],
      );
      assert.ok(
        changed < 0.001,
        "Reassembled pixels drifted by " + 100 * changed + "%",
      );
    }
    const findPart = async (query, id) => {
      await press("Browse parts");
      await page.getByRole("searchbox").fill(query);
      const btn = page.locator('[data-part="' + id + '"]');
      if (touch) await btn.tap();
      else await btn.click();
      await frames(); // Selection markers update in the next WebGL frame.
    };
    const pin = () =>
      page.locator("#pin").evaluate((el) => [el.style.left, el.style.top]);
    await page.goto(base);
    await page.locator("[data-ready=true]").waitFor({ timeout: 45000 });
    await page.evaluate(() => document.fonts.ready);
    assert.equal(
      await page.getByRole("heading", { level: 1 }).textContent(),
      "Seven-spotted ladybug",
    );
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      true,
    );
    const assembled = await capture();
    const reference = await geometryImage();
    await shot("exterior");
    await press("Lift cover");
    await frames();
    assert.equal(
      await page.locator(".panel-title").textContent(),
      "Left wing cover",
    );
    await press("Explore left flight wing");
    const folded = await capture();
    await press("Unfold wing");
    const unfolded = await capture();
    assert.notEqual(folded, unfolded);
    await shot("unfolded");
    await press("Interior");
    await page.locator("#system").selectOption("digestive");
    await findPart("food grinder", "gizzard");
    assert.equal(
      await page.locator(".panel-title").textContent(),
      "Food grinder",
    );
    await press("Pull apart");
    await press("Turn part");
    await frames();
    const before = await pin();
    const atlas = await capture();
    await press("Natural");
    const natural = await capture();
    assert.notEqual(atlas, natural);
    assert.deepEqual(await pin(), before);
    assert.equal(await page.locator("#system").inputValue(), "digestive");
    assert.equal(
      await page.getByRole("button", { name: "Put back", exact: true }).count(),
      1,
    );
    await shot("natural");
    await press("Undo");
    assert.equal(
      await page.locator("#atlas").getAttribute("aria-pressed"),
      "true",
    );
    await press("Put back");
    await frames();
    assert.notDeepEqual(await pin(), before);
    await press("Reassemble");
    await frames();
    await assertReassembled(reference);
    const dragFrom = async (point, dx, dy) => {
      await canvas.scrollIntoViewIfNeeded();
      const p = await point.boundingBox();
      assert.ok(p, "Visible part anchor");
      const x = p.x + p.width / 2,
        y = p.y + p.height / 2;
      if (engine === "chromium" && touch) {
        const cdp = await page.context().newCDPSession(page);
        const send = (type, tx, ty) =>
          cdp.send("Input.dispatchTouchEvent", {
            type,
            touchPoints: type === "touchEnd" ? [] : [{ x: tx, y: ty, id: 0 }],
          });
        await send("touchStart", x, y);
        for (let i = 1; i <= 5; i++)
          await send("touchMove", x + (dx * i) / 5, y + (dy * i) / 5);
        await send("touchEnd");
        await cdp.detach();
      } else {
        await page.mouse.move(x, y);
        await page.mouse.down();
        await page.mouse.move(x + dx, y + dy, { steps: 5 });
        await page.mouse.up();
      }
      await frames();
    };
    // No preselection or manipulation tool: the visible shell responds to a direct drag.
    await dragFrom(page.locator('[data-anchor="cover_l"]'), 0, -38);
    assert.equal(
      await page.locator(".panel-title").textContent(),
      "Left wing cover",
    );
    const opening = Number(await page.locator("#joint").inputValue());
    assert.ok(
      opening > 10 && opening < 90,
      "Drag holds a partial opening: " + opening,
    );
    await press("Undo");
    assert.equal(
      await page.locator("[data-action=start]").count(),
      1,
      "One undo reverses the complete stroke",
    );
    await press("Lift cover");
    await press("Explore left flight wing");
    const wingLabel = page.locator('[data-label="wing_l"]');
    await dragFrom(wingLabel, 0, -38);
    const wingOpen = Number(await page.locator("#joint").inputValue());
    assert.ok(
      wingOpen > 10 && wingOpen < 90,
      "Wing label scrubs the folding mesh",
    );
    await dragFrom(wingLabel, 0, 18);
    const wingReversed = Number(await page.locator("#joint").inputValue());
    assert.ok(
      wingReversed < wingOpen && wingReversed > 0,
      "Reverse drag closes the wing continuously",
    );
    await press("Reassemble");
    // Any ordinary structure can be removed directly, then put back.
    await press("Interior");
    await findPart("brain", "brain");
    await dragFrom(page.locator("#pin"), 26, -12);
    assert.equal(
      await page.getByRole("button", { name: "Put back", exact: true }).count(),
      1,
    );
    await press("Undo");
    assert.equal(
      await page.getByRole("button", { name: "Put back", exact: true }).count(),
      0,
    );
    await press("Reassemble");
    await press("See through");
    await frames();
    assert.equal(await page.locator("#opacity").inputValue(), "22");
    assert.notEqual(await capture(), assembled);
    await shot("translucent");
    await page.locator("#opacity").focus();
    await page.keyboard.press("Home");
    assert.equal(await page.locator("#opacity-value").textContent(), "0%");
    await press("Reassemble");
    await press("Break apart");
    await frames();
    assert.equal(await page.locator("[data-key-part]").count(), 44);
    assert.equal(
      new Set(await page.locator("[data-key-part] strong").allTextContents())
        .size,
      44,
    );
    await page.locator("#key-system").selectOption("digestive");
    assert.equal(await page.locator("[data-key-part]:visible").count(), 5);
    const tile = page.locator('[data-key-part="gizzard"]');
    await tile.scrollIntoViewIfNeeded();
    await tile.locator("img").evaluate(
      (img) =>
        new Promise((resolve, reject) => {
          if (img.complete && img.naturalWidth) resolve();
          else {
            img.onload = resolve;
            img.onerror = reject;
          }
        }),
    );
    await tile.click();
    await frames();
    assert.equal(
      await page.locator(".panel-title").textContent(),
      "Food grinder",
    );
    assert.ok(await page.locator('[data-label="gizzard"]').isVisible());
    await press("Labels");
    assert.ok(await page.locator("#annotations").isHidden());
    await press("Labels");
    await page.locator("#key-system").selectOption("all");
    await press("Previous labels");
    assert.equal(
      await page.locator("#label-range").textContent(),
      "25–28 of 44",
    );
    await press("Next labels");
    await page.waitForFunction(() =>
      [...document.querySelectorAll("[data-key-part] img")].every(
        (im) => im.complete && im.naturalWidth > 0,
      ),
    );
    await shot("exploded");
    await press("Reassemble");
    assert.ok(await page.locator("#anatomy-key").isHidden());
    assert.equal(await page.locator("#opacity").inputValue(), "100");
    if (engine === "chromium" && touch) {
      const cdp = await page.context().newCDPSession(page);
      await canvas.scrollIntoViewIfNeeded();
      const r = await canvas.boundingBox();
      const cx = Math.round(r.x + r.width * 0.12),
        cy = Math.round(r.y + r.height * 0.55);
      const t = (x, y, id) => ({ x, y, id, radiusX: 3, radiusY: 3, force: 1 });
      const send = (type, touchPoints) =>
        cdp.send("Input.dispatchTouchEvent", { type, touchPoints });
      await send("touchStart", [t(cx, cy, 0)]);
      for (let i = 1; i <= 6; i++)
        await send("touchMove", [t(cx + i * 9, cy - i * 3, 0)]);
      await send("touchEnd", []);
      assert.notEqual(
        await capture(),
        assembled,
        "A finger drag orbits the specimen",
      );
      const oldScale = await page.locator("#scale-bar").getAttribute("style");
      const pinchX = Math.round(r.x + r.width * 0.52);
      await send("touchStart", [t(pinchX - 25, cy, 0), t(pinchX + 25, cy, 1)]);
      for (let i = 1; i <= 5; i++)
        await send("touchMove", [
          t(pinchX - 25 - i * 4, cy, 0),
          t(pinchX + 25 + i * 4, cy, 1),
        ]);
      await send("touchEnd", []);
      await frames();
      assert.notEqual(
        await page.locator("#scale-bar").getAttribute("style"),
        oldScale,
        "Pinch changes zoom",
      );
      await press("Reassemble");
    }
    await press("Interior");
    await findPart("brain", "brain");
    await press("Pull apart");
    await frames();
    // The projected selection marker is at the center of the detached brain.
    const marker = await page.locator("#pin").boundingBox();
    const cx = marker.x + marker.width / 2,
      cy = marker.y + marker.height / 2;
    const position = await pin();
    if (engine === "chromium" && touch) {
      const cdp = await page.context().newCDPSession(page);
      const send = (type, x, y) =>
        cdp.send("Input.dispatchTouchEvent", {
          type,
          touchPoints: type === "touchEnd" ? [] : [{ x, y, id: 0 }],
        });
      await send("touchStart", cx, cy);
      await send("touchMove", cx + 28, cy + 13);
      await send("touchEnd");
    } else {
      await page.mouse.move(cx, cy);
      await page.mouse.down();
      await page.mouse.move(cx + 28, cy + 13, { steps: 5 });
      await page.mouse.up();
    }
    await frames();
    assert.notDeepEqual(
      await pin(),
      position,
      "A detached part can be dragged",
    );
    await press("Undo");
    await frames();
    assert.deepEqual(await pin(), position, "Undo restores the drag");
    await press("Reassemble");
    await press("Interior");
    await shot("atlas");
    await press("Field guide");
    assert.ok(await page.getByRole("dialog").isVisible());
    await press("Close dialog");
    await checkMantis({
      page,
      press,
      dragFrom,
      findPart,
      capture,
      pin,
      frames,
      shot,
      geometryImage,
      assertReassembled,
    });
    await checkBehaviors({
      page,
      base,
      frames,
      geometryImage,
      assertReassembled,
    });
    assert.deepEqual(errors, []);
    assert.deepEqual(remote, []);
    for (const path of [
      ".git/config",
      "private/family.jpg",
      "specimens/seven-spot/build.py",
    ]) {
      assert.equal((await page.request.get(base + path)).status(), 404);
    }
    console.log(
      engine +
        " " +
        name +
        ": passed dissection, behavior playback for all three specimens, chapter replay, pose restoration, labels and local-only loading.",
    );
    await page.close();
  }
} finally {
  await browser?.close();
  server.kill();
}
