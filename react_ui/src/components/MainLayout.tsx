
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
  developerMode?: boolean;
  onToggleDeveloperMode?: () => void;
  onDevHome?: () => void;
  onDevTestSt1?: () => void;
  onDevTestSt2?: () => void;
  onDevTestSt3?: () => void;
  // TS3 debug options
  ts3Highlight?: boolean;
  ts3Typing?: boolean;
  ts3Delay?: number;
  setTs3Highlight?: (v: boolean) => void;
  setTs3Typing?: (v: boolean) => void;
  setTs3Delay?: (v: number) => void;
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
  developerMode = false,
  onToggleDeveloperMode,
  onDevHome,
  onDevTestSt1,
  onDevTestSt2,
  onDevTestSt3,
  ts3Highlight = true,
  ts3Typing = true,
  ts3Delay = 200,
  setTs3Highlight,
  setTs3Typing,
  setTs3Delay,
}) => {
  const [logPanelOpen, setLogPanelOpen] = useState(false);
  const [backendLogs, setBackendLogs] = useState<any[]>([]);
  const [backendStatus, setBackendStatus] = useState<string>("");
  const [currentUrl, setCurrentUrl] = useState<string>("");
  const refreshBackendLogs = React.useCallback(async () => {
    try {
      const res = await fetch("http://localhost:5001/api/logs");
      const data = await res.json();
      setBackendLogs(data.logs || []);
    } catch {
      // ignore
    }
  }, []);

  // Backend loglarını çek
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await fetch("http://localhost:5001/api/logs");
        const data = await res.json();
        const logs = data.logs || [];
        setBackendLogs(logs);
        // En güncel backend info'yu status olarak ayarla (tek tip, Türkçe, kısaltılmış)
        if (logs.length > 0) {
          const last = logs[logs.length - 1];
          try {
            const levelMap: Record<string, string> = { 'INFO': 'BİLGİ', 'WARN': 'UYARI', 'WARNING': 'UYARI', 'ERROR': 'HATA', 'DEBUG': 'DEBUG' };
            if (typeof last === 'string') {
              const msg = last.toString();
              const trLevel = 'BİLGİ';
              const code = 'BE-LEGACY';
              const shortMsg = msg.length > 90 ? (msg.slice(0, 90) + '…') : msg;
              setBackendStatus(`[${trLevel}] ${code}: ${shortMsg}`);
            } else {
              const level = (last.level || 'INFO').toString().toUpperCase();
              const trLevel = levelMap[level] || 'BİLGİ';
              const code = last.code || 'BE-XXXX';
              const rawMsg = (last.message || '').toString();
              const extra = last.extra || {};
              let suffix = '';
              if (extra && extra.path) {
                const p = extra.path.toString();
                const parts = p.split(/\\|\//);
                const file = parts[parts.length - 1] || '';
                const folder = parts[parts.length - 2] || '';
                suffix = file ? ` (${folder}/${file})` : '';
              }
              const msg = rawMsg + suffix;
              const shortMsg = msg.length > 90 ? (msg.slice(0, 90) + '…') : msg;
              setBackendStatus(`[${trLevel}] ${code}: ${shortMsg}`);
            }
          } catch {
            setBackendStatus('');
          }
        } else setBackendStatus("");
      } catch (e) {
        setBackendLogs(["[ERROR] Backend logları alınamadı."]);
        setBackendStatus("[ERROR] Backend logları alınamadı.");
      }
    };
    fetchLogs();
    const interval = setInterval(fetchLogs, 2000);
    return () => clearInterval(interval);
  }, []);
  // Webview URL değiştiğinde arama kutusunu güncelle
  useEffect(() => {
    if (currentUrl && currentUrl !== address) {
      try {
        setAddress(currentUrl);
      } catch {}
    }
  }, [currentUrl]);
  return (
    <div
      className={"h-screen w-screen flex flex-col items-center justify-between bg-gradient-to-br from-[#f8fafc] to-[#e6f0fa] dark:from-[#1a2233] dark:to-[#223a5e] transition-colors overflow-hidden"}
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
          <div className="flex items-center gap-2">
            <button
              onClick={async () => {
                // Clear FE logs
                try {
                  if (typeof window !== 'undefined') {
                    (window as any).__DEV_LOGS = [];
                  }
                } catch {}
                // Clear BE logs
                try {
                  await fetch('http://localhost:5001/api/logs/clear', { method: 'POST' });
                } catch {}
                // Refresh list
                await refreshBackendLogs();
              }}
              className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] text-[#0057A0] dark:bg-[#335C81] dark:hover:bg-[#446E9B] dark:text-[#E6F0FA] text-sm font-semibold"
              title="Logları temizle"
            >
              Temizle
            </button>
            <button onClick={() => setLogPanelOpen(false)} className="text-[#0057A0] dark:text-[#E6F0FA] text-2xl font-bold">×</button>
          </div>
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
            {backendLogs.slice(-30).reverse().map((log, i) => {
              const key = `backend-${i}`;
              if (typeof log === 'string') {
                return (
                  <li key={key} className="flex flex-col gap-1 p-2 rounded-lg bg-[#FFF7E6] dark:bg-[#665C3A] border border-[#FFD580] dark:border-[#665C3A]">
                    <span className="text-xs text-[#B38B00] dark:text-[#FFD580]">BACKEND | <b>BE-LEGACY</b></span>
                    <span className="text-sm font-medium text-[#B38B00] dark:text-[#FFD580]">{log}</span>
                  </li>
                );
              }
              const t = (log.time || '').toString();
              const hh = t.includes('T') ? t.split('T')[1].slice(0,8) : t.slice(11,19);
              const isLLM = !!(log && log.extra && (log.extra.llm === true));
              const boxBg = isLLM ? 'bg-[#E8F8EE] dark:bg-[#1F3A2E] border-[#7BD389] dark:border-[#2E7D50]' : 'bg-[#FFF7E6] dark:bg-[#665C3A] border-[#FFD580] dark:border-[#665C3A]';
              const titleColor = isLLM ? 'text-[#1E824C] dark:text-[#7BD389]' : 'text-[#B38B00] dark:text-[#FFD580]';
              const textColor = isLLM ? 'text-[#1E824C] dark:text-[#7BD389]' : 'text-[#B38B00] dark:text-[#FFD580]';
              const extraColor = isLLM ? 'text-[#1E824C]/80 dark:text-[#7BD389]/80' : 'text-[#B38B00]/80 dark:text-[#FFD580]/80';
              return (
                <li key={key} className={`flex flex-col gap-1 p-2 rounded-lg border ${boxBg}`}>
                  <span className={`text-xs ${titleColor}`}>{hh} | <b>{log.component}</b> | <b>{log.code}</b> | <b>{log.level}</b></span>
                  <span className={`text-sm font-medium ${textColor}`}>{log.message}</span>
                  {log.extra && (
                    <span className={`text-[11px] ${extraColor} break-all`}>{JSON.stringify(log.extra)}</span>
                  )}
                </li>
              );
            })}
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
  developerMode={developerMode}
  onToggleDeveloperMode={onToggleDeveloperMode}
  onDevHome={onDevHome}
  onDevTestSt1={onDevTestSt1}
  onDevTestSt2={onDevTestSt2}
  onDevTestSt3={onDevTestSt3}
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
          onUrlChange={(u) => setCurrentUrl(u)}
          style={{ minHeight: 520, height: 'calc(70vh + 80px)' }}
        />
        <div style={{ height: 38 }} />
        <CommandPanel
          commandLog={commandLog}
          fontStack={fontStack}
          darkMode={darkMode}
        />
        {developerMode && (
          <div className="mt-4 w-full max-w-3xl rounded-lg border border-[#B3C7E6] dark:border-[#335C81] bg-white/80 dark:bg-[#223A5E]/80 p-4">
            <div className="text-sm font-semibold text-[#0057A0] dark:text-[#E6F0FA] mb-3">TS3 Görsel Debug Ayarları</div>
            <div className="flex flex-wrap items-center gap-4 text-sm">
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={!!ts3Highlight} onChange={(e) => setTs3Highlight && setTs3Highlight(e.target.checked)} />
                <span className="text-[#003366] dark:text-[#E6F0FA]">Highlight</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={!!ts3Typing} onChange={(e) => setTs3Typing && setTs3Typing(e.target.checked)} />
                <span className="text-[#003366] dark:text-[#E6F0FA]">Simulate Typing</span>
              </label>
              <label className="flex items-center gap-2">
                <span className="text-[#003366] dark:text-[#E6F0FA]">Delay (ms)</span>
                <input
                  type="number"
                  min={0}
                  step={50}
                  value={ts3Delay}
                  onChange={(e) => setTs3Delay && setTs3Delay(Math.max(0, Number(e.target.value) || 0))}
                  className="w-24 rounded border border-[#B3C7E6] dark:border-[#335C81] bg-white/80 dark:bg-[#1a2233] px-2 py-1 text-[#003366] dark:text-[#E6F0FA]"
                />
              </label>
            </div>
          </div>
        )}
      </main>
  <Footer fontStack={fontStack} status={backendStatus} darkMode={darkMode} />
  {/* BackendLogPanel kaldırıldı, loglar birleşik panelde gösteriliyor */}
  </div>
  );
};
