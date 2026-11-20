import { api } from "../../backend/netlify.mjs";
export default (req, context) => api(req, context, true);
export const config = {
  path: "/api/review",
  method: ["GET", "POST"],
  rateLimit: {
    action: "rate_limit",
    aggregateBy: ["ip", "domain"],
    windowLimit: 120,
    windowSize: 60,
  },
};
