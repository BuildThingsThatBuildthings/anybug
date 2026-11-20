import { createHash, timingSafeEqual } from "node:crypto";
import jpeg from "jpeg-js";

const idPattern =
  /^\d{13}-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const slugPattern = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const privateHeaders = {
  "Cache-Control": "private, no-store",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer",
};
const reply = (body, status = 200) =>
  Response.json(body, { status, headers: privateHeaders });
const photoKey = (id) => "photos/" + id;
const decisionKey = (id) => "decisions/" + id;
class InputError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}
function field(value, max, name, required = false) {
  if (
    typeof value !== "string" ||
    value.length > max ||
    /[\u0000-\u001f\u007f]/.test(value) ||
    (required && !value.trim())
  ) {
    throw new InputError(400, "Check the " + name + " field.");
  }
  return value.trim();
}
async function body(req, limit) {
  if (req.headers.get("content-type")?.split(";")[0] !== "application/json")
    throw new InputError(415, "Send JSON.");
  if (Number(req.headers.get("content-length")) > limit)
    throw new InputError(413, "The photo is too large.");
  const reader = req.body?.getReader();
  if (!reader) throw new InputError(400, "The request is empty.");
  let length = 0;
  const chunks = [];
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    length += value.byteLength;
    if (length > limit) {
      await reader.cancel();
      throw new InputError(413, "The photo is too large.");
    }
    chunks.push(value);
  }
  let data;
  try {
    data = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  } catch {
    throw new InputError(400, "Invalid request.");
  }
  if (!data || typeof data !== "object" || Array.isArray(data))
    throw new InputError(400, "Invalid request.");
  return data;
}
function cleanPhoto(encoded) {
  if (
    typeof encoded !== "string" ||
    !encoded.startsWith("/9j/") ||
    /[^A-Za-z0-9+/=]/.test(encoded)
  )
    throw new InputError(400, "Choose a valid photo.");
  try {
    const { width, height, data } = jpeg.decode(
      Buffer.from(encoded, "base64"),
      {
        useTArray: true,
        tolerantDecoding: false,
        maxResolutionInMP: 2.6,
        maxMemoryUsageInMB: 128,
      },
    );
    if (width < 1 || height < 1 || Math.max(width, height) > 1600)
      throw Error();
    // Build from pixel data alone, leaving EXIF, comments and original filenames behind.
    return new Blob([jpeg.encode({ width, height, data }, 78).data], {
      type: "image/jpeg",
    });
  } catch {
    throw new InputError(
      400,
      "This photo could not be read. Choose another image.",
    );
  }
}
function validId(id) {
  if (typeof id !== "string" || !idPattern.test(id))
    throw new InputError(400, "Invalid request reference.");
  return id;
}
function requireOwner(req, key) {
  const header = req.headers.get("authorization") || "";
  const digest = (value) => createHash("sha256").update(value).digest();
  if (!timingSafeEqual(digest(header), digest("Bearer " + key)))
    throw new InputError(401, "Enter the owner access key.");
}
async function submit(req, store) {
  if (req.method !== "POST")
    throw new InputError(405, "Use the suggestion form to send a request.");
  const input = await body(req, 2_600_000);
  const id = validId(input.id);
  if (Math.abs(Date.now() - Number(id.slice(0, 13))) > 86_400_000)
    throw new InputError(400, "Reload the form and try again.");
  if (input.permission !== true)
    throw new InputError(400, "Permission to review the photo is required.");
  const name = field(input.name, 80, "suggested name");
  const note = field(input.note, 240, "observation");
  const photo = cleanPhoto(input.photo);
  await store.set(photoKey(id), photo, {
    onlyIfNew: true,
    metadata: { name, note, receivedAt: new Date().toISOString() },
  });
  return reply({ id }, 201);
}
async function review(req, store) {
  const url = new URL(req.url);
  const id = url.searchParams.get("id");
  if (req.method === "GET" && !id) {
    const before = url.searchParams.get("before");
    if (before) validId(before);
    const listing = await store.list({ prefix: "photos/" });
    const ids = listing.blobs
      .map((item) => item.key.slice(7))
      .filter((id) => !before || id < before)
      .sort()
      .reverse();
    const page = ids.slice(0, 20);
    const items = await Promise.all(
      page.map(async (id) => {
        const [entry, decision] = await Promise.all([
          store.getMetadata(photoKey(id)),
          store.get(decisionKey(id), { type: "json" }),
        ]);
        return entry ? { id, ...entry.metadata, decision } : null;
      }),
    );
    return reply({
      items: items.filter(Boolean),
      next: ids.length > page.length ? page.at(-1) : null,
    });
  }
  validId(id);
  const entry = await store.getMetadata(photoKey(id));
  if (!entry) throw new InputError(404, "Request not found.");
  if (req.method === "POST") {
    const input = await body(req, 3500);
    if (!["approved", "declined"].includes(input.status))
      throw new InputError(400, "Choose a review decision.");
    const decision = {
      status: input.status,
      reviewedAt: new Date().toISOString(),
    };
    if (input.status === "approved") {
      decision.name = field(input.name, 100, "confirmed species name", true);
      decision.speciesId = field(input.speciesId, 70, "species ID", true);
      if (!slugPattern.test(decision.speciesId))
        throw new InputError(
          400,
          "Use lowercase letters, numbers and hyphens for the species ID.",
        );
      decision.focus = field(input.focus, 240, "build focus", true);
    }
    const { modified } = await store.setJSON(decisionKey(id), decision, {
      onlyIfNew: true,
    });
    if (!modified)
      throw new InputError(
        409,
        "This request already has a decision. Refresh the queue.",
      );
    return reply(decision);
  }
  if (req.method !== "GET") throw new InputError(405, "Method unavailable.");
  const view = url.searchParams.get("view");
  if (view === "photo") {
    const photo = await store.get(photoKey(id), { type: "arrayBuffer" });
    return new Response(photo, {
      headers: { ...privateHeaders, "Content-Type": "image/jpeg" },
    });
  }
  if (view === "brief") {
    const decision = await store.get(decisionKey(id), { type: "json" });
    if (decision?.status !== "approved")
      throw new InputError(
        409,
        "Approve the request before preparing a build.",
      );
    const bytes = await store.get(photoKey(id), { type: "arrayBuffer" });
    return reply({
      format: "anybug-request-v1",
      id,
      decision,
      observation: entry.metadata,
      photo: Buffer.from(bytes).toString("base64"),
    });
  }
  throw new InputError(400, "Unknown review action.");
}
export async function handle(req, { ownerKey, getStore }, owner = false) {
  try {
    if (!ownerKey || ownerKey.length < 32)
      throw new InputError(503, "Photo requests are temporarily closed.");
    if (owner) requireOwner(req, ownerKey);
    const origin = req.headers.get("origin");
    if (req.method === "POST" && origin && origin !== new URL(req.url).origin)
      throw new InputError(403, "Use the form on this site.");
    return await (owner ? review(req, getStore()) : submit(req, getStore()));
  } catch (error) {
    if (error instanceof InputError)
      return reply({ error: error.message }, error.status);
    console.error("Bugapedia request storage failed", error.name);
    return reply(
      { error: "The queue is temporarily unavailable. Try again." },
      503,
    );
  }
}
