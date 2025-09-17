export function getWebview(): any | null {
  const el: any = document.getElementById('app-webview');
  if (!el || typeof el.executeJavaScript !== 'function') return null;
  return el;
}

export async function getDomAndUrlFromWebview(devLog?: (c: string, m: string) => void): Promise<{ html?: string; url?: string; }> {
  const webview = getWebview();
  if (!webview) return {};
  try {
    devLog?.('IDX-TS2-WV-TRY', 'webview.executeJavaScript ile HTML çekme denemesi');
    const script = `(() => {
      try {
        const pickFrame = () => {
          const frames = Array.from(document.querySelectorAll('iframe'));
          let bestDoc = null; let bestScore = -1;
          for (const f of frames) {
            try {
              const doc = f.contentDocument || (f.contentWindow && f.contentWindow.document);
              if (!doc) continue; // cross-origin or not ready
              const cnt = doc.querySelectorAll('input, textarea, select, [contenteditable="true"]').length;
              const score = cnt; // could include size/visibility later
              if (score > bestScore) { bestScore = score; bestDoc = doc; }
            } catch (e) {}
          }
          return bestDoc;
        };
        const mainDoc = document;
        const chosen = pickFrame() || mainDoc;
        let html = '';
        let url = '';
        try { html = chosen.documentElement ? chosen.documentElement.outerHTML : (chosen.body ? chosen.body.outerHTML : ''); } catch (e) {}
        try { url = (chosen === mainDoc) ? document.URL : (chosen.URL || (chosen.location ? chosen.location.href : '')); } catch (e) {}
        return { html, url, source: (chosen === mainDoc ? 'main' : 'iframe') };
      } catch (e) { return { html: '', url: '', source: 'err', err: String(e) }; }
    })();`;
    const info = await webview.executeJavaScript(script, true);
    devLog?.('IDX-TS2-WV-OK', `webview HTML alındı len=${info?.html?.length || 0} url=${info?.url} src=${info?.source}`);
    return { html: info?.html, url: info?.url };
  } catch (e: any) {
    devLog?.('IDX-TS2-WV-ERR', String(e));
    return {};
  }
}

// Verify if a selector has a committed value in the active (iframe or main) document
export async function checkSelectorHasValue(selector: string, devLog?: (c: string, m: string) => void): Promise<boolean> {
  const webview = getWebview();
  if (!webview) return false;
  try {
    const script = `(() => {
      try {
        const pickDoc = () => {
          const frames = Array.from(document.querySelectorAll('iframe'));
          let bestDoc = null; let bestScore = -1;
          for (const f of frames) {
            try {
              const doc = f.contentDocument || (f.contentWindow && f.contentWindow.document);
              if (!doc) continue;
              const cnt = doc.querySelectorAll('input, textarea, select, [contenteditable="true"]').length;
              if (cnt > bestScore) { bestScore = cnt; bestDoc = doc; }
            } catch {}
          }
          return bestDoc || document;
        };
        const DOC = pickDoc();
        const el = DOC.querySelector(${JSON.stringify(selector)});
        if (!el) return false;
        const tag = (el.tagName||'').toLowerCase();
        if (tag === 'input') {
          const type = (el.type||'').toLowerCase();
          if (type === 'checkbox' || type === 'radio') return !!el.checked;
          return String(el.value||'').trim().length > 0;
        }
        if (tag === 'textarea') return String(el.value||'').trim().length > 0;
        if (tag === 'select') {
          const idx = el.selectedIndex;
          if (idx >= 0) {
            const opt = el.options[idx];
            const vv = String(el.value||'').trim();
            const tt = opt && opt.textContent ? String(opt.textContent).trim() : '';
            return vv.length > 0 || tt.length > 0;
          }
          return false;
        }
        if (el.getAttribute && el.getAttribute('contenteditable') === 'true') {
          return String(el.textContent||'').trim().length > 0;
        }
        return false;
      } catch { return false; }
    })();`;
    const ok = await webview.executeJavaScript(script, true);
    devLog?.('IDX-TS2-WV-VERIFY', `${selector} -> ${ok ? 'yes' : 'no'}`);
    return !!ok;
  } catch (e: any) {
    devLog?.('IDX-TS2-WV-VERIFY-ERR', String(e));
    return false;
  }
}

export async function getScreenshotFromWebview(devLog?: (c: string, m: string) => void): Promise<string | undefined> {
  const webview = getWebview();
  if (!webview) return undefined;
  try {
    // Render current viewport into a canvas and return data URL
    const script = `(() => {
      try {
        const w = document.documentElement.clientWidth || window.innerWidth || 1200;
        const h = document.documentElement.clientHeight || window.innerHeight || 800;
        const canvas = document.createElement('canvas');
        canvas.width = w; canvas.height = h;
        const ctx = canvas.getContext('2d');
        if (!ctx) return null;
  // html2canvas is not guaranteed; drawWindow may not exist in Electron; keep graceful
        const dataUrl = canvas.toDataURL('image/png');
        return dataUrl;
      } catch(e) { return null; }
    })();`;
    const dataUrl = await webview.executeJavaScript(script, true);
    if (typeof dataUrl === 'string' && dataUrl.startsWith('data:image/')) {
      devLog?.('IDX-TS2-WV-SHOT', 'screenshot captured');
      return dataUrl;
    }
  } catch (e: any) {
    devLog?.('IDX-TS2-WV-SHOT-ERR', String(e));
  }
  return undefined;
}

