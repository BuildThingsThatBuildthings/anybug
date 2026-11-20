import assert from "node:assert/strict";

export async function checkBehaviors({
  page,
  base,
  frames,
  geometryImage,
  assertReassembled,
}) {
  for (const [id, time, caption] of [
    ["european-mantis", 5.64, "Reach and grasp"],
    ["seven-spot", 6.9, "Fly and land"],
  ]) {
    await page.goto(base + "?specimen=" + id);
    await page.locator("[data-ready=true]").waitFor();
    await page
      .getByRole("button", { name: "Break apart", exact: true })
      .click();
    await frames();
    const separated = await geometryImage();
    await page.getByRole("button", { name: "Behavior", exact: true }).click();
    assert.ok(await page.locator("#motion-guide").isVisible());
    assert.equal(
      await page.locator("#motion-play").textContent(),
      "Play",
      "Reduced motion waits for a deliberate play",
    );
    assert.equal(await page.locator("#motion-chapters button").count(), 3);
    assert.equal(new URL(page.url()).searchParams.get("mode"), "behavior");
    const startPose = await geometryImage();
    await page.locator("#motion-seek").fill(String(time));
    await frames();
    assert.equal(await page.locator("#motion-caption").textContent(), caption);
    assert.notDeepEqual(
      await geometryImage(),
      startPose,
      "Seeking moves the real model",
    );
    await page.locator("#motion-play").click();
    await page.waitForFunction(
      (t) => Number(document.querySelector("#motion-seek").value) > t + 0.06,
      time,
    );
    await page.locator("#motion-play").click();
    const paused = await page.locator("#motion-seek").inputValue();
    await frames();
    assert.equal(await page.locator("#motion-seek").inputValue(), paused);
    await page.locator("#motion-chapters button").first().click();
    await page.waitForFunction(
      () => document.querySelector("#motion-play").textContent === "Replay",
    );
    assert.equal(
      await page.locator("#motion-caption").textContent(),
      id === "seven-spot" ? "Walk" : "Scan",
    );
    await page.getByRole("button", { name: "Back to dissection" }).click();
    await frames();
    assert.ok(
      await page.getByRole("button", { name: "Bring together" }).isVisible(),
    );
    assert.equal(new URL(page.url()).searchParams.has("mode"), false);
    await assertReassembled(separated);
  }
}
