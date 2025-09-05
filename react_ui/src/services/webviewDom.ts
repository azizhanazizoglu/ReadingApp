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
    const html = await webview.executeJavaScript('document.documentElement.outerHTML', true);
    const url = await webview.executeJavaScript('document.URL', true);
    devLog?.('IDX-TS2-WV-OK', `webview HTML alındı len=${html?.length || 0} url=${url}`);
    return { html, url };
  } catch (e: any) {
    devLog?.('IDX-TS2-WV-ERR', String(e));
    return {};
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
        // html2canvas is not guaranteed; try drawWindow if available (some engines expose it)
        if ((window as any).drawWindow) {
          try { (window as any).drawWindow(window, 0, 0, w, h, 'white'); } catch {}
        }
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
