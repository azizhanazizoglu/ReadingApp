import { BACKEND_URL } from "../config";
import { getWebview, getDomAndUrlFromWebview } from "../services/webviewDom";

/**
 * Orchestration for navigating to a specific user task page (e.g., "Yeni Trafik").
 * Backend endpoint for goUserTaskPage is not wired yet; we operate locally (DOM only)
 * and reuse /api/f2 for change detection. Later we can swap static planning calls
 * with backend plan endpoints (plan_open_side_menu / plan_go_user_page).
 */

// ---------------- Types ----------------
export type PlanAction = { kind: string; selector?: string; value?: any };
export type PlanItem = { selector: string; plan: { actions: PlanAction[]; meta?: any } };

export interface GoUserTaskResult {
  ok: boolean;
  changed: boolean;
  reason?: string;
  taskLabel: string;
  triedSelectors: string[];
  staticCandidatesTried: number;
  sideMenuOpened?: boolean;
  llmUsed?: boolean;
  finalSelector?: string;
  attempts: number;
  logs: string[];
  error?: string;
}

// ---------------- Helpers ----------------
const SIDE_MENU_CLASS_HINTS = [
  'lucide-menu','menu-icon','hamburger','navbar-toggler','fa-bars','menu-button','sidebar-toggle','nav-toggle','mobile-menu','burger-menu'
];

function normalizeText(t: string | null | undefined): string {
  return (t || '').replace(/\s+/g, ' ').trim();
}

function getWebviewElementScript<T=any>(scriptBody: string): Promise<T> {
  const wv: any = getWebview();
  if (!wv) return Promise.resolve(undefined as any);
  return wv.executeJavaScript(scriptBody, true);
}

type ClickDetails = { ok: boolean; logs: string[] };

async function clickInWebview(selector: string): Promise<ClickDetails> {
  const esc = (s: string) => JSON.stringify(s);
  return getWebviewElementScript<ClickDetails>(`(() => {
    const sel = ${esc(selector)};
    const logs = [];
    const byXpath = (xp) => { try { const r = document.evaluate(xp, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null); return r.singleNodeValue; } catch { return null; } };
    const normalize = (s) => (s||'').replace(/\s+/g,' ').trim();
    const isVisible = (e) => { try { const r = e.getBoundingClientRect(); return r && r.width>0 && r.height>0; } catch { return true; } };
    let el = null;
    logs.push('try selector='+sel);
    if (sel.startsWith('text:')) {
      const target = normalize(sel.slice(5));
      const cands = Array.from(document.querySelectorAll('button, a, [role="button"], [data-component-name="Button"], [data-lov-name="Button"]'));
      logs.push('text target='+target+' nodes='+cands.length);
      el = cands.find(e => normalize(e.textContent) === target && isVisible(e)) || null;
    } else if (sel.startsWith('css:')) {
      const css = sel.slice(4).trim();
      try { el = document.querySelector(css); logs.push('css query ok'); } catch(e) { logs.push('css query error '+(e?.message||'')); }
    } else if (sel.startsWith('xpath:')) {
      el = byXpath(sel.slice(6).trim());
    } else if (sel.startsWith('//') || sel.startsWith('(//')) {
      el = byXpath(sel);
    } else {
      try { el = document.querySelector(sel); } catch {}
    }
    if (el) {
      logs.push('element found; dispatching events');
      try { el.scrollIntoView({block:'center', inline:'center'}); } catch {}
      try { el.dispatchEvent(new PointerEvent('pointerdown', { bubbles:true, cancelable:true })); } catch {}
      try { el.dispatchEvent(new MouseEvent('mousedown', { bubbles:true, cancelable:true })); } catch {}
      try { el.dispatchEvent(new MouseEvent('mouseup', { bubbles:true, cancelable:true })); } catch {}
      try { el.dispatchEvent(new MouseEvent('click', { bubbles:true, cancelable:true, view:window })); } catch {}
      try { if (el.click) el.click(); } catch {}
      return { ok:true, logs };
    }
    // Heuristic fallback for lucide-menu hamburger: click ancestor button/a with svg.lucide-menu
    try {
      const icons = Array.from(document.querySelectorAll('svg.lucide-menu'));
      logs.push('fallback lucide-menu count='+icons.length);
      const icon = icons[0];
      if (icon) {
        let owner = icon.closest('button, [role="button"], a, div');
        if (!owner) owner = icon.parentElement;
        if (owner) {
          try { owner.scrollIntoView({block:'center', inline:'center'}); } catch {}
          try { owner.dispatchEvent(new PointerEvent('pointerdown', { bubbles:true, cancelable:true })); } catch {}
          try { owner.dispatchEvent(new MouseEvent('mousedown', { bubbles:true, cancelable:true })); } catch {}
          try { owner.dispatchEvent(new MouseEvent('mouseup', { bubbles:true, cancelable:true })); } catch {}
          try { owner.dispatchEvent(new MouseEvent('click', { bubbles:true, cancelable:true, view:window })); } catch {}
          try { if (owner.click) owner.click(); } catch {}
          return { ok:true, logs };
        }
      }
    } catch {}
    logs.push('no element clicked');
    return { ok:false, logs };
  })();`);
}

