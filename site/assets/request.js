const el = (id) => document.getElementById(id);
let submissionId,
  encoded,
  revision = 0;
function newId() {
  return Date.now() + "-" + crypto.randomUUID();
}
async function prepare(file) {
  if (
    !["image/jpeg", "image/png", "image/webp"].includes(file.type) ||
    file.size > 16 * 1024 * 1024
  )
    throw Error("Choose a JPEG, PNG, or WebP under 16 MB.");
  const url = URL.createObjectURL(file);
  try {
    const img = new Image();
    img.src = url;
    await img.decode();
    const scale = Math.min(
      1,
      1600 / Math.max(img.naturalWidth, img.naturalHeight),
    );
    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.round(img.naturalWidth * scale));
    canvas.height = Math.max(1, Math.round(img.naturalHeight * scale));
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "white";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg", 0.76);
  } finally {
    URL.revokeObjectURL(url);
  }
}
el("photo").onchange = async () => {
  const current = ++revision;
  encoded = null;
  submissionId = newId();
  el("preview").hidden = true;
  el("preview").removeAttribute("src");
  const file = el("photo").files[0];
  if (!file) return;
  el("message").textContent = "Preparing photo…";
  try {
    const data = await prepare(file);
    if (current !== revision) return;
    encoded = data.split(",")[1];
    el("preview").src = data;
    el("preview").hidden = false;
    el("message").textContent = "";
  } catch {
    if (current === revision) {
      el("message").textContent =
        "Choose a readable JPEG, PNG, or WebP under 16 MB.";
      el("photo").value = "";
    }
  }
};
el("request-form").onsubmit = async (event) => {
  event.preventDefault();
  if (!encoded) {
    el("message").textContent = "Choose a photo and wait for its preview.";
    return;
  }
  const form = event.currentTarget,
    fields = Array.from(form.elements);
  fields.forEach((field) => (field.disabled = true));
  el("message").textContent = "Sending…";
  try {
    const res = await fetch("/api/requests", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id: submissionId,
        name: el("name").value.trim(),
        note: el("note").value.replace(/\s+/g, " ").trim(),
        permission: el("permission").checked,
        photo: encoded,
      }),
    });
    if (!res.ok)
      throw Error(
        (await res.json().catch(() => ({}))).error ||
          (res.status === 429
            ? "Too many requests. Try again in a minute."
            : "Could not send your request. Please retry."),
      );
    const { id } = await res.json();
    el("reference").textContent = "Request reference · " + id.slice(-12);
    form.hidden = true;
    el("receipt").hidden = false;
    el("receipt").focus();
    form.reset();
    el("preview").removeAttribute("src");
    encoded = null;
  } catch (error) {
    el("message").textContent = error.message;
  } finally {
    fields.forEach((field) => (field.disabled = false));
  }
};
