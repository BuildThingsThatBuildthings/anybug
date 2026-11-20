const oldId = new URLSearchParams(location.search).get("specimen");
if (location.pathname === "/" && oldId) {
  const viewer = new URL("/explore/", location.href);
  viewer.searchParams.set("specimen", oldId);
  if (new URLSearchParams(location.search).get("mode") === "behavior")
    viewer.searchParams.set("mode", "behavior");
  location.replace(viewer);
}
const button = document.querySelector("[data-share]");
button.addEventListener("click", async () => {
  const specimen = button.dataset.share === "specimen";
  const link = new URL(specimen ? "/explore/" : "/", location.href);
  if (specimen && oldId) link.searchParams.set("specimen", oldId);
  if (specimen && document.body.classList.contains("behavior-mode"))
    link.searchParams.set("mode", "behavior");
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
