import { BACKEND_URL } from "../config";
import { getWebview, getDomAndUrlFromWebview } from "../services/webviewDom";

type PlanAction = { kind: string; selector?: string; value?: any };
export type PlanItem = { selector: string; plan: { actions: PlanAction[]; meta?: any } };

export type F1Response = {
  ok: boolean;
  allPlanHomePageCandidates?: PlanItem[];
  checkHtmlIfChanged?: { changed: boolean; reason?: string; before_hash?: string; after_hash?: string } | null;
  createCandidates?: { selectorsInOrder: string[]; mapping: any };
};

// Plan/detect API. Prefer raw HTML; backend filters internally.
async function callF1(payload: {
  // Operation mode (mandatory): 'allPlanHomePageCandidates' | 'planCheckHtmlIfChanged'
  op: 'allPlanHomePageCandidates' | 'planCheckHtmlIfChanged';
  html: string;
  name?: string;
  // Preferred raw detection inputs (UI no longer filters):
  prev_html?: string | null;
  current_html?: string | null;
  // Legacy filtered fields are still accepted by backend, but not used here.
  prev_filtered_html?: string | null;
  current_filtered_html?: string | null;
  wait_ms?: number;
}): Promise<F1Response> {
  const res = await fetch(`${BACKEND_URL}/api/f1`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`F1 failed: ${res.status}`);
  return res.json();
}

function clickInWebview(selector: string): Promise<boolean> {
  const wv: any = getWebview();
  if (!wv) return Promise.resolve(false);
  const script = `(() => {
    try {
      const sel = ${JSON.stringify(selector)};
      const byXpath = (xp) => {
        try { const r = document.evaluate(xp, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null); return r.singleNodeValue; } catch { return null; }
      };
      const normalize = (s) => (s || '').replace(/\s+/g, ' ').trim();
      const isVisible = (e) => {
        try { const r = e.getBoundingClientRect(); return r && r.width > 0 && r.height > 0; } catch { return true; }
      };
      let el = null;
      if (sel.startsWith('text:')) {
        const t = normalize(sel.slice(5));
        const candidates = Array.from(document.querySelectorAll('button, a, [role="button"], [data-component-name="Button"], [data-lov-name="Button"]'));
        el = candidates.find(e => normalize(e.textContent) === t && isVisible(e)) ||
             candidates.find(e => normalize(e.textContent).includes(t) && isVisible(e)) || null;
      } else if (sel.startsWith('css:')) {
        const css = sel.slice(4).trim();
        try { el = document.querySelector(css); } catch {}
      } else if (sel.startsWith('xpath:')) {
        const xp = sel.slice(6).trim();
        el = byXpath(xp);
      } else if (sel.startsWith('//') || sel.startsWith('(//')) {
        el = byXpath(sel);
      } else {
        try { el = document.querySelector(sel); } catch {}
      }
      if (el) {
        try { el.scrollIntoView({ block: 'center', inline: 'center' }); } catch {}
        try { el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window })); } catch {}
        try { if (el.click) el.click(); } catch {}
        return true;
      }
      return false;
    } catch { return false; }
  })();`;
  return wv.executeJavaScript(script, true);
}

function waitForWebviewEventOrTimeout(timeoutMs: number): Promise<"event" | "timeout"> {
  const wv: any = getWebview();
  return new Promise((resolve) => {
    let done = false;
    let t: any;
    const onStop = () => finish("event");
    const onNav = () => finish("event");
    const onInPage = () => finish("event");
    const onFrameFinish = () => finish("event");
    const onDom = () => finish("event");
    const cleanup = () => {
      try {
        wv?.removeEventListener?.("did-stop-loading", onStop);
        wv?.removeEventListener?.("did-navigate", onNav);
        wv?.removeEventListener?.("did-navigate-in-page", onInPage);
        wv?.removeEventListener?.("did-frame-finish-load", onFrameFinish);
        wv?.removeEventListener?.("dom-ready", onDom);
      } catch {}
      try { if (t) clearTimeout(t); } catch {}
    };
    const finish = (k: "event" | "timeout") => { if (done) return; done = true; cleanup(); resolve(k); };
    try {
      wv?.addEventListener?.("did-stop-loading", onStop, { once: true });
      wv?.addEventListener?.("did-navigate", onNav, { once: true });
      wv?.addEventListener?.("did-navigate-in-page", onInPage, { once: true });
      wv?.addEventListener?.("did-frame-finish-load", onFrameFinish, { once: true });
      wv?.addEventListener?.("dom-ready", onDom, { once: true });
    } catch {}
    t = setTimeout(() => finish("timeout"), Math.max(0, timeoutMs || 0));
  });
}

