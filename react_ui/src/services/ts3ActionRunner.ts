import { getWebview } from './webviewDom';

export async function runActions(actions: string[] | undefined, highlight: boolean, devLog?: (c: string, m: string) => void) {
  const webview = getWebview();
  if (!webview) throw new Error('Webview bulunamadı.');
  const script = `(() => {
    try {
      let actions = ${JSON.stringify(actions)};
      if (!Array.isArray(actions) || actions.length === 0) {
        actions = ['click#DEVAM','click#İLERİ','click#ILERI','click#Next','click#NEXT'];
      }
      const logs = [];
      const highlight = ${JSON.stringify(highlight)};
      const clickByText = (txt) => {
        try {
          const t = String(txt).trim().toLowerCase();
          const nodes = Array.from(document.querySelectorAll('button, a, [role="button"], input[type="button"], input[type="submit"]'));
          const found = nodes.find(b => {
            const text = (b.textContent || '').trim().toLowerCase();
            const id = (b.id || '');
            const val = (b && (b).value !== undefined) ? (b).value : '';
            return text === t || id === txt || val === txt;
          });
          if (found) {
            if (highlight) {
              try {
                if (found && found.scrollIntoView) {
                  found.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
                }
                const prev = (found && (found).style) ? (found).style.outline : undefined;
                if ((found).style) {
                  (found).style.outline = '2px solid #3b82f6';
                  setTimeout(() => { try { (found).style.outline = prev; } catch {} }, 1200);
                }
              } catch {}
            }
            if (found && (found).click) { (found).click(); }
            return true;
          }
        } catch {}
        return false;
      };
      const clickByCss = (sel) => {
        try {
          // Support special pseudo selectors we sometimes emit
          if (sel && typeof sel === 'string') {
            // Delegate text=... to text clicker
            if (sel.startsWith('text=')) {
              const textValue = sel.slice(5);
              return clickByText(textValue);
            }
            // Handle :has-text('...') and :contains('...') by extracting the text and using text click
            const hasTextMatch = sel.match(/:has-text\((?:'([^']+)'|"([^"]+)")\)/i);
            const containsMatch = sel.match(/:contains\((?:'([^']+)'|"([^"]+)")\)/i);
            const textLike = (hasTextMatch && (hasTextMatch[1] || hasTextMatch[2])) || (containsMatch && (containsMatch[1] || containsMatch[2]));
            if (textLike) {
              return clickByText(textLike);
            }
            // Ignore Playwright/XPath selectors (xpath=...)
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
          if ((el).click) { (el).click(); }
          return true;
        } catch { return false; }
      };
      let clicked = 0;
      actions.forEach(a => {
        try {
          if (typeof a !== 'string') return;
          if (a.startsWith('css#')) {
            const sel = a.slice(4);
            if (clickByCss(sel)) { clicked++; logs.push('css-click '+sel); } else { logs.push('css-notfound '+sel); }
            return;
          }
          const [kind, arg] = a.split('#');
          if (kind === 'click' && arg) { if (clickByText(arg)) { clicked++; logs.push('clicked '+arg); } else { logs.push('notfound '+arg); } }
        } catch (e) { logs.push('err '+String(e)); }
      });
      return { ok: true, clicked, logs };
    } catch (e) { return { ok: false, error: String(e) }; }
  })();`;
  const res = await webview.executeJavaScript(script, true);
  devLog?.('IDX-TS3-ACTIONS', JSON.stringify(res));
  return res;
}
