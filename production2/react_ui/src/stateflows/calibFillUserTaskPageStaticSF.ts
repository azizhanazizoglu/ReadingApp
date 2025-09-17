import { getDomAndUrlFromWebview } from "../services/webviewDom";
import { BACKEND_URL } from "@/config";

export type CalibStartResult = {
  ok: boolean;
  host?: string;
  task?: string;
  existing?: any;
  candidates_preview?: any[];
  inputs_found?: number;
  actions?: any[];
  ruhsat?: Record<string, string>;
  prep?: any;
  error?: string;
};

async function postCalib(op: string, body: any) {
  const url = `${BACKEND_URL}/api/calib`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ op, ...(body || {}) }),
  });
  return res.json();
}

export async function runCalibStart(task = "Yeni Trafik", log?: (m: string) => void): Promise<CalibStartResult> {
  log?.("CALIB-START | Preparing calibration session");
  const { html, url } = await getDomAndUrlFromWebview((m) => log?.(`[WV] ${m}`));
  if (!html) return { ok: false, error: "no_html" };
  log?.(`CALIB-START | Calling: ${BACKEND_URL}/api/calib op=startSession len=${html.length} url=${url}`);
  let start: any;
  try {
    start = await postCalib("startSession", { html, current_url: url, task });
    log?.(`CALIB-START | Response ok=${!!start?.ok} inputs=${start?.inputs_found ?? 'n/a'}`);
  } catch (e: any) {
    log?.(`CALIB-START | Fetch error: ${String(e?.message || e)}`);
    return { ok: false, error: "fetch_failed" };
  }
  if (!start?.ok) return { ok: false, error: start?.error || "start_failed" };
  return start as CalibStartResult;
}

export async function runCalibScan(html: string) {
  return postCalib("scanDom", { html });
}

export async function saveCalibDraft(host: string, task: string, draft: any) {
  return postCalib("saveDraft", { mapping: { host, task, draft } });
}

export async function finalizeCalib(host: string, task: string) {
  return postCalib("finalizeToConfig", { mapping: { host, task } });
}
