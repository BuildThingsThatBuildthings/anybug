import { api } from "../../backend/netlify.mjs";
export default (req, context) => api(req, context, false);
export const config = {
  path: "/api/requests",
  method: "POST",
  rateLimit: {
    action: "rate_limit",
    aggregateBy: ["ip", "domain"],
    windowLimit: 6,
    windowSize: 60,
  },
};