// Element picker: highlights hovered elements and returns a basic selector when clicked
export async function pickSelectorFromWebview(devLog?: (c: string, m: string) => void): Promise<string | undefined> {
  const webview = getWebview();
  if (!webview) return undefined;
  try {
    const script = `(() => {
      try {
        // Attach pick overlays/listeners to main doc and all same-origin iframes
        const getDocs = () => {
          const docs = [document];
          const frames = Array.from(document.querySelectorAll('iframe'));
          for (const f of frames) {
            try {
              const d = f.contentDocument || (f.contentWindow && f.contentWindow.document);
              if (d) docs.push(d);
            } catch {}
          }
          return docs;
        };
        const docs = getDocs();
        const state = { lastEl: null, lastDoc: null };
        const toSelector = (node) => {
          if (!node) return null;
          const tag = (node.tagName||'').toLowerCase();
          // prefer stable identifiers first
          const id = node.getAttribute && node.getAttribute('id'); if (id) return '#' + id;
          const dLovId = node.getAttribute && node.getAttribute('data-lov-id'); if (dLovId) return '[data-lov-id="' + dLovId + '"]';
          const dLovName = node.getAttribute && node.getAttribute('data-lov-name'); if (dLovName) return '[data-lov-name="' + dLovName + '"]';
          const name = node.getAttribute && node.getAttribute('name'); if (name) return tag + '[name="' + name + '"]';
          const aria = node.getAttribute && node.getAttribute('aria-label'); if (aria) return tag + '[aria-label="' + aria + '"]';
          const ph = node.getAttribute && node.getAttribute('placeholder'); if (ph) return tag + '[placeholder="' + ph + '"]';
          const cls = node.getAttribute && (node.getAttribute('class')||'').trim();
          if (cls) { const first = cls.split(/\s+/).filter(Boolean).slice(0,3).join('.'); if (first) return tag + '.' + first; }
          return tag || 'input';
        };
        const overlays = [];
        const makeOverlay = (DOC) => {
          const overlay = DOC.createElement('div');
          overlay.style.cssText = 'position:fixed;left:0;top:0;right:0;bottom:0;z-index:2147483647;pointer-events:none;';
          const box = DOC.createElement('div');
          box.style.cssText = 'position:absolute;border:2px solid #10b981;background:rgba(16,185,129,0.12);pointer-events:none;';
          overlay.appendChild(box);
          DOC.body.appendChild(overlay);
          const move = (ev) => {
            try {
              const el = DOC.elementFromPoint(ev.clientX, ev.clientY);
              if (!el || el === overlay || el === box) return;
              state.lastEl = el; state.lastDoc = DOC;
              const r = el.getBoundingClientRect();
              box.style.left = r.left + 'px'; box.style.top = r.top + 'px'; box.style.width = r.width + 'px'; box.style.height = r.height + 'px';
            } catch {}
          };
          const click = (ev) => {
            try {
              ev.preventDefault(); ev.stopPropagation();
              cleanup();
              const out = toSelector(state.lastEl);
              try { (DOC.defaultView||window).__PICK_SEL__ = out; } catch {}
              try { window.__PICK_SEL__ = out; } catch {}
              try { (window.top||window).__PICK_SEL__ = out; } catch {}
            } catch {}
          };
          DOC.addEventListener('mousemove', move, true);
          DOC.addEventListener('click', click, true);
          overlays.push({ DOC, overlay, move, click });
        };
        const cleanup = () => {
          for (const o of overlays) {
            try { o.DOC.removeEventListener('mousemove', o.move, true); } catch {}
            try { o.DOC.removeEventListener('click', o.click, true); } catch {}
            try { o.overlay.remove(); } catch {}
          }
        };
        for (const d of docs) makeOverlay(d);
        return 'READY';
      } catch(e) { return 'ERR'; }
    })();`;
    const ready = await webview.executeJavaScript(script, true);
    if (ready !== 'READY') return undefined;
    // Poll for result
  const poll = `new Promise((resolve)=>{ let n=0; const t=setInterval(()=>{ try{ const root = window; const v = (root).__PICK_SEL__ || (root.top && (root.top).__PICK_SEL__); if (v){ clearInterval(t); resolve(v); } else if (++n>80){ clearInterval(t); resolve(null); } }catch{ clearInterval(t); resolve(null);} }, 120); })`;
    const selector = await webview.executeJavaScript(poll, true);
    if (typeof selector === 'string' && selector.length > 0) {
      devLog?.('IDX-TS2-WV-PICK', selector);
      return selector;
    }
  } catch (e: any) {
    devLog?.('IDX-TS2-WV-PICK-ERR', String(e));
  }
  return undefined;
}

// Expose picker on window for simple calling from components
if (typeof window !== 'undefined') {
  (window as any).pickSelectorFromWebview = () => pickSelectorFromWebview((c,m)=>console.debug(c,m));
}

