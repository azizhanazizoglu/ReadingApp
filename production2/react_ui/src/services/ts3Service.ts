import { getWebview } from './webviewDom';
import { getTs3Plan } from './ts3PlanClient';
import { runBackendScript } from './ts3ScriptClient';
import { resolveValues as resolveValuesClient } from './ts3Resolver';
import { runInPageFill } from './ts3InPageFiller';
import { runActions } from './ts3ActionRunner';

type Ts3Options = {
  highlight?: boolean;
  stepDelayMs?: number;
  simulateTyping?: boolean;
  // When TS1 provides no usable values, optionally fill with dummy data for debugging
  useDummyWhenEmpty?: boolean;
  // Prefer backend-built injection script (webbot_filler) for testability
  useBackendScript?: boolean;
};

export async function runTs3(backEndUrl: string, devLog?: (c: string, m: string) => void, opts?: Ts3Options) {
  devLog?.('IDX-TS3-START', 'TS3 başlatıldı: mapping ile form doldurma (LLM yok)');
  const mr = await fetch(`${backEndUrl}/api/mapping`);
  const mj = await mr.json();
  const mapping = mj.mapping || null;
  if (!mapping || !mapping.field_mapping) throw new Error('Mapping bellekten bulunamadı. Önce Ts2 çalıştırın.');
  const fieldMapping = mapping.field_mapping || {};
  const actions: string[] = Array.isArray(mapping.actions) ? mapping.actions : [];

  const sr = await fetch(`${backEndUrl}/api/state`);
  const stateJson = await sr.json();
  const ruhsat_json = stateJson.ruhsat_json || null;
  if (!ruhsat_json) throw new Error('TS1 JSON bulunamadı. Önce Ts1 çalıştırın veya /api/start-automation kullanın.');

  const webview = getWebview();
  if (!webview) throw new Error('Webview bulunamadı. Electron tarayıcı açık olmalı.');

  const highlight = opts?.highlight !== false; // default: true
  const stepDelayMs = Math.max(0, Number(opts?.stepDelayMs || 0));
  const simulateTyping = opts?.simulateTyping !== false; // default: true
  const useDummyWhenEmpty = opts?.useDummyWhenEmpty === true; // default off; we'll auto-enable if everything empty
  const useBackendScript = opts?.useBackendScript !== false; // default: true to use backend webbot_filler

  // Log mapping keys for visibility
  devLog?.('IDX-TS3-MAP-KEYS', JSON.stringify(Object.keys(fieldMapping)));
  // Extra: log mapping selectors for each key (helps see exactly what TS3 will query)
  try {
    Object.entries(fieldMapping).forEach(([k, sel]) => {
      devLog?.('IDX-TS3-MAP-SELECTOR', `${k} -> ${sel}`);
    });
  } catch {}

  // Compose raw text for potential extraction
  const getRaw = () => {
    const r1 = typeof ruhsat_json.rawresponse === 'string' ? ruhsat_json.rawresponse : '';
    const r2 = typeof (stateJson.rawresponse) === 'string' ? stateJson.rawresponse : '';
    return r1 || r2 || '';
  };
  const raw = getRaw();
  if (raw) {
    const sample = raw.length > 200 ? raw.slice(0, 200) + '…' : raw;
    devLog?.('IDX-TS3-RAW-SUMMARY', sample);
  }
  // Resolve on client for immediate logs and to merge with backend plan later
  const dataResolved: Record<string, any> = resolveValuesClient(mapping, ruhsat_json, raw, devLog);

  // Optionally ask backend to build a plan and resolved values for diagnostics (unit-testable logic in webbot_filler)
  try {
    const plan = await getTs3Plan(backEndUrl, mapping, ruhsat_json, raw, useDummyWhenEmpty, devLog);
    if (plan?.resolved && typeof plan.resolved === 'object') {
      Object.assign(dataResolved, plan.resolved);
    }
  } catch (e) { devLog?.('IDX-TS3-PLAN-ERR', String(e)); }

  // If configured, request a backend-generated injection script and execute it
  if (useBackendScript) {
    await runBackendScript(backEndUrl, mapping, ruhsat_json, raw, { highlight, simulateTyping, stepDelayMs, useDummyWhenEmpty }, devLog);
  } else {
    await runInPageFill(fieldMapping, dataResolved, { highlight, simulateTyping, stepDelayMs }, devLog);
  }

  // Optional: mapping may include sample values (value_defaults or sample_values)
  const sampleValues: Record<string, any> = {
    ...(mapping?.sample_values || {}),
    ...(mapping?.value_defaults || {}),
    ...(mapping?.values || {}),
    ...(mapping?.value_mapping || {}),
    ...(mapping?.static_values || {}),
    ...(mapping?.write_values || {}),
  };
  let sampleApplied = false;
  for (const k of Object.keys(fieldMapping || {})) {
    const v = dataResolved[k];
    if ((v == null || String(v).trim() === '') && sampleValues && sampleValues[k] != null) {
      dataResolved[k] = sampleValues[k];
      sampleApplied = true;
      devLog?.('IDX-TS3-SAMPLE', `${k} <- mapping.sample (${String(sampleValues[k]).slice(0,60)}` + (String(sampleValues[k]).length>60?'…':'') + ')');
    }
  }

  // If all values are empty and user allows or we detect no TS1 data at all, prepare dummy values for debugging
  const allEmpty = Object.keys(fieldMapping || {}).every(k => {
    const v = dataResolved[k];
    return v == null || String(v).trim() === '';
  });
  if (allEmpty && useDummyWhenEmpty) {
    const dummy = {
      plaka_no: '34 ABC 123',
      tckimlik: '10000000000',
      dogum_tarihi: '1990-01-01',
      ad_soyad: 'Ali Veli',
    } as Record<string, string>;
    let applied = false;
    for (const k of Object.keys(fieldMapping || {})) {
      if (!dataResolved[k] || String(dataResolved[k]).trim() === '') {
        const val = dummy[k] ?? 'TEST';
        dataResolved[k] = val;
        applied = true;
        devLog?.('IDX-TS3-DUMMY', `${k} <- ${val}`);
      }
    }
    if (applied) {
      devLog?.('IDX-TS3-NOTE', 'TS1 verisi bulunamadı; dummy değerlerle doldurma modu etkin.');
    }
  }

  const fillScript = `(() => {
    try {
      const mapping = ${JSON.stringify(fieldMapping)};
      const data = ${JSON.stringify(dataResolved)};
      const logs = [];
      const highlight = ${JSON.stringify(highlight)};
      const stepDelayMs = ${JSON.stringify(stepDelayMs)};
      const simulateTyping = ${JSON.stringify(simulateTyping)};
      const delay = (ms) => new Promise(r => setTimeout(r, ms));
      const norm = (s) => {
        if (s == null) return '';
        const t = String(s).toLowerCase()
          .replace(/ç/g, 'c').replace(/ğ/g, 'g').replace(/ı/g, 'i').replace(/ö/g, 'o').replace(/ş/g, 's').replace(/ü/g, 'u')
          .replace(/Ç/g, 'c').replace(/Ğ/g, 'g').replace(/İ/g, 'i').replace(/Ö/g, 'o').replace(/Ş/g, 's').replace(/Ü/g, 'u')
          .replace(/[^\p{L}\p{N}]+/gu, ' ');
        try { return t.normalize('NFD').replace(/[\u0300-\u036f]/g, ' '); } catch { return t; }
      };
      const textForEl = (el) => {
        if (!el) return '';
        const id = el.id || '';
        let lab = '';
        try { const l = id ? document.querySelector('label[for="'+id+'"]') : null; lab = l ? (l.textContent||'') : ''; } catch {}
        const ph = el.getAttribute && (el.getAttribute('placeholder')||'');
        const ar = el.getAttribute && (el.getAttribute('aria-label')||'');
        const nm = el.getAttribute && (el.getAttribute('name')||'');
        const title = el.getAttribute && (el.getAttribute('title')||'');
        let up = '';
        try { let p = el; let i=0; while (p && i<3) { p = p.parentElement; if (p && p.textContent) { up = p.textContent + ' ' + up; } i++; } } catch {}
        return [lab, ph, ar, nm, title, up].map(norm).join(' ');
      };
      const synonyms = {
        'plaka_no': ['plaka', 'plaka no', 'plate', 'plate no', 'arac plaka', 'vehicle plate'],
        'ad_soyad': ['ad soyad', 'ad/soyad', 'isim', 'name', 'full name'],
        'tckimlik': ['tc', 'tc kimlik', 'kimlik', 'identity', 'national id'],
        'dogum_tarihi': ['dogum tarihi', 'doğum tarihi', 'birth date', 'birthdate', 'dob']
      };
      const findByKey = (key) => {
        const syns = synonyms[key] || [key];
        const targets = Array.from(document.querySelectorAll('input, textarea, select, [contenteditable="true"]'));
        const scored = targets.map(el => {
          const t = textForEl(el);
          const score = syns.reduce((acc, s) => acc + (t.includes(norm(s)) ? 1 : 0), 0) + (t.includes(norm(key)) ? 1 : 0);
          return { el, score };
        }).filter(x => x.score > 0).sort((a,b) => b.score - a.score);
        if (scored.length) {
          const top = scored.slice(0,3).map(x => {
            const el = x.el; const tag = (el.tagName||'').toLowerCase(); const id = el.id||''; const name = el.name||'';
            const txt = textForEl(el).slice(0,120);
            return '[' + tag + (id?('#'+id):'') + (name?(' name='+name):'') + ' score=' + x.score + '] "' + txt + '"';
          });
          logs.push('fallback-candidates '+key+' -> '+top.join(' | '));
          return scored[0].el;
        }
        return null;
      };
      const setNativeValue = (el, value) => {
        try {
          const proto = el.tagName === 'INPUT' ? window.HTMLInputElement.prototype : (el.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : null);
          if (proto) {
            const desc = Object.getOwnPropertyDescriptor(proto, 'value');
            if (desc && desc.set) { desc.set.call(el, value); return true; }
          }
        } catch {}
        try { el.value = value; return true; } catch { return false; }
      };
      const setNativeChecked = (el, checked) => {
        try {
          const proto = window.HTMLInputElement.prototype;
          const desc = Object.getOwnPropertyDescriptor(proto, 'checked');
          if (desc && desc.set) { desc.set.call(el, !!checked); return true; }
        } catch {}
        try { el.checked = !!checked; return true; } catch { return false; }
      };
      const getInfo = (el) => {
        if (!el) return { tag: 'none' };
        const tag = (el.tagName||'').toLowerCase();
        const type = (el.type||'').toLowerCase();
        let value = undefined;
        if (tag === 'input') {
          if (type === 'checkbox') value = !!el.checked;
          else if (type === 'radio') value = el.checked ? (el.value||'') : '';
          else value = el.value;
        } else if (tag === 'select') {
          const idx = el.selectedIndex;
          const opt = idx >= 0 ? el.options[idx] : null;
          value = { value: el.value, text: (opt && opt.textContent ? String(opt.textContent).trim() : '') };
        } else if (tag === 'textarea') {
          value = el.value;
        }
        const root = el.getRootNode && el.getRootNode();
        const rootKind = root && root.toString ? String(root.toString()) : '';
  const id = el.id||''; const name = el.name||'';
  return { tag, type, id, name, value, root: rootKind };
      };
      const normDate = (s) => {
        if (!s) return s;
        const t = String(s).trim();
        // dd.mm.yyyy or dd/mm/yyyy -> yyyy-MM-dd
        const m = t.match(/^([0-3]?\d)[./-]([0-1]?\d)[./-](\d{4})$/);
        if (m) {
          const dd = m[1].padStart(2, '0');
          const mm = m[2].padStart(2, '0');
          const yyyy = m[3];
          return yyyy + '-' + mm + '-' + dd;
        }
        // already yyyy-MM-dd
        if (/^\d{4}-\d{2}-\d{2}$/.test(t)) return t;
        return t;
      };
      const typeInto = async (el, text) => {
        const s = String(text == null ? '' : text);
        // clear first
        setNativeValue(el, '');
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        let acc = '';
        for (const ch of s) {
          acc += ch;
          // try key events for masks
          try {
            el.dispatchEvent(new KeyboardEvent('keydown', { key: ch, bubbles: true }));
          } catch {}
          setNativeValue(el, acc);
          el.dispatchEvent(new Event('input', { bubbles: true }));
          try {
            el.dispatchEvent(new KeyboardEvent('keyup', { key: ch, bubbles: true }));
          } catch {}
          await delay(5);
        }
        el.dispatchEvent(new Event('change', { bubbles: true }));
      };
      const setVal = (el, val) => {
        if (!el) return false;
        const tag = (el.tagName || '').toLowerCase();
        if (tag === 'input') {
          const type = (el.type || 'text').toLowerCase();
          el.focus();
          if (type === 'checkbox') {
            const want = !!val;
            setNativeChecked(el, want);
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            if (el.checked !== want) { try { el.click(); } catch {} }
            el.blur();
            return true;
          }
          if (type === 'radio') {
            const radios = document.querySelectorAll('input[type="radio"][name="' + el.name + '"]');
            const desired = String(val == null ? '' : val).trim().toLowerCase();
            let done = false;
            radios.forEach(r => {
              if (done) return;
              const rv = String(r.value||'').trim().toLowerCase();
              if (rv === desired) { try { r.click(); done = true; } catch {} }
            });
            el.blur();
            return done;
          }
          if (type === 'date') {
            const desired = normDate(val);
            setNativeValue(el, String(desired));
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            el.blur();
            return true;
          }
          // text-like
          if (simulateTyping) {
            return typeInto(el, val).then(() => { try { el.blur(); } catch {}; return true; });
          } else {
            setNativeValue(el, String(val == null ? '' : val));
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            el.blur();
            return true;
          }
        }
        if (tag === 'textarea') {
          el.focus();
          if (simulateTyping) {
            return typeInto(el, val).then(() => { try { el.blur(); } catch {}; return true; });
          } else {
            setNativeValue(el, String(val == null ? '' : val));
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            el.blur();
            return true;
          }
        }
        if (tag === 'select') {
          const desired = String(val == null ? '' : val).trim();
          el.value = desired;
          if (el.value !== desired) {
            const opts = Array.from(el.options || []);
            let found = opts.find(o => String(o.textContent||'').trim().toLowerCase() === desired.toLowerCase());
            if (!found) found = opts.find(o => String(o.textContent||'').toLowerCase().includes(desired.toLowerCase()));
            if (!found) found = opts.find(o => String(o.value||'').trim().toLowerCase() === desired.toLowerCase());
            if (found) el.value = found.value;
          }
          el.dispatchEvent(new Event('change', { bubbles: true }));
          return true;
        }
        return false;
      };
      let filled = 0;
  const entries = Object.entries(mapping);
      const details = [];
  try { logs.push('page-info url=' + (location && location.href ? location.href : '') + ' ready=' + (document && document.readyState ? document.readyState : '')); } catch {}
  try { const cnt = document.querySelectorAll('input, textarea, select, [contenteditable="true"]').length; logs.push('targets-count ' + cnt); } catch {}
      const run = async () => {
    for (const [k, selector] of entries) {
          try {
            const has = data && Object.prototype.hasOwnProperty.call(data, k);
            const val = has ? data[k] : '';
      if (val == null || String(val).trim() === '') { logs.push('skip-empty ' + k + ' (value empty)'); continue; }
            let el = null;
            try {
              const sel = String(selector);
              const els = document.querySelectorAll(sel);
              logs.push('selector-check '+k+' -> '+sel+' (count='+els.length+')');
              if (els && els.length > 0) { el = els[0]; }
            } catch (e) { logs.push('selector-error '+k+' -> '+String(e)); }
            if (!el) { el = findByKey(k); if (el) logs.push('fallback-selector '+k+' -> '+(el.id?('#'+el.id): (el.name?('name='+el.name): el.tagName))); }
      if (!el) { logs.push('not-found ' + k + ' -> ' + selector); continue; }
            if (el && highlight) {
              try { el.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' }); } catch {}
            }
            const before = getInfo(el);
            const result = await setVal(el, val);
            const after = getInfo(el);
            if (result) {
              filled++;
              logs.push('filled ' + k + ' -> ' + selector + ' (chosen='+after.tag+(after.id?('#'+after.id):'')+(after.name?(' name='+after.name):'')+')');
              details.push({ field: k, selector, before, desired: val, after });
              if (el && highlight) {
                try {
                  el.setAttribute('data-ts3-filled', '1');
                  el.title = 'TS3: ' + k + ' = ' + String(val ?? '');
                  const prevOutline = el.style.outline;
                  const prevBg = el.style.backgroundColor;
                  el.style.outline = '2px solid #22c55e';
                  el.style.backgroundColor = 'rgba(34,197,94,0.12)';
                  setTimeout(() => { try { el.style.outline = prevOutline; el.style.backgroundColor = prevBg; } catch {} }, Math.max(1200, stepDelayMs));
                } catch {}
              }
            } else {
              logs.push('skip ' + k + ' (not found or unsupported) -> ' + selector);
              details.push({ field: k, selector, before, desired: val, after, error: 'not-found-or-unsupported' });
            }
            if (stepDelayMs > 0) { await delay(stepDelayMs); }
          } catch (e) { logs.push('err '+String(e)); }
        }
      };
      return run().then(() => ({ ok: true, filled, logs, details }));
    } catch (e) { return { ok: false, error: String(e) }; }
  })();`;
  const actionRes = await runActions(actions, highlight, devLog);
  return { actionRes };
}
