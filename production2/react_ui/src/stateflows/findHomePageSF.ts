import { BACKEND_URL } from "../config";
import { getWebview, getDomAndUrlFromWebview } from "../services/webviewDom";

type PlanAction = { kind: string; selector?: string; value?: any };
export type PlanItem = { selector: string; plan: { actions: PlanAction[]; meta?: any } };

export type F1Response = {
  ok: boolean;
  allPlanHomePageCandidates?: PlanItem[];
  checkHtmlIfChanged?: { changed: boolean; reason?: string; before_hash?: string; after_hash?: string } | null;
  createCandidates?: { selectorsInOrder: string[]; mapping: any };
  planLetLLMMap?: { attempt: number; maxAttempts: number; prompt: string; filteredHtml: string; hints?: any };
  error?: string;
};

// Plan/detect API. Prefer raw HTML; backend filters internally.
async function callF1(payload: {
  // Operation mode (mandatory)
  op: 'allPlanHomePageCandidates' | 'planCheckHtmlIfChanged' | 'planLetLLMMap';
  html: string;
  name?: string;
  // Preferred raw detection inputs (UI no longer filters):
  prev_html?: string | null;
  current_html?: string | null;
  // Legacy filtered fields are still accepted by backend, but not used here.
  prev_filtered_html?: string | null;
  current_filtered_html?: string | null;
  wait_ms?: number;
  // LLM planning fields
  llm_feedback?: string | null;
  llm_attempt_index?: number | null;
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
  if (!total) {
    log(`F1 planList: total=0 (no static candidates). Requesting LLM plan...`);
    const feedback = `No static candidates from mapping. selectorsInOrder=${(planListRes.createCandidates?.selectorsInOrder||[]).length}`;
    const llmRes = await callF1({
      op: 'planLetLLMMap',
      html: rawBefore,
      name: opts?.name || 'F1',
      llm_feedback: feedback,
      llm_attempt_index: 0,
      wait_ms: 0,
    });
    if (llmRes && llmRes.planLetLLMMap) {
      log(`F1 LLM plan ready: attempt ${llmRes.planLetLLMMap.attempt+1}/${llmRes.planLetLLMMap.maxAttempts}`);
      log(`F1 LLM prompt length=${llmRes.planLetLLMMap.prompt?.length || 0}, filteredHtml length=${llmRes.planLetLLMMap.filteredHtml?.length || 0}`);
      const sp = (llmRes.planLetLLMMap as any).savedPaths;
      if (sp) {
        if (sp.dir) log(`F1 LLM saved dir: ${sp.dir}`);
        if (sp.composed) log(`F1 LLM composed prompt: ${sp.composed}`);
        if (sp.default) log(`F1 LLM default prompt: ${sp.default}`);
        if (sp.feedback) log(`F1 LLM feedback file: ${sp.feedback}`);
        if (sp.filtered) log(`F1 LLM filtered html: ${sp.filtered}`);
        if (sp.meta) log(`F1 LLM meta: ${sp.meta}`);
      }
      // If backend returned a concrete selector from LLM, try it first (and its alternatives)
      const sugg: any = (llmRes.planLetLLMMap as any).llmSuggestion;
      if (sugg) {
        const type = String(sugg.selectorType || '').toLowerCase();
        const sel = String(sugg.selector || '').trim();
        const alts: string[] = Array.isArray(sugg.alternatives) ? sugg.alternatives.filter((s:any)=>typeof s==='string') : [];
        const toTry: string[] = [];
        const wrap = (t: string, v: string) => t === 'text' ? `text:${v}` : t === 'css' ? `css:${v}` : t === 'xpath' ? `xpath:${v}` : v;
        if (sel) toTry.push(wrap(type, sel));
        for (const a of alts) toTry.push(wrap(type, a));
        log(`F1 LLM suggestion: trying ${toTry.length} selectors (primary + alternatives)`);
        let prevRawS = rawBefore;
        for (let i = 0; i < toTry.length; i++) {
          const ssel = toTry[i];
          const ok = await clickInWebview(ssel);
          log(`F1 LLM-sugg try [${i+1}/${toTry.length}] selector=${ssel} click -> ${ok ? 'ok' : 'fail'}`);
          const waited = await waitForWebviewEventOrTimeout(Math.max(600, waitMs));
          log(`F1 LLM-sugg wait result: ${waited}${waited === 'timeout' ? ' (no nav event; continuing)' : ''}`);
          const afterS = await getDomAndUrlFromWebview(msg => log(`[WV] ${msg}`));
          const rawAfterS = afterS.html || "";
          const detectS = await callF1({ op: 'planCheckHtmlIfChanged', html: rawAfterS, name: opts?.name || 'F1', prev_html: prevRawS, current_html: rawAfterS, wait_ms: 0 });
          log(`F1 LLM-sugg response <- planCheckHtmlIfChanged ok=${!!detectS?.ok}`);
          const chS = detectS.checkHtmlIfChanged;
          if (chS && chS.changed) {
            log(`F1 LLM-sugg changed at selector=${ssel} reason=${chS.reason || ''} ` + (chS.before_hash && chS.after_hash ? `hashes=${chS.before_hash?.slice(0,8)}->${chS.after_hash?.slice(0,8)}` : ''));
            return { ok: true, changed: true, reason: chS.reason || 'changed', selector: ssel } as any;
          }
          prevRawS = rawAfterS;
        }
      }
      // Heuristic fallback: try known Home labels right away
      const homeLabels = ["Ana Sayfa", "Anasayfa", "Home", "Homepage", "Dashboard", "Main"];
      const llmSelectors: string[] = [];
      for (const lbl of homeLabels) {
        llmSelectors.push(`text:${lbl}`);
        llmSelectors.push(`xpath://button[normalize-space(text())='${lbl}']`);
        llmSelectors.push(`xpath://*[self::a or self::button or @role='button'][contains(normalize-space(.), '${lbl}')]`);
        llmSelectors.push(`css:[data-component-name="Button"][data-component-content*='${encodeURIComponent(lbl).replace(/'/g, "%27")}']`);
        llmSelectors.push(`css:button[aria-label='${lbl}']`);
      }
      log(`F1 LLM heuristic: trying ${llmSelectors.length} selectors for home button`);
      let prevRaw2 = rawBefore;
      for (let i = 0; i < llmSelectors.length; i++) {
        const sel = llmSelectors[i];
        const ok = await clickInWebview(sel);
        log(`F1 LLM try [${i+1}/${llmSelectors.length}] selector=${sel} click -> ${ok ? 'ok' : 'fail'}`);
        const waited = await waitForWebviewEventOrTimeout(Math.max(600, waitMs));
        log(`F1 LLM wait result: ${waited}${waited === 'timeout' ? ' (no nav event; continuing)' : ''}`);
        const after2 = await getDomAndUrlFromWebview(msg => log(`[WV] ${msg}`));
        const rawAfter2 = after2.html || "";
        const detect2 = await callF1({ op: 'planCheckHtmlIfChanged', html: rawAfter2, name: opts?.name || 'F1', prev_html: prevRaw2, current_html: rawAfter2, wait_ms: 0 });
        log(`F1 LLM response <- planCheckHtmlIfChanged ok=${!!detect2?.ok}`);
        const ch2 = detect2.checkHtmlIfChanged;
        if (ch2 && ch2.changed) {
          log(`F1 LLM changed at selector=${sel} reason=${ch2.reason || ''} ` + (ch2.before_hash && ch2.after_hash ? `hashes=${ch2.before_hash?.slice(0,8)}->${ch2.after_hash?.slice(0,8)}` : ''));
          return { ok: true, changed: true, reason: ch2.reason || 'changed', selector: sel } as any;
        }
        prevRaw2 = rawAfter2;
      }
      return { ok: true, changed: false, reason: "no-candidates-llm-tried-known-home-labels-no-change", llmPlan: llmRes.planLetLLMMap } as any;
    } else if (llmRes && llmRes.error) {
      log(`F1 LLM plan error: ${llmRes.error}`);
      return { ok: false, reason: llmRes.error } as any;
    }
    return { ok: false, reason: "no-candidates-no-llm" } as any;
  }
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
  const triedSelectors: string[] = [];
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
    triedSelectors.push(act.selector);
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
  // All candidates tried without change → request LLM fallback plan
  const feedback = `Tried selectors (in order) and no change detected:\n${triedSelectors.map((s, idx)=>`[${idx}] ${s}`).join('\n')}`;
  log(`F1 all candidates exhausted; requesting LLM plan with feedback (${triedSelectors.length} selectors).`);
  const llmRes = await callF1({
    op: 'planLetLLMMap',
    html: rawBefore,
    name: opts?.name || 'F1',
    llm_feedback: feedback,
    llm_attempt_index: 0,
    wait_ms: 0,
  });
  if (llmRes && llmRes.planLetLLMMap) {
    log(`F1 LLM plan ready: attempt ${llmRes.planLetLLMMap.attempt+1}/${llmRes.planLetLLMMap.maxAttempts}`);
    log(`F1 LLM prompt length=${llmRes.planLetLLMMap.prompt?.length || 0}, filteredHtml length=${llmRes.planLetLLMMap.filteredHtml?.length || 0}`);
    const sp = (llmRes.planLetLLMMap as any).savedPaths;
    if (sp) {
      if (sp.dir) log(`F1 LLM saved dir: ${sp.dir}`);
      if (sp.composed) log(`F1 LLM composed prompt: ${sp.composed}`);
      if (sp.default) log(`F1 LLM default prompt: ${sp.default}`);
      if (sp.feedback) log(`F1 LLM feedback file: ${sp.feedback}`);
      if (sp.filtered) log(`F1 LLM filtered html: ${sp.filtered}`);
      if (sp.meta) log(`F1 LLM meta: ${sp.meta}`);
    }
    return { ok: true, changed: false, reason: "all-tried-no-change", llmPlan: llmRes.planLetLLMMap } as any;
  } else if (llmRes && llmRes.error) {
    log(`F1 LLM plan error: ${llmRes.error}`);
    return { ok: false, reason: llmRes.error } as any;
  }
  return { ok: true, changed: false, reason: "all-tried-no-change-no-llm" } as any;
}
