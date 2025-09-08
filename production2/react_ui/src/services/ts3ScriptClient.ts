import { getWebview } from './webviewDom';

export async function runBackendScript(backEndUrl: string, mapping: any, ruhsat_json: any, raw: string,
  opts: { highlight: boolean; simulateTyping: boolean; stepDelayMs: number; useDummyWhenEmpty: boolean },
  devLog?: (c: string, m: string) => void) {
  try {
    const r = await fetch(`${backEndUrl}/api/ts3/generate-script`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mapping, ruhsat_json, raw, options: {
        use_dummy_when_empty: opts.useDummyWhenEmpty,
        highlight: opts.highlight,
        simulate_typing: opts.simulateTyping,
        step_delay_ms: opts.stepDelayMs,
      }})
    });
    if (!r.ok) { devLog?.('IDX-TS3-SCRIPT-ERR', `status ${r.status}`); return { ok: false }; }
    const j = await r.json();
    if (Array.isArray(j?.logs)) j.logs.forEach((ln: string, i: number) => devLog?.('IDX-TS3-SCRIPT-PLAN', `${i.toString().padStart(3,'0')} ${ln}`));
    const webview = getWebview();
    if (!webview) throw new Error('Webview bulunamadı.');
    const res = await webview.executeJavaScript(String(j.script || ''), true);
    devLog?.('IDX-TS3-FILL', JSON.stringify({ ok: res?.ok, filled: res?.filled }));
    if (Array.isArray(res?.logs)) res.logs.forEach((ln: string, i: number) => devLog?.('IDX-TS3-TRACE', `${i.toString().padStart(3,'0')} ${ln}`));
    return res;
  } catch (e: any) {
    devLog?.('IDX-TS3-SCRIPT-ERR', String(e));
    return { ok: false, error: String(e) };
  }
}