async function detectPageChange(prevHtml: string, currentHtml: string): Promise<{ changed: boolean; reason?: string; before_hash?: string; after_hash?: string;}> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/f2`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prev_html: prevHtml, current_html: currentHtml })
    });
    if (!res.ok) return { changed: false, reason: 'f2-fail' };
    const j = await res.json();
    return { changed: !!j.changed, reason: j.reason, before_hash: j.before_hash, after_hash: j.after_hash };
  } catch {
    // fallback naive hash compare
    const h = (s: string) => crypto.subtle ? '' : String(s.length);
    return { changed: prevHtml !== currentHtml, reason: 'naive-diff' } as any;
  }
}

// Build static user task candidates (exact match first; optional fuzzy substring/token match)
async function buildStaticUserTaskCandidates(label: string, fuzzy = false): Promise<PlanItem[]> {
  const esc = (s: string) => JSON.stringify(s);
  const elements: { selector: string; text: string; }[] = await getWebviewElementScript(`(() => {
    const out = [];
    const norm = (t) => (t||'').replace(/\s+/g,' ').trim();
    const label = norm(${esc(label)});
    const labelLower = label.toLowerCase();
    const labelTokens = labelLower.split(/\s+/).filter(Boolean);
    const nodes = Array.from(document.querySelectorAll('button, a, [role="button"], [data-component-name="Button"], [data-lov-name="Button"]'));
    for (const n of nodes) {
      const txt = norm(n.textContent);
      const txtLower = txt.toLowerCase();
      const txtTokens = txtLower.split(/\s+/).filter(Boolean);
      let accept = false;
      let fuzzyType = null;
      if (txt === label) { accept = true; fuzzyType = 'exact'; }
      else if (fuzzy) {
        // substring
        if (labelLower.length > 4 && (txtLower.includes(labelLower) || labelLower.includes(txtLower))) { accept = true; fuzzyType = 'substr'; }
        else {
          // token subset (>=60% of tokens match)
            const inter = labelTokens.filter(t => txtTokens.includes(t));
            if (inter.length && (inter.length / Math.max(1,labelTokens.length)) >= 0.6) { accept = true; fuzzyType = 'tokens'; }
        }
      }
      if (accept) {
        // Prefer text: selector first
        out.push({ selector: 'text:' + txt, text: txt });
        // Additional css candidate via data-* attributes if available
        const dcn = n.getAttribute('data-component-name');
        const dcc = n.getAttribute('data-component-content');
        const classes = (n.getAttribute('class')||'').split(/\s+/).filter(Boolean);
        if (classes.length) {
          out.push({ selector: 'css:' + classes.map(c=>'.'+CSS.escape(c)).join(''), text: txt });
        } else if (dcn) {
          out.push({ selector: 'css:[data-component-name="'+dcn+'"]', text: txt });
        } else if (dcc) {
          out.push({ selector: 'css:[data-component-content*="'+dcc.slice(0,20)+'"]', text: txt });
        }
      }
    }
    // Dedup by selector
    const seen = new Set();
    return out.filter(o => { if (seen.has(o.selector)) return false; seen.add(o.selector); return true; });
  })();`);
  return elements.map(e => ({ selector: e.selector, plan: { actions: [{ kind: 'click', selector: e.selector }] } }));
}

async function buildSideMenuToggleCandidates(): Promise<PlanItem[]> {
  const escArr = JSON.stringify(SIDE_MENU_CLASS_HINTS);
  const out: { selector: string; score: number }[] = await getWebviewElementScript(`(() => {
    const hints = new Set(${escArr});
    const norm = (s) => (s||'').toLowerCase();
    const results = [];
    const nodes = Array.from(document.querySelectorAll('button, a, div, span'));
    for (const n of nodes) {
      let score = 0;
      const cls = (n.getAttribute('class')||'').toLowerCase();
      for (const h of hints) if (cls.includes(h)) score += 5;
      const aria = (n.getAttribute('aria-label')||'').toLowerCase();
      if (aria && ['menu','hamburger','navigation'].some(k=>aria.includes(k))) score += 4;
      const svg = n.querySelector('svg');
      if (svg) {
        const scls = (svg.getAttribute('class')||'').toLowerCase();
        for (const h of hints) if (scls.includes(h)) score += 3;
        // If it's a lucide-menu icon, push a robust :has selector candidate
        if (scls.includes('lucide-menu')) {
          results.push({ selector: 'css:button:has(svg.lucide-menu)', score: 100 });
        }
      }
      if (score >= 5) {
        // Build a css selector (favor first class chain)
        const classes = (n.getAttribute('class')||'').split(/\s+/).filter(Boolean).slice(0,3);
        if (classes.length) {
          results.push({ selector: 'css:' + classes.map(c=>'.'+CSS.escape(c)).join(''), score });
        } else if (aria) {
          const first = aria.split(/\s+/)[0];
          results.push({ selector: 'css:[aria-label*="'+first+'"]', score });
        }
      }
    }
    // Dedup, sort by score desc
    const seen = new Set();
    const uniq = [];
    for (const r of results.sort((a,b)=>b.score-a.score)) {
      if (seen.has(r.selector)) continue; seen.add(r.selector); uniq.push(r);
    }
    return uniq.slice(0,6);
  })();`);
  return out.map(o => ({ selector: o.selector, plan: { actions: [{ kind: 'click', selector: o.selector }], meta: { sideMenu: true, score: o.score } } }));
}

// Placeholder LLM fallback (will be replaced when backend endpoint ready)
async function llmFallbackAttempts(taskLabel: string, tried: string[], maxAttempts: number, log: (m: string)=>void): Promise<{ selector?: string; used: boolean; tried: string[]; }> {
  log(`LLM fallback placeholder invoked (max=${maxAttempts}) – no backend yet.`);
  return { used: false, tried };
}

interface RunOpts { 
  waitAfterClickMs?: number; 
  maxStaticCycles?: number; 
  maxLLMAttempts?: number; 
  log?: (msg: string)=>void; 
  useBackend?: boolean; // if true, call /api/f2 planning ops instead of pure DOM static logic
  forceLLM?: boolean;   // pass force_llm to backend
  fuzzy?: boolean;      // enable fuzzy candidate pass before opening side menu
  maxLoops?: number;    // total backend planning loops (default 6)
  maxStaticTries?: number; // max number of static clicks (including menu) (default 8)
  maxLLMTries?: number;    // max number of LLM prompt encounters (default 3)
}

async function executeClickPlan(selector: string, triedSelectors: string[], logFn: (m:string)=>void) {
  logFn(`UTASK executing plan click selector=${selector}`);
  const res = await clickInWebview(selector);
  triedSelectors.push(selector);
  for (const l of res.logs) logFn(`UTASK click: ${l}`);
  logFn(`UTASK click result=${res.ok}`);
  return res.ok;
}

async function callBackend(op: string, payload: any, logFn: (m:string)=>void): Promise<any> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/f2`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ op, ...payload }) });
    if (!res.ok) { logFn(`UTASK backend op=${op} HTTP ${res.status}`); return { ok:false, error:`http_${res.status}` }; }
    const j = await res.json();
    logFn(`UTASK backend op=${op} keys=${Object.keys(j||{}).join(',')}`);
    return j;
  } catch (e:any) {
    logFn(`UTASK backend error op=${op} ${String(e?.message||e)}`);
    return { ok:false, error:'fetch_failed' };
  }
}

