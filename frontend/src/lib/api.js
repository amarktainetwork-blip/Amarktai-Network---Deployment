// frontend/src/lib/api.js
// Single source of truth for same-origin API + WebSocket URLs.
// Contract:
//   - HTTP base path: /api  (reverse-proxied by Nginx)
//   - WS endpoint:    /api/ws
export const API_BASE = "/api";

export function wsUrl(path = "/api/ws") {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}${path}`;
}
