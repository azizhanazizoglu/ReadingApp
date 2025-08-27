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
        const btns = Array.from(document.querySelectorAll('button, input[type="button"], input[type="submit"]'));
        const t = String(txt).trim().toLowerCase();
        const found = btns.find(b => (b.textContent||'').trim().toLowerCase() === t || (b.id||'') === txt || (b.value||'') === txt);
        if (found) {
          if (highlight) {
            try {
              found.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
              const prev = found.style.outline;
              found.style.outline = '2px solid #3b82f6';
              setTimeout(() => { try { found.style.outline = prev; } catch {} }, 1200);
            } catch {}
          }
          found.click();
          return true;
        }
        return false;
      };
      let clicked = 0;
      actions.forEach(a => {
        try {
          if (typeof a !== 'string') return;
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
