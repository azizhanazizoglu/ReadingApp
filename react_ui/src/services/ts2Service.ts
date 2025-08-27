import { getDomAndUrlFromWebview } from './webviewDom';

export async function runTs2(backEndUrl: string, iframeUrl: string | undefined, devLog?: (c: string, m: string) => void) {
  const { html, url } = await getDomAndUrlFromWebview(devLog);
  const payload: any = {};
  const activeUrl = url || iframeUrl;
  if (activeUrl) payload.url = activeUrl;
  if (html) payload.html = html;
  devLog?.('IDX-TS2-PAYLOAD', `payload: url=${activeUrl || ''} html_len=${html?.length || 0}`);
  const r = await fetch(`${backEndUrl}/api/test-state-2`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({} as any));
    throw new Error(err.error || 'Test State 2 failed');
  }
  const data = await r.json();
  devLog?.('IDX-TS2-200', `TS2 çağrıldı (url=${activeUrl || ''})${html ? ', html inline' : ''}. Mapping kaydedildi: ${data.path}`);
  return data;
}
