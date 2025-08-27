import { useAutomation } from "@/hooks/useAutomation";
import { ThemeToggle } from "@/components/ThemeToggle";
import { AllianzLogo } from "@/components/AllianzLogo";
import { Button } from "@/components/ui/button";
import { useState, useEffect } from "react";
import { useAutomationHandlers } from "@/hooks/useAutomationHandlers";
import { runTs2 } from "@/services/ts2Service";
import { runTs3 } from "@/services/ts3Service";
import { SearchBar } from "@/components/SearchBar";
import { MainLayout } from "@/components/MainLayout";
// Developer panel artık Header içinde toggle ile gösteriliyor

// Varsayılan backend adresi (gerekirse .env ile değiştirilebilir)
const BACKEND_URL = "http://localhost:5001";
// Tüm status mesajları (Türkçe)
const statusMessages = [
  "Hazır",
  "Web sitesi yükleniyor...",
  "Web sitesi başarıyla yüklendi.",
  "Otomasyon başlatıldı...",
  "JPEG yükleniyor...",
  "JPEG başarıyla yüklendi.",
  "Otomasyon tamamlandı.",
  "Hata oluştu."
];
// Uygulama adı
const APP_NAME = "Zirve Sigorta";

const fontStack =
  "SF Pro Display, SF Pro Icons, Helvetica Neue, Helvetica, Arial, sans-serif";

function useDarkMode() {
  const [dark, setDark] = useState(false);
  useEffect(() => {
    const match = window.matchMedia("(prefers-color-scheme: dark)");
    setDark(match.matches || document.documentElement.classList.contains("dark"));
    const listener = (e: MediaQueryListEvent) => setDark(e.matches);
    match.addEventListener("change", listener);
    return () => match.removeEventListener("change", listener);
  }, []);
  return dark;
}

const Index = () => {
  const [address, setAddress] = useState("");
  const [developerMode, setDeveloperMode] = useState(false);
  // TS3 options for debugging UX
  const [ts3Highlight, setTs3Highlight] = useState(true);
  const [ts3Typing, setTs3Typing] = useState(true);
  const [ts3Delay, setTs3Delay] = useState(200);
  const darkMode = useDarkMode();
  const { 
    iframeUrl, 
    setIframeUrl, 
    status, 
    setStatus, 
    loading, 
    setLoading, 
    automation, 
    setAutomation, 
    result, 
    setResult, 
    uploading, 
    setUploading, 
    commandLog, 
    setCommandLog, 
    fileInputRef 
  } = useAutomation({ backendUrl: BACKEND_URL, statusMessages });


  // Tüm handler fonksiyonlarını custom hook'tan al
  const {
    handleGo,
    handleIframeLoad,
    handleAutomation,
    handleUploadClick,
    handleFileChange,
  } = useAutomationHandlers({
    iframeUrl,
    setIframeUrl,
    setStatus,
    setLoading,
    setResult,
    setCommandLog,
    setAutomation,
    result,
    statusMessages,
    fileInputRef,
    setUploading,
    BACKEND_URL,
  });

  // Developer buton handlerları
  const handleHome = () => {
    setAddress("https://preview--screen-to-data.lovable.app/traffic-insurance");
  };
  const handleTestSt1 = () => handleAutomation();
  const handleTestSt2 = async () => {
    const dev = (c: string, m: string) => {
      if (typeof window !== 'undefined') {
        (window as any).__DEV_LOGS = (window as any).__DEV_LOGS || [];
        (window as any).__DEV_LOGS.push({ time: new Date().toISOString(), component: 'Index', state: 'debug', code: c, message: m });
      }
    };
    try { await runTs2(BACKEND_URL, iframeUrl || address, dev); }
    catch (e: any) {
      if (typeof window !== 'undefined') {
        (window as any).__DEV_LOGS = (window as any).__DEV_LOGS || [];
        (window as any).__DEV_LOGS.push({ time: new Date().toISOString(), component: 'Index', state: 'error', code: 'IDX-TS2-500', message: String(e) });
      }
    }
  };

  const handleTestSt3 = async () => {
    const dev = (c: string, m: string) => {
      if (typeof window !== 'undefined') {
        (window as any).__DEV_LOGS = (window as any).__DEV_LOGS || [];
        (window as any).__DEV_LOGS.push({ time: new Date().toISOString(), component: 'Index', state: 'event', code: c, message: m });
      }
    };
  // Kullanıcı ayarlarını uygula
  try { await runTs3(BACKEND_URL, dev, { highlight: ts3Highlight, stepDelayMs: ts3Delay, simulateTyping: ts3Typing }); }
    catch (e: any) { dev('IDX-TS3-ERR', String(e)); }
  };

  return (
    <>
      <MainLayout
        appName={APP_NAME}
        darkMode={darkMode}
        fontStack={fontStack}
        address={address}
        setAddress={setAddress}
        handleGo={handleGo}
        loading={loading}
        automation={automation}
        handleAutomation={handleAutomation}
        iframeUrl={iframeUrl}
        uploading={uploading}
        handleUploadClick={handleUploadClick}
        fileInputRef={fileInputRef}
        handleFileChange={handleFileChange}
        result={result}
        handleIframeLoad={handleIframeLoad}
        commandLog={commandLog}
        status={status}
  developerMode={developerMode}
  onToggleDeveloperMode={() => setDeveloperMode((v) => !v)}
  onDevHome={handleHome}
  onDevTestSt1={handleTestSt1}
  onDevTestSt2={handleTestSt2}
  onDevTestSt3={handleTestSt3}
  ts3Highlight={ts3Highlight}
  ts3Typing={ts3Typing}
  ts3Delay={ts3Delay}
  setTs3Highlight={setTs3Highlight}
  setTs3Typing={setTs3Typing}
  setTs3Delay={setTs3Delay}
      />
    </>
  );
};

export default Index;

/*
*/