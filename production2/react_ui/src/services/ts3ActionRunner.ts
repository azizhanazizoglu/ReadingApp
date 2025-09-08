import { getWebview } from './webviewDom';

export async function runActions(actions: string[] | undefined, highlight: boolean, devLog?: (c: string, m: string) => void) {
  const webview = getWebview();
  if (!webview) throw new Error('Webview bulunamadı.');
  const script = `(() => {
    const delay = (ms) => new Promise(r => setTimeout(r, ms));
    const isVisible = (el) => {
      try {
        if (!el) return false;
        const rects = el.getClientRects && el.getClientRects();
        if (!rects || rects.length === 0) return false;
        const cs = window.getComputedStyle ? window.getComputedStyle(el) : null;
        if (cs && (cs.visibility === 'hidden' || cs.display === 'none' || Number(cs.opacity) === 0)) return false;
        return true;
      } catch { return true; }
    };
  const isMenuSelector = (s) => {
      try { const ss = String(s).toLowerCase(); return /aria-label\s*=\s*['\"]menu['\"]/i.test(ss) || /lucide-menu/i.test(ss) || /data-lov-name\s*=\s*['\"]menu['\"]/i.test(ss) || /\bmenu\b/i.test(ss); } catch { return false; }
    };
    const isMenuElement = (el) => {
      try {
        const aria = (el && el.getAttribute) ? String(el.getAttribute('aria-label')||'').toLowerCase() : '';
        if (aria === 'menu') return true;
        if (el && el.querySelector) { if (el.querySelector('svg.lucide-menu')) return true; }
      } catch {}
      return false;
    };
    const nodeText = (el) => {
      try { return String((el && el.textContent) ? el.textContent : '').replace(/\s+/g,' ').trim().toLowerCase(); } catch { return ''; }
    };
    const scoreNode = (el) => {
      try {
        let s = 0;
        const tag = (el && el.tagName ? el.tagName : '').toLowerCase();
        const role = el && el.getAttribute ? String(el.getAttribute('role')||'').toLowerCase() : '';
        if (tag === 'button' || tag === 'a' || tag === 'input') s += 2;
        if (role === 'button') s += 1;
        if (role === 'menuitem') s += 3;
        if (isVisible(el)) s += 1;
        return s;
      } catch { return 0; }
    };
  const clickElementOrAncestor = (el) => {
      try {
        let cur = el;
        let hop = 0; const maxHop = 5;
        while (cur && hop < maxHop) {
      if (typeof cur.click === 'function') { cur.click(); return cur; }
      cur = cur.parentElement; hop++;
        }
      } catch {}
      return null;
    };
  return (async () => {
      try {
        let actions = ${JSON.stringify(actions)};
        if (!Array.isArray(actions) || actions.length === 0) {
          actions = ['click#DEVAM','click#İLERİ','click#ILERI','click#Next','click#NEXT'];
        }
        const logs = [];
        const highlight = ${JSON.stringify(highlight)};
  let lastWasMenu = false;
  const clickByText = async (txt) => {
          try {
    const tRaw = String(txt);
    const t = tRaw.trim().toLowerCase();
  const nodes = Array.from(document.querySelectorAll('*'));
  const pool = nodes.sort((a,b) => scoreNode(b) - scoreNode(a));
  const found = pool.find(b => {
      const text = nodeText(b);
      if (!text) return false;
      const id = (b.id || '').toLowerCase();
      const title = (b.getAttribute && (b.getAttribute('title')||'').toLowerCase()) || '';
      const aria = (b.getAttribute && (b.getAttribute('aria-label')||'').toLowerCase()) || '';
      const val = (b && (b).value !== undefined) ? String((b).value).toLowerCase() : '';
      const hit = text.includes(t) || id === t || title.includes(t) || aria.includes(t) || val === t;
      return hit && isVisible(b);
    });
            if (found) {
              if (highlight) {
                try {
                  if (found && found.scrollIntoView) {
                    found.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
                  }
      const prev = (found && found.style) ? found.style.outline : undefined;
      if ((found).style) {
        found.style.outline = '2px solid #3b82f6';
        setTimeout(() => { try { found.style.outline = prev; } catch {} }, 1200);
                  }
                } catch {}
              }
              const clickedEl = clickElementOrAncestor(found) || found;
      if (isMenuElement(clickedEl)) { lastWasMenu = true; await delay(800); } else { lastWasMenu = false; }
              return true;
            }
          } catch {}
          return false;
        };
        const clickByCss = async (sel) => {
          try {
            if (sel && typeof sel === 'string') {
              if (sel.startsWith('text=')) {
                const textValue = sel.slice(5);
                return await clickByText(textValue);
              }
              const hasTextMatch = sel.match(/:has-text\((?:'([^']+)'|"([^"]+)")\)/i);
              const containsMatch = sel.match(/:contains\((?:'([^']+)'|"([^"]+)")\)/i);
              const textLike = (hasTextMatch && (hasTextMatch[1] || hasTextMatch[2])) || (containsMatch && (containsMatch[1] || containsMatch[2]));
              if (textLike) {
                const ok = await clickByText(textLike);
                if (!ok && lastWasMenu) {
                  // One-time ensure: re-open menu and retry
                  try {
                    const reopen = document.querySelector("button[aria-label='Menu']")
                      || document.querySelector("button:has([data-lov-name='Menu'])")
                      || document.querySelector('button:has(svg.lucide-menu)');
                    if (reopen && typeof reopen.click === 'function') { reopen.click(); logs.push('retry: reopen-menu'); await delay(800); }
                  } catch {}
                  const ok2 = await clickByText(textLike);
                  if (ok2) { logs.push('retry: clicked '+textLike); lastWasMenu = false; }
                  return ok2;
                }
                return ok;
              }
              if (/^xpath=/i.test(sel)) {
                return false;
              }
            }
            const el = document.querySelector(sel);
            if (!el) return false;
            if (highlight) {
              try {
                if ((el).scrollIntoView) {
                  (el).scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
                }
                const prev = (el).style ? (el).style.outline : undefined;
                if ((el).style) {
                  (el).style.outline = '2px solid #22c55e';
                  setTimeout(() => { try { (el).style.outline = prev; } catch {} }, 1200);
                }
              } catch {}
            }
            const clickedEl = clickElementOrAncestor(el) || el;
            if (isMenuSelector(sel) || isMenuElement(clickedEl)) { lastWasMenu = true; await delay(800); } else { lastWasMenu = false; }
            return true;
          } catch { return false; }
        };
        let clicked = 0;
        for (const a of actions) {
          try {
            if (typeof a !== 'string') continue;
            if (a.startsWith('css#')) {
              const sel = a.slice(4);
              if (await clickByCss(sel)) { clicked++; logs.push('css-click '+sel); } else { logs.push('css-notfound '+sel); }
              continue;
            }
            const [kind, arg] = a.split('#');
            if (kind === 'click' && arg) { if (await clickByText(arg)) { clicked++; logs.push('clicked '+arg); } else { logs.push('notfound '+arg); } }
          } catch (e) { logs.push('err '+String(e)); }
        }
        return { ok: true, clicked, logs };
      } catch (e) { return { ok: false, error: String(e) }; }
    })();
  })();`;
  const res = await webview.executeJavaScript(script, true);
  devLog?.('IDX-TS3-ACTIONS', JSON.stringify(res));
  return res;
}
