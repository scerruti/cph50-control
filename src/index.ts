export interface Env {
  CP_USERNAME: string;
  CP_PASSWORD: string;
  CP_STATION_ID: string;
  ALERT_EMAIL: string;
  TZ_REGION: "America/Los_Angeles";
}

interface AuthResponse {
  userid?: string;
  user?: { id?: number; user_id?: number };
  sessionStorage?: { coulomb_sess?: string };
  access_token?: string;
  auth_token?: string;
}

interface ChargerListResponse {
  data?: Array<{ station_id?: string; station_name?: string }>;
}

const AUTH_URL = "https://na.chargepoint.com/users/validate";
const HOME_CHARGERS_URL = "https://na.chargepoint.com/home/get_home_chargers";
const START_SESSION_URL = "https://na.chargepoint.com/home/start_session";
const MAILCHANNELS_URL = "https://api.mailchannels.net/tx/v1/send";

const MAX_ATTEMPTS = 3;
const BASE_DELAY_MS = 2000;

async function performChargeFlow(env: Env, sendAlerts: boolean = true): Promise<{ ok: boolean; error?: string }> {
  let userId = "";
  let sessionToken = "";

  try {
    const params = new URLSearchParams();
    params.append("user_name", env.CP_USERNAME);
    params.append("user_password", env.CP_PASSWORD);

    const authRes = await fetchWithRetry(() =>
      fetch(AUTH_URL, {
        method: "POST",
        headers: {
          "content-type": "application/x-www-form-urlencoded",
          "user-agent": "ChargePoint/6.113.0 (com.chargepoint.mobile; build:1; iOS 16.0.0)"
        },
        body: params.toString(),
        redirect: "manual"
      })
    );

    const authJson = (await authRes.json()) as AuthResponse;
    userId = authJson.userid || String(authJson.user?.id || authJson.user?.user_id || "");
    sessionToken = authJson.sessionStorage?.coulomb_sess || authJson.access_token || authJson.auth_token || "";

    if (!userId || !sessionToken) {
      const msg = `Auth missing user_id or session token. Got: ${JSON.stringify({ userid: authJson.userid, hasCoulomb: !!authJson.sessionStorage?.coulomb_sess })}`;
      console.error(msg);
      if (sendAlerts) await sendAlert(env, "⚠️ URGENT: EV Charging Failed", msg);
      return { ok: false, error: msg };
    }
  } catch (err) {
    const msg = `Auth error: ${String(err)}`;
    console.error(msg);
    if (sendAlerts) await sendAlert(env, "⚠️ URGENT: EV Charging Failed", msg);
    return { ok: false, error: msg };
  }

  try {
    const startRes = await fetchWithRetry(() =>
      fetch(START_SESSION_URL, {
        method: "POST",
        headers: { "content-type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          user_id: userId,
          station_id: env.CP_STATION_ID,
          coulomb_sess: sessionToken,
          device_id: "cloudflare-worker"
        }).toString()
      })
    );

    if (!startRes.ok) {
      const body = await startRes.text();
      const msg = `Start session failed: ${startRes.status}\n${body}`;
      console.error("Start session failed", startRes.status, body);
      if (sendAlerts) await sendAlert(env, "⚠️ URGENT: EV Charging Failed", msg);
      return { ok: false, error: msg };
    }

    return { ok: true };
  } catch (err) {
    const msg = `Start session error: ${String(err)}`;
    console.error(msg);
    if (sendAlerts) await sendAlert(env, "⚠️ URGENT: EV Charging Failed", msg);
    return { ok: false, error: msg };
  }
}

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

async function fetchWithRetry(requestFn: () => Promise<Response>): Promise<Response> {
  let attempt = 0;
  let lastError: unknown;
  let lastResponse: Response | null = null;
  while (attempt < MAX_ATTEMPTS) {
    try {
      const res = await requestFn();
      if (res.ok) return res;
      lastResponse = res;
      lastError = new Error(`HTTP ${res.status}`);
    } catch (err) {
      lastError = err;
    }
    attempt += 1;
    if (attempt >= MAX_ATTEMPTS) break;
    await delay(BASE_DELAY_MS * 2 ** (attempt - 1));
  }
  // If we have a response, return it even if non-ok (let caller handle it)
  if (lastResponse) return lastResponse;
  throw lastError instanceof Error ? lastError : new Error(String(lastError));
}

function getLocalHour(timeZone: string): number {
  const now = Date.now();
  const fmt = new Intl.DateTimeFormat("en-US", { hour: "numeric", hour12: false, timeZone });
  return Number(fmt.format(now));
}