export async function runFindHomePageSF(opts?: { waitAfterClickMs?: number; name?: string; log?: (msg: string) => void; }) {
  const log = opts?.log || (() => {});
  const waitMs = Math.max(0, opts?.waitAfterClickMs ?? 800);

  // 1) Capture raw HTML before
  const before = await getDomAndUrlFromWebview(msg => log(`[WV] ${msg}`));
  const rawBefore = before.html || "";
  let prevUrl = before.url || "";
  if (!rawBefore) throw new Error("webview HTML not available");
  log(`F1 initial capture: html_len=${rawBefore.length}`);

  // 2) Planning: decoupled and explicit.
  // First, get the plan list (for count + optional selector traceability).
  log(`F1 request -> allPlanHomePageCandidates`);
  const planListRes = await callF1({ op: 'allPlanHomePageCandidates', html: rawBefore, name: opts?.name || "F1", wait_ms: 0 });
  log(`F1 response <- ok=${!!planListRes?.ok} keys=${Object.keys(planListRes||{}).join(',')}`);
  const initialPlans = Array.isArray(planListRes.allPlanHomePageCandidates) ? planListRes.allPlanHomePageCandidates : [];
  const total = initialPlans.length;
  if (!total) return { ok: false, reason: "no-candidates" };
  const selectorsInOrder = planListRes.createCandidates?.selectorsInOrder || [];
  log(`F1 planList: total=${total}`);
  if (selectorsInOrder.length) {
    log(`F1 selectorsInOrder (${selectorsInOrder.length}):`);
    selectorsInOrder.forEach((s, idx) => log(`F1   [${idx}] ${s}`));
  }
  const mapping: any = planListRes.createCandidates?.mapping;
  const mcands: any[] = Array.isArray(mapping?.candidates) ? mapping.candidates : [];
  if (mcands.length) {
    log(`F1 mapping candidates (${mcands.length}) [type,text,score,css#,heur#]:`);
    mcands.slice(0, 10).forEach((c: any, idx: number) => {
      const cssN = Array.isArray(c?.selectors?.css) ? c.selectors.css.length : 0;
      const heurN = Array.isArray(c?.selectors?.heuristic) ? c.selectors.heuristic.length : 0;
      const t = (c?.text || '').toString().slice(0, 60);
      log(`F1   #${idx} ${c?.type||'*'} | "${t}" | score=${c?.score ?? ''} | css=${cssN} heur=${heurN}`);
    });
  }

  let prevRaw = rawBefore;
  for (let i = 0; i < total; i++) {
    const item = initialPlans[i];
    if (!item) { log(`F1 plan[${i}] missing`); continue; }
    log(`F1 try [${i+1}/${total}] selector=${item.selector}`);
    const actions = (item.plan?.actions || []) as PlanAction[];
    if (!actions.length) {
      log(`F1 plan[${i}] has no actions`);
    } else {
      log(`F1 plan[${i}] actions=${JSON.stringify(actions)}`);
    }
    // Execute only click actions for navigation
    for (const act of actions) {
      if (String(act.kind).toLowerCase() === "click" && act.selector) {
        const ok = await clickInWebview(act.selector);
    log(`F1 plan[${i}] selector=${act.selector} click -> ${ok ? "ok" : "fail"}`);
      }
    }
    const waited = await waitForWebviewEventOrTimeout(waitMs);
    log(`F1 wait result: ${waited}${waited === 'timeout' ? ' (no nav event; continuing)' : ''}`);

    const after = await getDomAndUrlFromWebview(msg => log(`[WV] ${msg}`));
    const rawAfter = after.html || "";
    const urlAfter = after.url || "";
    log(`F1 after capture: html_len=${rawAfter.length}`);
    if (prevUrl && urlAfter && prevUrl !== urlAfter) {
      log(`F1 URL changed: ${prevUrl} -> ${urlAfter}`);
    }
    // 3) Ask backend: "did page change?" (detector call)
    // UI now sends raw prev/current; backend filters internally and returns checkHtmlIfChanged.
    log(`F1 request -> planCheckHtmlIfChanged`);
    const detect = await callF1({
      op: 'planCheckHtmlIfChanged',
      html: rawAfter,
      name: opts?.name || "F1",
      prev_html: prevRaw,
      current_html: rawAfter,
      wait_ms: 0,
    });
    log(`F1 response <- planCheckHtmlIfChanged ok=${!!detect?.ok}`);
    const ch = detect.checkHtmlIfChanged;
    if (ch && ch.changed) {
      log(`F1 changed at plan[${i}] selector=${item.selector} reason=${ch.reason || ''} ` +
          (ch.before_hash && ch.after_hash ? `hashes=${ch.before_hash?.slice(0,8)}->${ch.after_hash?.slice(0,8)}` : ''));
      return { ok: true, changed: true, reason: ch.reason || "changed", index: i, selector: item.selector };
    }
    log(`F1 no-change at plan[${i}]`);
    prevRaw = rawAfter;
    prevUrl = urlAfter || prevUrl;
  }
  return { ok: true, changed: false, reason: "all-tried-no-change" };
}
