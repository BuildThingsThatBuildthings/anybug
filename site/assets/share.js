const oldId = new URLSearchParams(location.search).get("specimen");
if (location.pathname === "/" && oldId)
  location.replace("/explore/?specimen=" + encodeURIComponent(oldId));
const button = document.querySelector("[data-share]");
button.addEventListener("click", async () => {
  const specimen = button.dataset.share === "specimen";
  const link = new URL(specimen ? "/explore/" : "/", location.href);
  if (specimen && oldId) link.searchParams.set("specimen", oldId);
  const url = link.href;
  try {
    if (navigator.share) {
      await navigator.share({ title: "Bugapedia", url });
      return;
    }
    await navigator.clipboard.writeText(url);
    button.textContent = specimen
      ? "Specimen link copied"
      : "Library link copied";
  } catch (error) {
    if (error.name !== "AbortError") window.prompt("Copy this link", url);
  }
});