// Briefly highlight the element for a given selector in the active doc and return a small descriptor text
export async function previewSelectorInWebview(selector: string, devLog?: (c: string, m: string) => void): Promise<string | undefined> {
  const webview = getWebview();
  if (!webview) return undefined;
  try {
    const script = `(() => {
      try {
        const docs = [document, ...Array.from(document.querySelectorAll('iframe')).map(f=>{ try{ return f.contentDocument || (f.contentWindow&&f.contentWindow.document) }catch(e){ return null } }).filter(Boolean)];
        let FOUND = null, DOC = document;
        for (const d of docs){ try{ const el = d.querySelector(${JSON.stringify(selector)}); if (el){ FOUND = el; DOC = d; break; } } catch{} }
        const el = FOUND; if (!el) return null;
        const r = el.getBoundingClientRect();
        const hl = DOC.createElement('div');
        hl.style.cssText = 'position:fixed;border:2px solid #22d3ee;background:rgba(34,211,238,0.12);z-index:2147483646;left:'+r.left+'px;top:'+r.top+'px;width:'+r.width+'px;height:'+r.height+'px;pointer-events:none;border-radius:6px;';
        DOC.body.appendChild(hl);
        setTimeout(()=>{ try{ hl.remove(); }catch{} }, 900);
        const tag = (el.tagName||'').toLowerCase();
        const id = el.getAttribute('id');
        const name = el.getAttribute('name');
        const ph = el.getAttribute('placeholder');
        const aria = el.getAttribute('aria-label');
        return [tag, id?('#'+id):'', name?('name='+name):'', ph?('ph='+ph):'', aria?('aria='+aria):''].filter(Boolean).join(' ');
      } catch { return null; }
    })();`;
    const info = await webview.executeJavaScript(script, true);
    if (typeof info === 'string' && info.length) {
      devLog?.('IDX-TS2-WV-PREVIEW', info);
      return info;
    }
  } catch (e: any) {
    devLog?.('IDX-TS2-WV-PREVIEW-ERR', String(e));
  }
  return undefined;
}

if (typeof window !== 'undefined') {
  (window as any).previewSelectorInWebview = (sel: string) => previewSelectorInWebview(sel, (c,m)=>console.debug(c,m));
}

// Check if selector resolves to an element in the active document
export async function checkSelectorInWebview(selector: string, devLog?: (c: string, m: string) => void): Promise<boolean> {
  const webview = getWebview();
  if (!webview) return false;
  try {
    const script = `(() => {
      try {
        const docs = [document, ...Array.from(document.querySelectorAll('iframe')).map(f=>{ try{ return f.contentDocument || (f.contentWindow&&f.contentWindow.document) }catch(e){ return null } }).filter(Boolean)];
        for (const d of docs){ try{ if (d.querySelector(${JSON.stringify(selector)})) return true; } catch{} }
        return false;
      } catch { return false; }
    })();`;
    const ok = await webview.executeJavaScript(script, true);
    devLog?.('IDX-TS2-WV-CHECK', `${selector} -> ${ok ? 'yes' : 'no'}`);
    return !!ok;
  } catch (e: any) {
    devLog?.('IDX-TS2-WV-CHECK-ERR', String(e));
    return false;
  }
}

if (typeof window !== 'undefined') {
  (window as any).checkSelectorInWebview = (sel: string) => checkSelectorInWebview(sel, (c,m)=>console.debug(c,m));
}

// Get element outerHTML snippet for selector (truncated and sanitized for display)
export async function getElementHtmlInWebview(selector: string, maxLen = 1000, devLog?: (c: string, m: string) => void): Promise<string | undefined> {
  const webview = getWebview();
  if (!webview) return undefined;
  try {
    const script = `(() => {
      try {
        const docs = [document, ...Array.from(document.querySelectorAll('iframe')).map(f=>{ try{ return f.contentDocument || (f.contentWindow&&f.contentWindow.document) }catch(e){ return null } }).filter(Boolean)];
        let el = null;
        for (const d of docs){ try{ const cand = d.querySelector(${JSON.stringify(selector)}); if (cand){ el = cand; break; } } catch{} }
        if (!el) return null;
        let html = el.outerHTML || '';
        // Normalize whitespace minimally; keep linebreaks
        html = html.replace(/\t/g, '  ');
        if (html.length > ${Math.max(200, 1000)}) html = html.slice(0, ${Math.max(200, 1000)}) + '\n…';
        return html;
      } catch { return null; }
    })();`;
    const snippet = await webview.executeJavaScript(script, true);
    if (typeof snippet === 'string' && snippet.length) {
      devLog?.('IDX-TS2-WV-HTML', `len=${snippet.length}`);
      return snippet;
    }
  } catch (e: any) {
    devLog?.('IDX-TS2-WV-HTML-ERR', String(e));
  }
  return undefined;
}

if (typeof window !== 'undefined') {
  (window as any).getElementHtmlInWebview = (sel: string, maxLen?: number) => getElementHtmlInWebview(sel, maxLen, (c,m)=>console.debug(c,m));
}
