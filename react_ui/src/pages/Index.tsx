import { useAutomation } from "@/hooks/useAutomation";
import { ThemeToggle } from "@/components/ThemeToggle";
import { AllianzLogo } from "@/components/AllianzLogo";
import { Button } from "@/components/ui/button";
import { useState, useEffect } from "react";
import { useAutomationHandlers } from "@/hooks/useAutomationHandlers";
import { SearchBar } from "@/components/SearchBar";
import { MainLayout } from "@/components/MainLayout";

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

  return (
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
    />
  );
};

export default Index;

/*
*/