export async function runGoUserTaskPageSF(taskLabel: string, opts?: RunOpts): Promise<GoUserTaskResult> {
  const logFn = opts?.log || (()=>{});
  const waitMs = Math.max(0, opts?.waitAfterClickMs ?? 800);
  const maxStaticCycles = Math.max(1, opts?.maxStaticCycles ?? 2); // (initial + after menu open)
  const triedSelectors: string[] = [];
  let sideMenuOpened = false;
  let attempts = 0;

  // Capture initial html
  const beforeCap = await getDomAndUrlFromWebview(msg => logFn(`[WV] ${msg}`));
  let prevHtml = beforeCap.html || '';
  if (!prevHtml) return { ok:false, changed:false, taskLabel, triedSelectors, staticCandidatesTried:0, attempts, logs:[], error:'no-initial-html' };

  // BACKEND-DRIVEN MODE
  const useBackend = opts?.useBackend !== undefined ? opts.useBackend : true; // default true now
  if (useBackend) {
    logFn(`UTASK backend-loop start label='${taskLabel}' forceLLM=${!!opts.forceLLM}`);
    const maxLoops = Math.max(1, opts?.maxLoops ?? 6);
    const maxStaticTries = Math.max(0, opts?.maxStaticTries ?? 8);
    const maxLLMTries = Math.max(0, opts?.maxLLMTries ?? 3);
    let lastChange = false;
    let llmSeen = false;
    let staticTries = 0;
    let llmTries = 0;
    for (let i = 0; i < maxLoops; i++) {
      if (staticTries >= maxStaticTries && llmTries >= maxLLMTries) {
        logFn(`UTASK limits exhausted (static=${staticTries}/${maxStaticTries}, llm=${llmTries}/${maxLLMTries})`);
        break;
      }
      // Recapture each loop to adapt if page changed externally
      const cap = await getDomAndUrlFromWebview(m=>logFn(`[WV] ${m}`));
      const htmlNow = cap.html || prevHtml;
      if (htmlNow !== prevHtml) {
        logFn(`UTASK loop ${i+1}/${maxLoops} detected external change`);
        prevHtml = htmlNow;
      }
      const forceLLMIter = ((!!opts.forceLLM) || (i >= 1)) && (llmTries < maxLLMTries); // enable LLM from 2nd loop, limited
      logFn(`UTASK loop ${i+1}/${maxLoops} -> goUserPage (forceLLMIter=${forceLLMIter})`);
      const plan = await callBackend('goUserPage', { html: prevHtml, taskLabel, force_llm: forceLLMIter }, logFn);
      if (plan?.planType === 'llmPrompt') {
        if (llmTries < maxLLMTries) {
          llmTries++;
          llmSeen = true;
          logFn(`UTASK LLM prompt available (llmTries=${llmTries}/${maxLLMTries})`);
        } else {
          logFn('UTASK LLM prompt ignored (llm tries exhausted)');
        }
      }
      if (plan?.planType === 'fillPlan' && plan?.selector) {
        if (staticTries >= maxStaticTries) {
          logFn(`UTASK static tries exhausted; skipping click for ${plan.selector}`);
        } else {
        attempts++;
        await executeClickPlan(plan.selector, triedSelectors, logFn);
          staticTries++;
        }
        await new Promise(r=>setTimeout(r, waitMs));
        const afterCap = await getDomAndUrlFromWebview(m=>logFn(`[WV] ${m}`));
        const det = await detectPageChange(prevHtml, afterCap.html||'');
        lastChange = !!det.changed;
        prevHtml = afterCap.html || prevHtml;
        logFn(`UTASK after goUserPage click changed=${lastChange}`);
        // Always continue to call goUserPage on every change as requested
        continue;
      }
      // No selector (or llmPrompt) -> try opening side menu every time
      logFn(`UTASK no direct selector; trying openSideMenu`);
      const openPlan = await callBackend('openSideMenu', { html: prevHtml }, logFn);
      if (openPlan?.planType === 'fillPlan' && openPlan?.mapping?.primary) {
        attempts++;
        const selector = openPlan.mapping.primary;
        let ok = false;
        if (staticTries < maxStaticTries) {
          ok = await executeClickPlan(selector, triedSelectors, logFn);
          staticTries++;
        } else {
          logFn('UTASK static tries exhausted; skipping primary menu click');
        }
        if (!ok) {
          logFn('UTASK primary menu click failed; trying local lucide-menu fallbacks');
          const altSelectors = [ 'css:button:has(svg.lucide-menu)', 'css:svg.lucide-menu' ];
          for (const s of altSelectors) {
            if (staticTries >= maxStaticTries) { logFn('UTASK static tries exhausted; stop fallbacks'); break; }
            const ok2 = await executeClickPlan(s, triedSelectors, logFn);
            staticTries++;
            if (ok2) { ok = true; break; }
          }
        }
        sideMenuOpened = true;
        await new Promise(r=>setTimeout(r, Math.max(waitMs, 600)));
        const afterMenu = await getDomAndUrlFromWebview(m=>logFn(`[WV] ${m}`));
        const detM = await detectPageChange(prevHtml, afterMenu.html||'');
        lastChange = !!detM.changed;
        prevHtml = afterMenu.html || prevHtml;
        logFn(`UTASK after menu click changed=${lastChange}`);
      } else {
        logFn('UTASK openSideMenu plan not available; skipping');
      }
    }
    return { ok:true, changed: false, taskLabel, triedSelectors, staticCandidatesTried: triedSelectors.length, sideMenuOpened, llmUsed: llmSeen, attempts, logs: [] };
  }
  // DOM-LOCAL MODE (legacy)

  // STATIC LOOP: two phases (before & after attempting to open menu)
  for (let cycle = 0; cycle < maxStaticCycles; cycle++) {
    attempts++;
    logFn(`UTASK cycle ${cycle+1}/${maxStaticCycles} (sideMenuOpened=${sideMenuOpened}) scanning static user task candidates`);
  let staticCands = await buildStaticUserTaskCandidates(taskLabel);
  if (!staticCands.length && (opts?.fuzzy ?? true)) {
      logFn('UTASK no exact candidates; trying fuzzy mode');
      staticCands = await buildStaticUserTaskCandidates(taskLabel, true);
    }
    if (staticCands.length) {
      logFn(`UTASK found ${staticCands.length} static candidates for '${taskLabel}'`);
      for (let i = 0; i < staticCands.length; i++) {
        const c = staticCands[i];
        logFn(`UTASK try static [${i+1}/${staticCands.length}] selector=${c.selector}`);
        for (const act of c.plan.actions) {
          if (act.kind.toLowerCase() === 'click' && act.selector) {
            const ok = await clickInWebview(act.selector);
            triedSelectors.push(act.selector);
            logFn(`UTASK click -> ${ok?'ok':'fail'}`);
          }
        }
        await new Promise(r => setTimeout(r, waitMs));
        const afterCap = await getDomAndUrlFromWebview(msg => logFn(`[WV] ${msg}`));
        const afterHtml = afterCap.html || '';
        const det = await detectPageChange(prevHtml, afterHtml);
        logFn(`UTASK detect changed=${det.changed} reason=${det.reason || ''}`);
        if (det.changed) {
          return {
            ok:true, changed:true, reason:det.reason, taskLabel,
            triedSelectors, staticCandidatesTried: staticCands.length,
            sideMenuOpened, llmUsed:false, finalSelector: c.selector,
            attempts, logs: []
          };
        }
        prevHtml = afterHtml; // update baseline even if no change
      }
      logFn(`UTASK all static candidates exhausted without change`);
    } else {
      logFn(`UTASK no static candidates found in cycle ${cycle+1}`);
    }
    // If not last cycle, attempt opening side menu
    if (cycle < maxStaticCycles - 1) {
      logFn(`UTASK attempt to open side menu (no success yet)`);
      const toggles = await buildSideMenuToggleCandidates();
      if (!toggles.length) {
        logFn('UTASK no side menu toggle candidates');
        continue;
      }
      for (let ti = 0; ti < toggles.length; ti++) {
        const t = toggles[ti];
        logFn(`UTASK toggle try [${ti+1}/${toggles.length}] selector=${t.selector}`);
        for (const act of t.plan.actions) {
          if (act.kind.toLowerCase() === 'click' && act.selector) {
            const res = await clickInWebview(act.selector);
            triedSelectors.push(act.selector);
            for (const l of res.logs) logFn(`UTASK toggle: ${l}`);
            logFn(`UTASK toggle click -> ${res.ok?'ok':'fail'}`);
          }
        }
        await new Promise(r => setTimeout(r, Math.max(400, waitMs)));
        const afterToggle = await getDomAndUrlFromWebview(msg => logFn(`[WV] ${msg}`));
        const htmlT = afterToggle.html || '';
        // Heuristic: if new candidate appears now we mark side menu as opened.
        const candsNow = await buildStaticUserTaskCandidates(taskLabel);
        if (candsNow.length) {
          sideMenuOpened = true;
          logFn(`UTASK side menu likely opened (found ${candsNow.length} candidates after toggle)`);
          prevHtml = htmlT;
          break; // proceed next cycle for static tries
        }
        prevHtml = htmlT;
      }
    }
  }

  // LLM fallback (placeholder) – attempt cycles
  const maxLLM = Math.max(1, opts?.maxLLMAttempts ?? 2);
  const llmRes = await llmFallbackAttempts(taskLabel, triedSelectors, maxLLM, logFn);
  if (llmRes.selector) {
    return { ok:true, changed:false, taskLabel, triedSelectors: llmRes.tried, staticCandidatesTried: triedSelectors.length, sideMenuOpened, llmUsed:true, finalSelector: llmRes.selector, attempts, logs: [] };
  }

  return { ok:true, changed:false, taskLabel, triedSelectors, staticCandidatesTried: triedSelectors.length, sideMenuOpened, llmUsed: llmRes.used, attempts, logs: [] };
}
