import assert from "node:assert/strict";

export async function checkMantis({
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
}) {
  await press("Specimens");
  await page.getByRole("link", { name: "European praying mantis" }).click();
  await page.locator('[data-ready="true"]').waitFor({ timeout: 45000 });
  await frames();
  assert.match(page.url(), /specimen=european-mantis/);
  assert.equal(
    await page.locator("#name").textContent(),
    "European praying mantis",
  );
  assert.ok(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  );
  await shot("mantis");
  const assembled = await geometryImage();
  const anchor = (id) => page.locator('[data-anchor="' + id + '"]');
  const label = (id) => page.locator('[data-label="' + id + '"]');
  const opening = async () => Number(await page.locator("#joint").inputValue());

  // Grab the 3D surface before selecting a part or enabling a tool.
  await dragFrom(anchor("tibia_l"), 0, -45);
  assert.ok(
    await page.getByRole("button", { name: "Fold left front leg" }).isVisible(),
  );
  const left = await opening();
  assert.ok(left > 10 && left < 90);
  await dragFrom(label("tibia_r"), 0, -62);
  assert.ok(
    await page
      .getByRole("button", { name: "Fold right front leg" })
      .isVisible(),
  );
  const right = await opening();
  assert.ok(right > left && right < 100);
  await dragFrom(label("tibia_r"), 0, 21);
  assert.ok((await opening()) < right);
  await findPart("left grasping shin", "tibia_l");
  assert.equal(
    await opening(),
    left,
    "Moving the right leg preserves the left pose",
  );
  await shot("mantis-legs");

  await press("Reassemble");
  const opaque = await capture();
  await press("See through");
  assert.equal(
    await page.getByRole("slider", { name: "Body opacity" }).inputValue(),
    "22",
  );
  assert.notEqual(await capture(), opaque);
  await shot("mantis-translucent");
  await dragFrom(label("brain"), 26, 12);
  assert.equal(await page.locator(".panel-title").textContent(), "Brain");
  assert.ok(await page.getByRole("button", { name: "Put back" }).isVisible());
  await press("Undo");
  await page.locator("#opacity").focus();
  await page.keyboard.press("Home");
  assert.equal(await page.locator("#opacity-value").textContent(), "0%");
  await findPart("brain", "brain");
  await press("Natural");
  const natural = await capture();
  await press("Atlas");
  assert.notEqual(await capture(), natural);

  await press("Break apart");
  const records = (
    await (
      await page.request.get(
        new URL("specimens/european-mantis/anatomy.json", page.url()).href,
      )
    ).json()
  ).parts;
  const cards = page.locator("[data-key-part]");
  assert.deepEqual(
    await cards.evaluateAll((items) =>
      items.map((item) => ({
        id: item.dataset.keyPart,
        name: item.querySelector("strong").textContent,
        term: item.querySelector("span").textContent,
      })),
    ),
    records.map(({ id, name, term }) => ({ id, name, term })),
  );
  await findPart("left grasping shin", "tibia_l");
  const before = await pin();
  await dragFrom(label("tibia_l"), 29, 17);
  assert.notDeepEqual(
    await pin(),
    before,
    "An articulated part also pulls free during dissection",
  );
  await press("Undo");
  await frames();
  assert.deepEqual(await pin(), before);
  await shot("mantis-dissection");
  await press("Reassemble");
  await frames();
  await assertReassembled(assembled);
  assert.equal(await page.locator("#opacity").inputValue(), "100");
  await press("Field guide");
  assert.match(await page.getByRole("dialog").innerText(), /either front leg/i);
  await press("Close dialog");
}
