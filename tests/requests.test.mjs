import test from "node:test";
import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import jpeg from "jpeg-js";
import { handle } from "../backend/requests.mjs";

const ownerKey = "local-contract-test-".repeat(3);
const sample = jpeg.encode({
  width: 2,
  height: 2,
  data: Buffer.alloc(16, 255),
}).data;
const marker = Buffer.from("PRIVATE PHOTO COMMENT");
const segment = Buffer.from([255, 254, 0, marker.length + 2]);
const photo = Buffer.concat([
  sample.subarray(0, 2),
  segment,
  marker,
  sample.subarray(2),
]).toString("base64");
const submission = () => ({
  id: Date.now() + "-" + randomUUID(),
  photo,
  permission: true,
  name: "Possible mantis",
  note: "Look at its forelegs.",
});
function fixture() {
  const records = new Map();
  const store = {
    async set(key, data, options) {
      if (records.has(key) && options.onlyIfNew) return { modified: false };
      records.set(key, { data, metadata: options.metadata });
      return { modified: true };
    },
    async getMetadata(key) {
      return records.get(key) ?? null;
    },
    async get(key, { type }) {
      const record = records.get(key);
      if (!record) return null;
      return type === "arrayBuffer" ? record.data.arrayBuffer() : record.data;
    },
    async setJSON(key, value, options) {
      return this.set(key, value, options);
    },
    async list({ prefix }) {
      return {
        blobs: Array.from(records.keys())
          .filter((k) => k.startsWith(prefix))
          .map((key) => ({ key })),
      };
    },
  };
  return (path, data, token, overrides = {}) => {
    const owner = path.startsWith("/api/review");
    const req = new Request("https://local.invalid" + path, {
      method: data ? "POST" : "GET",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: "Bearer " + token } : {}),
        ...overrides.headers,
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    return handle(
      req,
      { ownerKey: overrides.ownerKey ?? ownerKey, getStore: () => store },
      owner,
    );
  };
}
test("Private requests require a configured owner and explicit consent", async () => {
  const call = fixture(),
    input = submission();
  assert.equal((await call("/api/review")).status, 401);
  assert.equal(
    (await call("/api/review?id=" + input.id + "&view=photo", null, "wrong"))
      .status,
    401,
  );
  assert.equal(
    (await call("/api/requests", input, null, { ownerKey: "" })).status,
    503,
  );
  assert.equal(
    (await call("/api/requests", { ...input, permission: false })).status,
    400,
  );
  assert.equal(
    (await call("/api/requests", { ...input, photo: "/9j/invalid" })).status,
    400,
  );
  assert.equal(
    (await call("/api/requests", { ...input, note: "x".repeat(241) })).status,
    400,
  );
  assert.equal(
    (
      await call("/api/requests", input, null, {
        headers: { origin: "https://other.invalid" },
      })
    ).status,
    403,
  );
  assert.equal(
    (await call("/api/requests", { ...input, photo: "a".repeat(2_600_001) }))
      .status,
    413,
  );
  assert.deepEqual(
    (await (await call("/api/review", null, ownerKey)).json()).items,
    [],
  );
});
test("Submission, private preview, immutable approval and private build handoff", async () => {
  const call = fixture(),
    input = submission(),
    path = "/api/review?id=" + input.id;
  assert.equal((await call("/api/requests", input)).status, 201);
  assert.equal(
    (await call("/api/requests", { ...input, name: "Duplicate" })).status,
    201,
  );
  const listed = await call("/api/review", null, ownerKey);
  assert.match(listed.headers.get("cache-control"), /no-store/);
  const { items } = await listed.json();
  assert.equal(items.length, 1);
  assert.equal(items[0].name, input.name);
  const photo = Buffer.from(
    await (await call(path + "&view=photo", null, ownerKey)).arrayBuffer(),
  );
  assert.equal(jpeg.decode(photo).width, 2);
  assert.equal(photo.includes(marker), false);
  assert.equal((await call(path + "&view=brief", null, ownerKey)).status, 409);
  const decision = {
    status: "approved",
    speciesId: "european-mantis",
    name: "European praying mantis",
    focus: "Opening the grasping legs",
  };
  assert.equal(
    (await call(path, { ...decision, speciesId: "../bad" }, ownerKey)).status,
    400,
  );
  assert.equal((await call(path, decision, ownerKey)).status, 200);
  assert.equal(
    (await call(path, { status: "declined" }, ownerKey)).status,
    409,
  );
  const brief = await (await call(path + "&view=brief", null, ownerKey)).json();
  assert.equal(brief.decision.status, "approved");
  assert.equal(brief.observation.note, input.note);
  assert.equal(brief.photo, photo.toString("base64"));
  assert.equal(brief.format, "anybug-request-v1");
});
test("Declined suggestions cannot become build packets", async () => {
  const call = fixture(),
    input = submission(),
    path = "/api/review?id=" + input.id;
  await call("/api/requests", input);
  assert.equal(
    (await call(path, { status: "declined" }, ownerKey)).status,
    200,
  );
  assert.equal((await call(path + "&view=brief", null, ownerKey)).status, 409);
});
