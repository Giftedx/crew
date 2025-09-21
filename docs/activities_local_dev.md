# Discord Activities: Local Development

This guide helps you run a local Embedded App (Activity) and verify connectivity against this API.

## Prerequisites

- A Discord application configured for Activities (Social SDK)
- Discord client (desktop) with Activities enabled for your app
- Local API running (e.g., FastAPI from this repo)
- A tunneling tool for HTTPS URL mapping (e.g., cloudflared)

## Health probe

- API provides a lightweight endpoint for Activities local tests:
  - `GET /activities/health` → `{ "status": "ok", "component": "activities" }`
  - Optional: `GET /activities/echo` (enable with `ENABLE_ACTIVITIES_ECHO=1`) returns basic request info

Caching behavior

- For local development, Activities endpoints are never cached by the API response cache:
  - `/activities/health`
  - `/activities/echo`
- This ensures you always see real-time responses while iterating on your embedded app.

### CORS preflight (OPTIONS) for Activities

If your embedded app origin differs from the API origin (e.g., Vite at localhost:5173), browsers will send a CORS preflight (OPTIONS) request before the actual call. The API includes a minimal inline CORS handler for local development. Preflight requests are not cached.

Quick check with curl (simulated preflight):

```bash
curl -i -X OPTIONS \
  -H 'Origin: http://localhost:5173' \
  -H 'Access-Control-Request-Method: GET' \
  -H 'Access-Control-Request-Headers: x-custom-header' \
  http://localhost:8000/activities/health
```

Expected headers in the 200 OK response include:

- `Access-Control-Allow-Origin: http://localhost:5173`
- `Access-Control-Allow-Methods: GET`
- `Access-Control-Allow-Headers: x-custom-header` (or `*`)

## URL mapping (cloudflared)

- Install cloudflared (see the official instructions)
- Start a tunnel to your local API (assuming it listens on 8000):

```bash
cloudflared tunnel --url http://localhost:8000
```

- Copy the public HTTPS URL (e.g., `https://purple-bird-1234.trycloudflare.com`)
- Use this URL in your Discord Activities local development settings as the base

## Launch from the client

- Use Discord's local development flow to launch your app from the client
- Point your Activity pages at the tunneled URL (e.g., `${PUBLIC_URL}/activities/health` for a trivial probe)

## Logging & debugging

- Check API logs for requests to `/activities/health`
- Open browser developer tools in your embedded web app
- Enable detailed console logs during development

## References

- See `docs/resources_index.md` → Discord Activities (Embedded Apps) for the full set of official guides:
  - Core concepts, getting started, building an Activity
  - Local development (run locally, launch from client, URL mapping, logging)
  - User actions (entry point command, open external link, invite dialog, share moment, encourage hardware acceleration)

## Example Embedded App

- Minimal Vite React example in this repo: `examples/activities/hello-activity/`
  - Configure `VITE_API_BASE` to your tunnel URL to call the API from the embedded client

## Notes

- Keep your local endpoint responses small and fast to test client wiring quickly.
- For production, ensure proper rate limiting, authentication, and logging.

## CORS for local web clients (optional)

If your Activity or web client is served from a different origin (e.g., Vite dev server), enable CORS on the API during local development:

```bash
export ENABLE_CORS=1
# Comma-separated list of allowed origins
export CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Alternatively, expose these via Settings in code (enable_cors / cors_allow_origins).

You can also enable this via the interactive setup wizard:

- Run the wizard and choose "Local web clients & Activities dev"
- Toggle "CORS for local dev" to yes, and provide allowed origins
- Optionally enable the "Activities echo debug endpoint" for troubleshooting
