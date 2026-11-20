import { getStore } from "@netlify/blobs";
import { handle } from "./requests.mjs";

export function api(req, context, owner) {
  const production = context.deploy?.context === "production";
  const name = production
    ? "bugapedia-requests"
    : "bugapedia-preview-" + (context.deploy?.id || "local").slice(0, 36);
  return handle(
    req,
    {
      ownerKey: Netlify.env.get("BUGAPEDIA_OWNER_KEY"),
      getStore: () => getStore({ name, consistency: "strong" }),
    },
    owner,
  );
}
