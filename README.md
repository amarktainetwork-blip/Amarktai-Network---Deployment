# Amarktai Network (Production)

This repository is **production-wired for same-origin deployment** behind Nginx:

- Frontend served by Nginx at `/`
- Backend reverse-proxied by Nginx under `/api`
- WebSocket endpoint: `/api/ws`
- Frontend HTTP base: `API_BASE="/api"`
- Frontend WS base: `ws(s)://{location.host}/api/ws`
- Static assets are local in `frontend/public/assets/` and referenced as `/assets/...`

## Key paths

- Backend app: `backend/server.py` (FastAPI)
- Frontend: `frontend/` (build output depends on your frontend tooling)
- Shared contract:
  - Health: `/api/health/*`
  - Mode: `/api/system/mode`
  - Wallet: `/api/wallet/*`

## Notes

- Do not hardcode localhost or external asset hosts.
- Keep Nginx configured to support WebSocket upgrade for `/api/ws`.
