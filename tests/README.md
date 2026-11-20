# Verification

The model rebuild performs a Blender-to-GLB round-trip and checks selectable geometry, source IDs, shape-key and rotation tracks, anatomical counts, and physical size.

The browser suite launches its own ephemeral loopback server. It checks continuous wing opening by direct drag, extraction without preselecting a tool, the 44-part labeled tray, adjustable shell opacity, wing deployment, the rendered change between Atlas and Natural, selection position, detached-part movement and undo, a reset within 0.1% rendered pixel variation, and local-only asset requests. The mantis checks navigate through the species chooser, drag both front legs independently, reverse a partially opened joint, verify all 59 key entries against their model records, and restore the assembled view. Chromium touch profiles also send multitouch pinch and one-finger orbit gestures. These profiles simulate device dimensions and input.

Install Node 22+, Python 3, and the optional test dependencies:

```sh
npm ci
npx playwright install chromium webkit
npm test
BROWSER=webkit PROFILE=phone npm test
```

Set `PROFILE` to `desktop`, `phone`, or `tablet` to run one layout. Set `REVIEW_DIR` to save screenshots. On Linux, Playwright may also require its documented browser system dependencies.