async function sendAlert(env: Env, subject: string, body: string): Promise<void> {
  const payload = {
    personalizations: [
      {
        to: [{ email: env.ALERT_EMAIL }]
      }
    ],
    from: {
      email: "no-reply@cph50-control.workers.dev",
      name: "CPH50 Control"
    },
    subject,
    content: [
      {
        type: "text/plain",
        value: body
      }
    ]
  };

  try {
    const res = await fetch(MAILCHANNELS_URL, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      console.error("MailChannels alert failed", res.status);
    }
  } catch (err) {
    console.error("MailChannels alert error", err);
  }
}

export default {
  async scheduled(_event: ScheduledEvent, env: Env): Promise<void> {
    const tz = env.TZ_REGION || "America/Los_Angeles";
    const hour = getLocalHour(tz);
    if (hour !== 6) return;

    await performChargeFlow(env, true);
  },
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    
    if (url.pathname === "/charge" && request.method === "POST") {
      if (!env.CP_STATION_ID) {
        return new Response(JSON.stringify({ error: "CP_STATION_ID not set" }), {
          status: 400,
          headers: { "content-type": "application/json" }
        });
      }
      const result = await performChargeFlow(env, false);
      return new Response(JSON.stringify(result), {
        status: result.ok ? 200 : 500,
        headers: { "content-type": "application/json" }
      });
    }

    if (url.pathname === "/setup" && request.method === "POST") {
      try {
        let authRes: Response;
        try {
          const params = new URLSearchParams();
          params.append("user_name", env.CP_USERNAME);
          params.append("user_password", env.CP_PASSWORD);

          authRes = await fetchWithRetry(() =>
            fetch(AUTH_URL, {
              method: "POST",
              headers: {
                "content-type": "application/x-www-form-urlencoded",
                "user-agent": "ChargePoint/6.113.0 (com.chargepoint.mobile; build:1; iOS 16.0.0)"
              },
              body: params.toString(),
              redirect: "manual"
            })
          );
        } catch (authErr) {
          return new Response(
            JSON.stringify({
              error: `Auth fetch failed: ${String(authErr)}`,
              usernameSet: !!env.CP_USERNAME,
              passwordSet: !!env.CP_PASSWORD,
              usernameLength: env.CP_USERNAME?.length || 0,
              passwordLength: env.CP_PASSWORD?.length || 0
            }),
            { status: 500, headers: { "content-type": "application/json" } }
          );
        }

        if (!authRes.ok) {
          const bodyText = await authRes.text();
          return new Response(
            JSON.stringify({
              error: `Auth returned ${authRes.status}`,
              status: authRes.status,
              responseBody: bodyText.slice(0, 500)
            }),
            { status: authRes.status, headers: { "content-type": "application/json" } }
          );
        }

        const authJson = (await authRes.json()) as AuthResponse;
        const userId = authJson.userid || String(authJson.user?.id || authJson.user?.user_id || "");
        const sessionToken = authJson.sessionStorage?.coulomb_sess || authJson.access_token || authJson.auth_token || "";

        // DEBUG: Return full response if auth fails
        if (!sessionToken || authJson.error) {
          return new Response(
            JSON.stringify({
              error: "Auth failed or missing session token",
              authResponse: authJson
            }),
            { status: 401, headers: { "content-type": "application/json" } }
          );
        }

        if (!userId) {
          return new Response(
            JSON.stringify({ error: `Could not find user_id in login response. Got: ${JSON.stringify(authJson)}` }),
            { status: 500, headers: { "content-type": "application/json" } }
          );
        }

        let chargerRes: Response;
        try {
          chargerRes = await fetchWithRetry(() =>
            fetch(HOME_CHARGERS_URL, {
              method: "POST",
              headers: { "content-type": "application/x-www-form-urlencoded" },
              body: new URLSearchParams({
                user_id: userId,
                coulomb_sess: sessionToken
              }).toString()
            })
          );
        } catch (chargerErr) {
          return new Response(JSON.stringify({ error: `Charger fetch failed: ${String(chargerErr)}` }), {
            status: 500,
            headers: { "content-type": "application/json" }
          });
        }

        const chargerJson = (await chargerRes.json()) as ChargerListResponse;
        const chargers = chargerJson.data || [];

        if (chargers.length === 0) {
          return new Response(JSON.stringify({ error: "No home chargers found", response: chargerJson }), {
            status: 404,
            headers: { "content-type": "application/json" }
          });
        }

        const list = chargers.map((c) => ({
          station_id: c.station_id,
          station_name: c.station_name
        }));

        return new Response(JSON.stringify({ chargers: list }, null, 2), {
          status: 200,
          headers: { "content-type": "application/json" }
        });
      } catch (err) {
        return new Response(JSON.stringify({ error: String(err) }), {
          status: 500,
          headers: { "content-type": "application/json" }
        });
      }
    }

    return new Response(JSON.stringify({ error: "Not found" }), {
      status: 404,
      headers: { "content-type": "application/json" }
    });
  }
};
