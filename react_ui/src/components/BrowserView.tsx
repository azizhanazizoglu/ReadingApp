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
import { useLoadingTimeout } from "../errorHandling/errorHandling";


interface BrowserViewProps {
  iframeUrl: string;
  loading: boolean;
  uploading: boolean;
  darkMode: boolean;
  fontStack: string;
  handleIframeLoad: () => void;
  result: string | null;
}


export const BrowserView: React.FC<BrowserViewProps & { style?: React.CSSProperties }> = ({
  iframeUrl,
  loading,
  uploading,
  darkMode,
  fontStack,
  handleIframeLoad,
  result,
  style = {},
}) => {
  const [timeoutActive, setTimeoutActive] = React.useState(false);
  useLoadingTimeout({ loading, setTimeoutActive });
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
  return (
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
        <iframe
          key={iframeUrl}
          src={iframeUrl}
          title="Webpage"
          className="w-full h-full min-h-[540px] rounded-3xl border-none"
          style={{ background: "white" }}
          onLoad={handleIframeLoad}
        />
      ) : (
        <span className="text-[#7B8FA1] dark:text-[#B3C7E6] text-xl select-none">
          [ Web sitesi burada görünecek ]
        </span>
      )}
      {(loading || uploading) && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/70 dark:bg-[#223A5E]/80 z-10 rounded-3xl">
          <span className="text-[#0057A0] dark:text-[#E6F0FA] text-lg font-semibold animate-pulse">
            {loading ? "Yükleniyor..." : "Yükleniyor..."}
          </span>
        </div>
      )}
      {timeoutActive && (
        <div className="timeout-overlay" style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', background: 'rgba(0,0,0,0.7)', zIndex: 10, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ color: 'red', fontWeight: 'bold', fontSize: 20 }}>Yükleme çok uzun sürdü! (Timeout)</span>
        </div>
      )}
      {result && (
        <div className="w-full max-w-6xl mb-4 p-4 rounded-xl bg-white/80 dark:bg-[#335C81]/80 shadow text-[#003366] dark:text-[#E6F0FA] text-center text-base break-words">
          {result}
        </div>
      )}
    </div>
  );
};
