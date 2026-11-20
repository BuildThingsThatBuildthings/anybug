const el = (id) => document.getElementById(id);
let key = "",
  next = null,
  generation = 0,
  catalog = [];
const photos = new Set();
function node(tag, text) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  return element;
}
function action(label, fn) {
  const b = node("button", label);
  b.type = "button";
  b.onclick = async () => {
    b.disabled = true;
    el("message").textContent = "";
    try {
      await fn(b);
    } catch (error) {
      el("message").textContent = error.message;
    } finally {
      b.disabled = false;
    }
  };
  return b;
}
async function api(query = "", data) {
  const response = await fetch("/api/review" + query, {
    method: data ? "POST" : "GET",
    cache: "no-store",
    headers: {
      Authorization: "Bearer " + key,
      ...(data ? { "Content-Type": "application/json" } : {}),
    },
    body: data ? JSON.stringify(data) : undefined,
  });
  if (!response.ok) {
    if (response.status === 401) lock();
    throw Error(
      (await response.json().catch(() => ({}))).error ||
        "Review is temporarily unavailable.",
    );
  }
  return response;
}
function cleanup() {
  for (const url of photos) URL.revokeObjectURL(url);
  photos.clear();
}
function lock() {
  generation++;
  key = "";
  next = null;
  cleanup();
  el("key").value = "";
  el("requests").replaceChildren();
  el("message").textContent = "";
  el("unlock").hidden = false;
  el("lock").hidden = true;
  el("desk").hidden = true;
}
function input(label, value, limit) {
  const wrap = node("label", label),
    field = node("input");
  field.value = value;
  field.maxLength = limit;
  field.required = true;
  wrap.append(field);
  return { wrap, field };
}
const slug = (name) =>
  name
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 70);
function render(item) {
  const card = node("article");
  card.className = "review-card paper";
  const status = item.decision?.status || "pending";
  const time = node(
    "p",
    new Date(item.receivedAt).toLocaleDateString() + " · " + status,
  );
  time.className = "meta";
  card.append(
    time,
    node("h2", item.decision?.name || item.name || "Unidentified bug"),
  );
  if (item.note) card.append(node("p", item.note));
  const query = "?id=" + encodeURIComponent(item.id);
  const photo = node("img");
  photo.className = "preview";
  photo.hidden = true;
  photo.alt = "Private submitted bug photo";
  card.append(
    action("View private photo", async (b) => {
      const blob = await (await api(query + "&view=photo")).blob();
      if (!key || !card.isConnected) return;
      const url = URL.createObjectURL(blob);
      photos.add(url);
      photo.src = url;
      photo.hidden = false;
      b.hidden = true;
    }),
    photo,
  );
  if (status === "pending") {
    const form = node("form");
    const name = input("Confirmed species", item.name || "", 100),
      id = input("Species ID", slug(item.name || ""), 70),
      focus = input("What should the model demonstrate?", item.note || "", 240);
    id.field.pattern = "[a-z0-9]+(-[a-z0-9]+)*";
    let edited = false;
    id.field.oninput = () => {
      edited = true;
    };
    name.field.oninput = () => {
      if (!edited) id.field.value = slug(name.field.value);
    };
    const approve = node("button", "Approve for modeling");
    approve.className = "primary";
    const decline = action("Decline request", async () => {
      await api(query, { status: "declined" });
      await load();
    });
    const actions = node("div");
    actions.className = "row";
    actions.append(approve, decline);
    form.append(name.wrap, id.wrap, focus.wrap, actions);
    form.onsubmit = async (e) => {
      e.preventDefault();
      approve.disabled = true;
      decline.disabled = true;
      try {
        await api(query, {
          status: "approved",
          name: name.field.value,
          speciesId: id.field.value,
          focus: focus.field.value,
        });
        await load();
      } catch (error) {
        el("message").textContent = error.message;
        approve.disabled = false;
        decline.disabled = false;
      }
    };
    card.append(form);
  } else if (status === "approved") {
    card.append(node("p", "Build focus · " + item.decision.focus));
    card.append(
      action("Download private build request", async () => {
        const payload = await (await api(query + "&view=brief")).blob();
        if (!key || !card.isConnected) return;
        const url = URL.createObjectURL(payload),
          link = node("a");
        link.href = url;
        link.download = "bug-request-" + item.id + ".json";
        link.click();
        setTimeout(() => URL.revokeObjectURL(url), 1500);
      }),
    );
    if (catalog.some((s) => s.id === item.decision.speciesId)) {
      const link = node("a", "Open specimen in the library ↗");
      link.href =
        "/explore/?specimen=" + encodeURIComponent(item.decision.speciesId);
      card.append(link);
    } else {
      const help = node(
        "p",
        "Import the download with python3 scripts/import-request.py FILE.json. Its private folder contains the photo and the modeling brief.",
      );
      help.className = "help";
      card.append(help);
    }
  }
  return card;
}
async function load(append = false) {
  const gen = ++generation;
  const result = await (
    await api(append && next ? "?before=" + encodeURIComponent(next) : "")
  ).json();
  if (gen !== generation) return;
  if (!append) {
    cleanup();
    el("requests").replaceChildren();
  }
  // Older cards remain usable after appending the next page.
  for (const item of result.items) el("requests").append(render(item));
  if (!el("requests").childElementCount)
    el("requests").append(node("p", "No photo requests yet."));
  next = result.next;
  el("more").hidden = !next;
  el("unlock").hidden = true;
  el("desk").hidden = false;
  el("lock").hidden = false;
  el("message").textContent = "";
}
el("unlock").onsubmit = async (e) => {
  e.preventDefault();
  key = el("key").value;
  el("key").value = "";
  try {
    await load();
  } catch (error) {
    lock();
    el("message").textContent = error.message;
  }
};
el("lock").onclick = lock;
for (const [id, append] of [
  ["refresh", false],
  ["more", true],
])
  el(id).onclick = async () => {
    el(id).disabled = true;
    try {
      await load(append);
    } catch (error) {
      el("message").textContent = error.message;
    } finally {
      el(id).disabled = false;
    }
  };
window.addEventListener("pagehide", lock);
fetch("/specimens/catalog.json")
  .then((r) => r.json())
  .then((items) => {
    catalog = items;
  })
  .catch(() => {});
