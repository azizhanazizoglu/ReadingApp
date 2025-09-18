// Developer log tipi window'a ekleniyor
declare global {
  interface Window {
    __DEV_LOGS?: Array<{
      time: string;
      component: string;
      state: string;
      code?: string;
      message?: string;
    }>;
  }
}
import React from "react";
import { createPortal } from 'react-dom';
// timeout overlay kaldırıldı; sürekli etkileşimli bir tarayıcı görünümü isteniyor


interface BrowserViewProps {
  iframeUrl: string;
  loading: boolean;
  uploading: boolean;
  darkMode: boolean;
  fontStack: string;
  handleIframeLoad: () => void;
  result: string | null;
  onUrlChange?: (url: string) => void;
}


export const BrowserView: React.FC<BrowserViewProps & { style?: React.CSSProperties }> = ({
  iframeUrl,
  loading,
  uploading,
  darkMode,
  fontStack,
  handleIframeLoad,
  result,
  onUrlChange,
  style = {},
}) => {
  // Timeout overlay devre dışı
  React.useEffect(() => {
    if (typeof window !== 'undefined') {
      if (!window.__DEV_LOGS) window.__DEV_LOGS = [];
      if (loading) {
        window.__DEV_LOGS.push({
          time: new Date().toISOString(),
          component: 'BrowserView',
          state: 'loading',
          code: 'BV-1001',
          message: 'BrowserView loading state aktif.'
        });
      }
      if (uploading) {
        window.__DEV_LOGS.push({
          time: new Date().toISOString(),
          component: 'BrowserView',
          state: 'uploading',
          code: 'BV-1002',
          message: 'BrowserView uploading state aktif.'
        });
      }
    }
  }, [loading, uploading]);

  // Hata yakalama örneği (ileride global error handler ile entegre edilebilir)
  const handleError = (err: any, context: string) => {
    if (typeof window !== 'undefined') {
      if (!window.__DEV_LOGS) window.__DEV_LOGS = [];
      window.__DEV_LOGS.push({
        time: new Date().toISOString(),
        component: 'BrowserView',
        state: 'error',
        code: 'BV-9001',
        message: `Hata (${context}): ${err?.message || err}`
      });
    }
  };

  // Webview event bindings: sync URL and loading states
  React.useEffect(() => {
    const el = document.getElementById('app-webview') as any;
    if (!el) return;
    const onDomReady = () => {
      try {
        // URL'yi al ve üst seviyeye bildir
        const u = el.getURL ? el.getURL() : el.src;
        if (onUrlChange && typeof u === 'string' && u) onUrlChange(u);
      } catch {}
    };
    const onDidNavigate = (_e: any, url?: string) => {
      try {
        const u = (typeof url === 'string' && url) ? url : (el.getURL ? el.getURL() : el.src);
        if (onUrlChange && typeof u === 'string' && u) onUrlChange(u);
      } catch {}
    };
    const onStart = () => {
      if (typeof window !== 'undefined') {
        if (!window.__DEV_LOGS) window.__DEV_LOGS = [];
        window.__DEV_LOGS.push({ time: new Date().toISOString(), component: 'BrowserView', state: 'event', code: 'BV-2001', message: 'webview did-start-loading' });
      }
    };
    const onStop = () => {
      if (typeof window !== 'undefined') {
        if (!window.__DEV_LOGS) window.__DEV_LOGS = [];
        window.__DEV_LOGS.push({ time: new Date().toISOString(), component: 'BrowserView', state: 'event', code: 'BV-2002', message: 'webview did-stop-loading' });
      }
      // Yükleme bitti kabul edelim
      try { handleIframeLoad(); } catch {}
      // URL'i güncelle
      try {
        const u = el.getURL ? el.getURL() : el.src;
        if (onUrlChange && typeof u === 'string' && u) onUrlChange(u);
      } catch {}
    };
    el.addEventListener('dom-ready', onDomReady);
    el.addEventListener('did-navigate', onDidNavigate);
    el.addEventListener('did-navigate-in-page', onDidNavigate);
    el.addEventListener('did-start-loading', onStart);
    el.addEventListener('did-stop-loading', onStop);
    return () => {
      try { el.removeEventListener('dom-ready', onDomReady); } catch {}
      try { el.removeEventListener('did-navigate', onDidNavigate); } catch {}
      try { el.removeEventListener('did-navigate-in-page', onDidNavigate); } catch {}
      try { el.removeEventListener('did-start-loading', onStart); } catch {}
      try { el.removeEventListener('did-stop-loading', onStop); } catch {}
    };
  }, [iframeUrl, handleIframeLoad, onUrlChange]);
  const content = (
      <div
        className="flex-grow w-full rounded-3xl shadow-2xl border border-[#B3C7E6] dark:border-[#335C81] flex items-center justify-center transition-colors overflow-hidden"
        style={{
          minHeight: 520,
          maxHeight: 1100,
          height: 'calc(70vh + 80px)',
          marginBottom: 8,
          marginTop: 24,
          position: "relative",
          background: darkMode ? undefined : "rgba(238,245,255,0.97)",
          ...style,
        }}
      >
        {iframeUrl ? (
          // eslint-disable-next-line @typescript-eslint/ban-ts-comment
          // @ts-ignore
          <webview
            id="app-webview"
            key={iframeUrl}
            src={iframeUrl}
            className="w-full h-full min-h-[540px] rounded-3xl border-none"
            style={{ background: "white" }}
          />
        ) : (
          <span className="text-[#7B8FA1] dark:text-[#B3C7E6] text-xl select-none">
            [ Web sitesi burada görünecek ]
          </span>
        )}
      </div>
  );

  // If calibration sliding host exists, mount there (removes margins & rounded mismatch if desired)
  const hostEl = typeof document !== 'undefined' ? document.getElementById('calibration-iframe-host') : null;
  if (hostEl) {
    return createPortal(
      <div style={{ position:'absolute', inset:0, padding:16, boxSizing:'border-box' }}>
        {React.cloneElement(content, { style: { ...((content as any).props.style||{}), marginTop:0, marginBottom:0, height:'100%', maxHeight:'100%', borderRadius:24 } })}
      </div>,
      hostEl
    );
  }
  return content;
};
