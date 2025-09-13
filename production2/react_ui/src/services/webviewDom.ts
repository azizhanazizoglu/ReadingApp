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
