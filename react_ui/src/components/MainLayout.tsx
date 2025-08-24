
import { Header } from "@/components/Header";
import { BrowserView } from "@/components/BrowserView";
import { CommandPanel } from "@/components/CommandPanel";
import { Footer } from "@/components/Footer";
import React, { useState, useEffect } from "react";

interface MainLayoutProps {
  appName: string;
  darkMode: boolean;
  fontStack: string;
  address: string;
  setAddress: (v: string) => void;
  handleGo: (address: string) => void;
  loading: boolean;
  automation: boolean;
  handleAutomation: () => void;
  iframeUrl: string;
  uploading: boolean;
  handleUploadClick: () => void;
  fileInputRef: React.RefObject<HTMLInputElement>;
  handleFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  result: any;
  handleIframeLoad: () => void;
  commandLog: any[];
  status: string;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  appName,
  darkMode,
  fontStack,
  address,
  setAddress,
  handleGo,
  loading,
  automation,
  handleAutomation,
  iframeUrl,
  uploading,
  handleUploadClick,
  fileInputRef,
  handleFileChange,
  result,
  handleIframeLoad,
  commandLog,
  status,
}) => {
  const [logPanelOpen, setLogPanelOpen] = useState(false);
  const [backendLogs, setBackendLogs] = useState<string[]>([]);

  // Backend loglarını çek
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await fetch("http://localhost:5001/api/logs");
        const data = await res.json();
        setBackendLogs(data.logs || []);
      } catch (e) {
        setBackendLogs(["[ERROR] Backend logları alınamadı."]);
      }
    };
    fetchLogs();
    const interval = setInterval(fetchLogs, 2000);
    return () => clearInterval(interval);
  }, []);
  return (
    <div
      className="h-screen w-screen flex flex-col items-center justify-between bg-gradient-to-br from-[#f8fafc] to-[#e6f0fa] dark:from-[#1a2233] dark:to-[#223a5e] transition-colors overflow-hidden"
      style={{
        fontFamily: fontStack,
        minHeight: 0,
        minWidth: 0,
        height: '100vh',
        width: '100vw',
      }}
    >
      {/* Sağ alt köşede log butonu */}
      <button
        onClick={() => setLogPanelOpen((v) => !v)}
        className="fixed bottom-7 right-10 z-40 bg-white/90 dark:bg-[#223A5E] border border-[#B3C7E6] dark:border-[#335C81] rounded-full shadow-lg p-2 hover:bg-[#E6F0FA] dark:hover:bg-[#335C81] transition-all flex items-center gap-2"
        style={{ minWidth: 44, minHeight: 44 }}
        aria-label="Logları Göster"
      >
        <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
          <rect x="3" y="5" width="18" height="14" rx="3"/>
          <path d="M8 9h8M8 13h6" />
        </svg>
        <span className="font-semibold text-[#0057A0] dark:text-[#E6F0FA] text-base select-none">Log</span>
      </button>

      {/* Sağdan açılan log paneli: sadece developer logları (window.__DEV_LOGS) */}
      <div
        className={`fixed top-0 right-0 h-full w-[370px] bg-white dark:bg-[#223A5E] shadow-2xl border-l border-[#B3C7E6] dark:border-[#335C81] z-50 transition-transform duration-300 ${logPanelOpen ? 'translate-x-0' : 'translate-x-full'}`}
        style={{ fontFamily: fontStack }}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#B3C7E6] dark:border-[#335C81] bg-[#F8FAFC] dark:bg-[#223A5E]">
          <span className="font-bold text-lg text-[#0057A0] dark:text-[#E6F0FA]">Loglar (Developer)</span>
          <button onClick={() => setLogPanelOpen(false)} className="text-[#0057A0] dark:text-[#E6F0FA] text-2xl font-bold">×</button>
        </div>
        <div className="overflow-y-auto px-6 py-4" style={{ maxHeight: 'calc(100vh - 80px)' }}>
          {/* Hem frontend (window.__DEV_LOGS) hem backend loglarını göster */}
          <ul className="space-y-3">
            {/* Frontend logları */}
            {typeof window !== 'undefined' && window.__DEV_LOGS && window.__DEV_LOGS.length > 0 &&
              window.__DEV_LOGS.slice(-30).reverse().map((log, i) => (
                <li key={"frontend-"+i} className="flex flex-col gap-1 p-2 rounded-lg bg-[#F8FAFC] dark:bg-[#335C81] border border-[#B3C7E6] dark:border-[#335C81]">
                  <span className="text-xs text-[#7B8FA1] dark:text-[#B3C7E6]">{log.time.split('T')[1].slice(0,8)} | <b>{log.component}</b> | <b>{log.code}</b></span>
                  <span className="text-sm font-medium text-[#0057A0] dark:text-[#E6F0FA]">{log.message || log.state}</span>
                </li>
              ))}
            {/* Backend logları */}
            {backendLogs.slice(-30).reverse().map((log, i) => (
              <li key={"backend-"+i} className="flex flex-col gap-1 p-2 rounded-lg bg-[#FFF7E6] dark:bg-[#665C3A] border border-[#FFD580] dark:border-[#665C3A]">
                <span className="text-xs text-[#B38B00] dark:text-[#FFD580]">{`BACKEND | #${backendLogs.length- i}`} | <b>BACKEND</b> | <b>BL-{String(1000 + backendLogs.length-i)}</b></span>
                <span className="text-sm font-medium text-[#B38B00] dark:text-[#FFD580]">{log}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="px-6 py-3 border-t border-[#B3C7E6] dark:border-[#335C81] bg-[#F8FAFC] dark:bg-[#223A5E] text-xs text-[#7B8FA1] dark:text-[#B3C7E6]">
          Son state: <span className="font-semibold text-[#0057A0] dark:text-[#E6F0FA]">{status}</span>
        </div>
      </div>

      <Header
        appName={appName}
        darkMode={darkMode}
        fontStack={fontStack}
        address={address}
        setAddress={setAddress}
        handleGo={() => handleGo(address)}
        loading={loading}
        automation={automation}
        handleAutomation={handleAutomation}
        iframeUrl={iframeUrl}
        uploading={uploading}
        handleUploadClick={handleUploadClick}
        fileInputRef={fileInputRef}
        handleFileChange={handleFileChange}
      />
      <main
        className="flex flex-col items-center w-full flex-1 px-8"
        style={{
          maxWidth: 1400,
          width: "100%",
          flex: 1,
          minHeight: 0,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'flex-start',
        }}
      >
        <BrowserView
          iframeUrl={iframeUrl}
          loading={loading}
          uploading={uploading}
          darkMode={darkMode}
          fontStack={fontStack}
          handleIframeLoad={handleIframeLoad}
          result={result}
          style={{ minHeight: 520, height: 'calc(70vh + 80px)' }}
        />
        <div style={{ height: 38 }} />
        <CommandPanel
          commandLog={commandLog}
          fontStack={fontStack}
          darkMode={darkMode}
        />
      </main>
      <Footer fontStack={fontStack} status={status} darkMode={darkMode} />
  {/* BackendLogPanel kaldırıldı, loglar birleşik panelde gösteriliyor */}
  </div>
  );
};
