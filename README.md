# CPH50 Charge Controller (Cloudflare Worker)

Cloudflare Worker that starts ChargePoint Home Flex (CPH50) charging at 6:00 AM America/Los_Angeles daily. Cron runs at 13:00 and 14:00 UTC and the worker exits unless local hour === 6.

## Setup
- Install deps: `npm install`
- Deploy first (creates the worker): `npm run deploy` (after `wrangler login`)
- Use `/setup` endpoint to discover station ID:
  - `curl -X POST https://cph50-control-worker.<account>.workers.dev/setup`
  - Copy the `station_id` from the response.
- Set secrets:
  - `npx wrangler secret put CP_USERNAME --name cph50-control-worker`
  - `npx wrangler secret put CP_PASSWORD --name cph50-control-worker`
  - `npx wrangler secret put CP_STATION_ID --name cph50-control-worker` (paste the ID from /setup)
  - `npx wrangler secret put ALERT_EMAIL --name cph50-control-worker`
- (Optional) set var in wrangler.toml or dashboard: `TZ_REGION="America/Los_Angeles"`

## Development
- Local dev: `npm run dev`

## Quality
- Lint: `npm run lint`
- Typecheck: `npm run typecheck`
- Combined: `npm run check`

## Deploy
- Deploy: `npm run deploy`
- Auth: `wrangler login`

## Behavior
- Cron: `0 13,14 * * *` (wrangler.toml) — worker self-checks TZ and runs only at 6:00 AM local.
- Auth: POST to ChargePoint login, capture access_token and cookies.
- Start charge: POST to ChargePoint action endpoint with `station_id` = `CP_STATION_ID`.
- Retry: 3 attempts with 2s/4s/8s backoff for each fetch.
- Alerts: On repeated failure of start-session, sends MailChannels email to `ALERT_EMAIL` (tokens/cookies not logged).

## Setup Endpoint
- Path: `POST /setup`
- No auth required.
- Returns: JSON list of home chargers with `station_id` and `station_name`.
- Use this to discover your station ID before configuring the secret.

## Manual Charge Endpoint
- Path: `POST /charge`
- No auth required.
- Triggers the same charge logic as the scheduled cron (authenticate, call start_session).
- Useful for testing before relying on the scheduled trigger.
- Requires `CP_STATION_ID` to be set.
- Returns: JSON with `ok: true/false` and optional `error` message.
- Example: `curl -X POST https://cph50-control-worker.<account>.workers.dev/charge`
