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
