import { getDomAndUrlFromWebview, checkSelectorHasValue } from "../services/webviewDom";
import { BACKEND_URL } from "../config";
import { runActions } from "../services/ts3ActionRunner";
import { runInPageFill } from "../services/ts3InPageFiller";

export type F3Options = {
  waitAfterActionMs?: number;
  maxLoops?: number;
  maxLLMTries?: number;
  log?: (m: string) => void;
};

async function postF3(op: string, body: any, log?: (m: string)=>void) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/f3`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ op, ...(body||{}) }),
    });
    if (!res.ok) return { ok:false, error: `http_${res.status}` };
    const j = await res.json();
    log?.(`F3 backend op=${op} keys=${Object.keys(j||{}).join(',')}`);
    return j;
  } catch (e: any) {
    log?.(`F3 backend error op=${op} ${String(e?.message||e)}`);
    return { ok:false, error:'fetch_failed' };
  }
}

export async function runFillFormsUserTaskPageSF(opts?: F3Options) {
  const log = opts?.log || (()=>{});
  // Load config from backend to allow dynamic tuning
  let cfg: any = undefined;
  try {
    const res = await fetch(`${BACKEND_URL}/api/config`);
    if (res.ok) cfg = await res.json();
  } catch {}
  const f3cfg = cfg?.goFillForms?.stateflow || {};
  const waitMs = Math.max(0, opts?.waitAfterActionMs ?? (typeof f3cfg.waitAfterActionMs === 'number' ? f3cfg.waitAfterActionMs : 600));
  const maxLoops = Math.max(1, opts?.maxLoops ?? (typeof f3cfg.maxLoops === 'number' ? f3cfg.maxLoops : 10));
  const perFieldAttemptWaits: number[] = Array.isArray(f3cfg.perFieldAttemptWaits) && f3cfg.perFieldAttemptWaits.length
    ? f3cfg.perFieldAttemptWaits.map((n: any) => Math.max(0, Number(n)||0))
    : [250, 400, 600];
  const postFillVerifyDelayMs: number = typeof f3cfg.postFillVerifyDelayMs === 'number' ? f3cfg.postFillVerifyDelayMs : 200;
  const htmlCheckDelayMs: number = typeof f3cfg.htmlCheckDelayMs === 'number' ? f3cfg.htmlCheckDelayMs : 200;
  const commitEnterCfg = (f3cfg.commitEnter !== undefined) ? !!f3cfg.commitEnter : true;
  const clickOutsideCfg = (f3cfg.clickOutside !== undefined) ? !!f3cfg.clickOutside : true;

  // Step 0: get ruhsat json from backend component
  const input = await postF3('loadRuhsatFromTmp', {}, log);
  if (!input?.ok) {
    log(`F3 loadRuhsatFromTmp failed: ${JSON.stringify(input)}`);
    return { ok:false, step:'loadRuhsat', error: input?.error || 'no_input' };
  }
  log(`F3 loadRuhsatFromTmp meta: ${JSON.stringify(input.meta || {})}`);
  if (input.prep) {
    log(`F3 staging prep: ${JSON.stringify(input.prep)}`);
  }
  const ruhsat = input.data;

  let prevHtml = (await getDomAndUrlFromWebview((m)=>log(`[WV] ${m}`))).html || '';
  if (!prevHtml) return { ok:false, error:'no-initial-html' };
  // Cache last analyze results to avoid re-calling LLM for same HTML
  let lastAnaHtml: string | undefined;
  let lastAna: any | undefined;

  for (let i=0; i<maxLoops; i++) {
    // Check final page statically first
    const fin = await postF3('detectFinalPage', { html: prevHtml }, log);
    if (fin?.ok && fin.is_final) {
      // Try to click final CTA by text
      const hits: string[] = fin.hits || [];
      for (const t of hits) {
        await runActions([`click#${t}`], true, (c,m)=>log(`${c} ${m}`));
        await new Promise(r=>setTimeout(r, waitMs));
        const cur = (await getDomAndUrlFromWebview((m)=>log(`[WV] ${m}`))).html || prevHtml;
        if (cur !== prevHtml) return { ok:true, changed:true, final:true, finalSelector:`text:${t}` };
      }
    }

    // Analyze page once per HTML; reuse mapping if HTML unchanged
    let ana: any;
    if (lastAnaHtml === prevHtml && lastAna) {
      ana = lastAna;
      log(`SF-F3 analyze: reused cached mapping for current HTML`);
    } else {
      ana = await postF3('analyzePage', { html: prevHtml, ruhsat_json: ruhsat }, log);
      lastAnaHtml = prevHtml;
      lastAna = ana;
    }
    if (!ana?.ok) return { ok:false, step:'analyze', error: ana?.error || 'llm-failed' };
    if (ana.page_kind === 'final_activation') {
      const acts: string[] = ana.actions || [];
      for (const t of acts) {
        await runActions([`click#${t}`], true, (c,m)=>log(`${c} ${m}`));
        await new Promise(r=>setTimeout(r, waitMs));
        const cur = (await getDomAndUrlFromWebview((m)=>log(`[WV] ${m}`))).html || prevHtml;
        if (cur !== prevHtml) return { ok:true, changed:true, final:true, finalSelector:`text:${t}` };
      }
      // if none worked, fallthrough to next loop (page may need other steps)
    } else {
      const fieldMapping: Record<string,string> = ana.field_mapping || {};
      if (fieldMapping && Object.keys(fieldMapping).length) {
        const expectedKeys = Object.keys(fieldMapping).filter(k => ruhsat && typeof ruhsat[k] !== 'undefined' && String(ruhsat[k]??'').trim() !== '');
        const dynamicThreshold = Math.min(2, Math.max(1, expectedKeys.length >= 2 ? 2 : 1));
        // Fill fields sequentially with waits and selector-level verification; prioritize critical fields
        const critical = ['sasi_no','motor_no','tescil_tarihi'];
        const order = Array.from(new Set([...critical, 'plaka_no', 'model_yili', ...expectedKeys]))
          .filter(k => !!fieldMapping[k] && String(ruhsat[k] ?? '').trim() !== '');
        log(`SF-F3 Form1: sequential fill order -> ${order.join(', ')}`);

        const selectorStatus: Record<string, boolean> = {};
        for (const k of order) {
          const sel = fieldMapping[k];
          log(`SF-F3 step: fill ${k} -> ${sel}`);
          let okOne = false;
          const attempts = perFieldAttemptWaits.length > 0 ? perFieldAttemptWaits : [300, 500, 700];
          for (let attempt = 1; attempt <= attempts.length; attempt++) {
            const waitAfter = attempts[attempt-1];
            await runInPageFill({ [k]: sel }, ruhsat, { highlight: true, simulateTyping: true, stepDelayMs: 0, commitEnter: commitEnterCfg, clickOutside: clickOutsideCfg, waitAfterFillMs: waitAfter }, (c,m)=>log(`${c} ${m}`));
            await new Promise(r=>setTimeout(r, Math.max(0, waitAfter - 100)));
            okOne = await checkSelectorHasValue(sel, (c,m)=>log(`${c} ${m}`));
            log(`SF-F3 step: verify ${k} attempt ${attempt} -> ${okOne ? 'YES' : 'NO'}`);
            if (okOne) break;
          }
          selectorStatus[k] = !!okOne;
          if (!okOne) { log(`SF-F3 step: give up ${k} after 3 attempts`); }
        }

        // Global verification via HTML-only filled check + critical gates
        await new Promise(r=>setTimeout(r, htmlCheckDelayMs));
        let curHtml = (await getDomAndUrlFromWebview((m)=>log(`[WV] ${m}`))).html || prevHtml;
        const filledCheck = await postF3('detectFormsFilled', { html: curHtml, mapping: { min_filled: dynamicThreshold } }, log);
        log(`SF-F3 Form1: filled-check (html-only) -> ${JSON.stringify(filledCheck)}`);

        const criticalPresent = critical.some(k => !!fieldMapping[k]);
        const criticalOk = critical.filter(k => !!fieldMapping[k]).every(k => !!selectorStatus[k]);
        const committedCount = Object.values(selectorStatus).filter(Boolean).length;
        const committedEnough = committedCount >= dynamicThreshold;

        if ((!filledCheck?.ok) || (criticalPresent && !criticalOk) || !committedEnough) {
          log(`SF-F3 skip actions: gates not satisfied (htmlOk=${!!filledCheck?.ok}, criticalOk=${criticalOk}, committed=${committedCount}/${dynamicThreshold})`);
        } else {
          const acts: string[] = Array.isArray(ana.actions) ? ana.actions : [];
          if (acts.length) {
            const clickActs = acts.map(t => `click#${t}`);
            await runActions(clickActs, true, (c,m)=>log(`${c} ${m}`));
          }
        }
      }
      await new Promise(r=>setTimeout(r, waitMs));
    }

    prevHtml = (await getDomAndUrlFromWebview((m)=>log(`[WV] ${m}`))).html || prevHtml;
  }

  return { ok:true, step:'completed' };
}
