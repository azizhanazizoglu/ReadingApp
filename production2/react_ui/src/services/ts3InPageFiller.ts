import { getWebview } from './webviewDom';

export type FillOptions = {
  highlight: boolean;
  stepDelayMs: number;
  simulateTyping: boolean;
  // Press Enter after filling inputs to commit values on masked/controlled fields.
  // Defaults to true if undefined.
  commitEnter?: boolean;
  // After each field, click outside (document body) to force blur/change in some UIs
  clickOutside?: boolean;
  // Wait after each field to let the framework update DOM (ms)
  waitAfterFillMs?: number;
};

export async function runInPageFill(fieldMapping: Record<string, string>, dataResolved: Record<string, any>, opts: FillOptions, devLog?: (c: string, m: string) => void) {
  const webview = getWebview();
  if (!webview) throw new Error('Webview bulunamadı.');
  const fillScript = `(() => {
    'use strict';
    try {
      const pickDoc = () => {
        try {
          const frames = Array.from(document.querySelectorAll('iframe'));
          let bestDoc = null; let bestScore = -1;
          for (const f of frames) {
            try {
              // remove TS casts: use plain contentDocument/contentWindow
              const doc = (f && f.contentDocument) ? f.contentDocument : ((f && f.contentWindow && f.contentWindow.document) ? f.contentWindow.document : null);
              if (!doc) continue;
              const cnt = doc.querySelectorAll('input, textarea, select, [contenteditable="true"]').length;
              if (cnt > bestScore) { bestScore = cnt; bestDoc = doc; }
            } catch (e) {}
          }
          return bestDoc || document;
        } catch (e) { return document; }
      };
  const DOC = pickDoc();
  // remove TS casts for defaultView resolution
  const WIN = (DOC && DOC.defaultView) ? DOC.defaultView : window;
      const SRC = (DOC === document ? 'main' : 'iframe');
      
      const mapping = ${JSON.stringify(fieldMapping)};
      const data = ${JSON.stringify(dataResolved)};
  const logs = [];
      logs.push('doc-source ' + SRC);
      const highlight = ${JSON.stringify(opts.highlight)};
      const stepDelayMs = ${JSON.stringify(opts.stepDelayMs)};
      const simulateTyping = ${JSON.stringify(opts.simulateTyping)};
  const commitEnter = ${JSON.stringify((opts as any).commitEnter ?? true)};
  const delay = (ms) => new Promise(r => setTimeout(r, ms));
  const clickOutside = ${JSON.stringify((opts as any).clickOutside ?? true)};
  const waitAfterFillMs = ${JSON.stringify((opts as any).waitAfterFillMs ?? 150)};
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
  try { const l = id ? DOC.querySelector('label[for="'+id+'"]') : null; lab = l ? (l.textContent||'') : ''; } catch {}
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
  const targets = Array.from(DOC.querySelectorAll('input, textarea, select, [contenteditable="true"]'));
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
          const proto = el.tagName === 'INPUT' ? WIN.HTMLInputElement.prototype : (el.tagName === 'TEXTAREA' ? WIN.HTMLTextAreaElement.prototype : null);
          if (proto) {
            const desc = Object.getOwnPropertyDescriptor(proto, 'value');
            if (desc && desc.set) { desc.set.call(el, value); return true; }
          }
        } catch {}
        try { el.value = value; return true; } catch { return false; }
      };
      const setNativeChecked = (el, checked) => {
        try {
          const proto = WIN.HTMLInputElement.prototype;
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
        const m = t.match(/^([0-3]?\d)[./-]([0-1]?\d)[./-](\d{4})$/);
        if (m) return m[3] + '-' + m[2].padStart(2,'0') + '-' + m[1].padStart(2,'0');
        if (/^\d{4}-\d{2}-\d{2}$/.test(t)) return t;
        return t;
      };
      const typeInto = async (el, text) => {
        const s = String(text == null ? '' : text);
        setNativeValue(el, '');
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        let acc = '';
        for (const ch of s) {
          acc += ch;
          try { el.dispatchEvent(new KeyboardEvent('keydown', { key: ch, bubbles: true })); } catch {}
          setNativeValue(el, acc);
          el.dispatchEvent(new Event('input', { bubbles: true }));
          try { el.dispatchEvent(new KeyboardEvent('keyup', { key: ch, bubbles: true })); } catch {}
          await delay(5);
        }
        el.dispatchEvent(new Event('change', { bubbles: true }));
        if (commitEnter) {
          try {
            logs.push('commit-enter typing');
            el.dispatchEvent(new WIN.KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
            el.dispatchEvent(new WIN.KeyboardEvent('keypress', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
            el.dispatchEvent(new WIN.KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
          } catch {}
        }
      };
      const pressEnter = (el) => {
        try {
          logs.push('commit-enter direct');
          el.dispatchEvent(new WIN.KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
          el.dispatchEvent(new WIN.KeyboardEvent('keypress', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
          el.dispatchEvent(new WIN.KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
        } catch {}
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
            const radios = DOC.querySelectorAll('input[type="radio"][name="' + el.name + '"]');
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
            if (commitEnter) { pressEnter(el); }
            el.blur();
            return true;
          }
          if (simulateTyping) { return typeInto(el, val).then(() => { try { if (commitEnter) pressEnter(el); } catch {}; if (clickOutside) { try { (DOC.body||el).click(); el.dispatchEvent(new Event('change', { bubbles: true })); } catch {} } try { el.blur(); el.dispatchEvent(new Event('focusout', { bubbles: true })); } catch {}; return true; }); }
          setNativeValue(el, String(val == null ? '' : val));
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
          if (commitEnter) { pressEnter(el); }
          if (clickOutside) { try { (DOC.body||el).click(); el.dispatchEvent(new Event('change', { bubbles: true })); } catch {} }
          try { el.blur(); el.dispatchEvent(new Event('focusout', { bubbles: true })); } catch {}
          return true;
        }
        if (tag === 'textarea') {
          el.focus();
          if (simulateTyping) { return typeInto(el, val).then(() => { try { if (commitEnter) pressEnter(el); } catch {}; if (clickOutside) { try { (DOC.body||el).click(); el.dispatchEvent(new Event('change', { bubbles: true })); } catch {} } try { el.blur(); el.dispatchEvent(new Event('focusout', { bubbles: true })); } catch {}; return true; }); }
          setNativeValue(el, String(val == null ? '' : val));
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
          if (commitEnter) { pressEnter(el); }
          if (clickOutside) { try { (DOC.body||el).click(); el.dispatchEvent(new Event('change', { bubbles: true })); } catch {} }
          try { el.blur(); el.dispatchEvent(new Event('focusout', { bubbles: true })); } catch {}
          return true;
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
      try {
        let u = '';
        try { u = (DOC && (DOC.URL !== undefined) ? DOC.URL : (location && location.href ? location.href : '')); } catch(e) {}
        let rs = '';
        try { rs = (DOC && (DOC.readyState !== undefined) ? DOC.readyState : ''); } catch(e) {}
        logs.push('page-info url=' + u + ' ready=' + rs);
      } catch {}
  try { const cnt = DOC.querySelectorAll('input, textarea, select, [contenteditable="true"]').length; logs.push('targets-count ' + cnt); } catch {}
      const run = async () => {
  for (const [k, selector] of entries) {
          try {
            const has = data && Object.prototype.hasOwnProperty.call(data, k);
            const val = has ? data[k] : '';
            if (val == null || String(val).trim() === '') { logs.push('skip-empty ' + k + ' (value empty)'); continue; }
            let el = null;
            try {
              const sel = String(selector);
      const els = Array.from(DOC.querySelectorAll(sel));
              logs.push('selector-check '+k+' -> '+sel+' (count='+els.length+')');
              if (els && els.length > 0) {
                if (els.length === 1) {
                  el = els[0];
                } else {
                  // choose best by scoring label/placeholder/name/title text against key synonyms
                  const syns = (synonyms[k] || [k]).map(norm);
                  let best = null;
                  let bestScore = -1;
                  for (const cand of els) {
                    const t = textForEl(cand);
                    const score = syns.reduce((acc, s) => acc + (t.includes(s) ? 1 : 0), 0);
                    if (score > bestScore) { bestScore = score; best = cand; }
                  }
                  el = best || els[0];
                  logs.push('multi-match choose '+k+' score='+bestScore);
                }
              }
            } catch (e) { logs.push('selector-error '+k+' -> '+String(e)); }
            if (!el) { el = findByKey(k); if (el) logs.push('fallback-selector '+k+' -> '+(el.id?('#'+el.id): (el.name?('name='+el.name): el.tagName))); }
            if (!el) { logs.push('not-found ' + k + ' -> ' + selector); continue; }
            if (el && highlight) {
              try { el.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' }); } catch {}
            }
            const before = getInfo(el);
            const result = await setVal(el, val);
            if (waitAfterFillMs && waitAfterFillMs > 0) { await delay(waitAfterFillMs); }
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
      return run().then(() => ({ ok: true, filled, logs, details })).catch(err => ({ ok:false, error: String(err), stack: (err && err.stack) ? String(err.stack) : undefined, logs }));
  } catch (e) { return { ok: false, error: String(e), stack: (e && e.stack) ? String(e.stack) : undefined }; }
  })();`;

  let res: any;
  try {
    res = await webview.executeJavaScript(fillScript, true);
  } catch (e: any) {
    const msg = String(e?.message || e || '');
    devLog?.('IDX-TS3-FILL-ERR', msg);
    if (/GUEST_VIEW_MANAGER_CALL|Script failed to execute/i.test(msg)) {
      await new Promise(r => setTimeout(r, 700));
      try {
        res = await webview.executeJavaScript(fillScript, true);
      } catch (e2: any) {
        devLog?.('IDX-TS3-FILL-ERR2', String(e2?.message || e2 || ''));
        throw e2;
      }
    } else {
      throw e;
    }
  }
  devLog?.('IDX-TS3-FILL', JSON.stringify({ ok: res?.ok, filled: res?.filled }));
  if (Array.isArray(res?.logs)) {
    (res.logs as string[]).forEach((ln: string, i: number) => devLog?.('IDX-TS3-TRACE', `${i.toString().padStart(3,'0')} ${ln}`));
  }
  if (res?.details) {
    const chunks = [] as any[];
    const arr = res.details;
    const size = 5;
    for (let i = 0; i < arr.length; i += size) { chunks.push(arr.slice(i, i + size)); }
    chunks.forEach((ch, idx) => devLog?.('IDX-TS3-DETAILS-'+idx, JSON.stringify(ch)));
  }
  return res;
}
