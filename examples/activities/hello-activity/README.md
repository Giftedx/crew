# Hello Activity (Vite + React)

Minimal Embedded App that pings your local API.

## Setup

```bash
cd examples/activities/hello-activity
npm install
npm run dev
```

Optionally set a public API base (tunneled):

```bash
# in another shell (example)
cloudflared tunnel --url http://localhost:8000
# then
VITE_API_BASE=https://<your-public-url> npm run dev
```

Open the dev server URL; it will call `${VITE_API_BASE}/activities/health` or `/activities/health` on same-origin.

## Debugging with echo endpoint (optional)

Enable the echo endpoint in the API and try it from the app or your browser:

```bash
# in repo root
export ENABLE_ACTIVITIES_ECHO=1
```

Then hit `${VITE_API_BASE}/activities/echo?q=ping` to see request headers and routing info.

## Quick local API setup tips

When developing this Activity locally against the Python API, enable CORS and the optional echo endpoint:

```bash
# in repo root
export ENABLE_CORS=1
export CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
export ENABLE_ACTIVITIES_ECHO=1  # optional: enables /activities/echo
```

Notes:

- Activities endpoints (`/activities/*`) are intentionally excluded from the API response cache for real-time behavior.
- You can also configure these via the setup wizard: `make setup`.
