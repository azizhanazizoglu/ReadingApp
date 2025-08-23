import { useAutomation } from "@/hooks/useAutomation";
import { ThemeToggle } from "@/components/ThemeToggle";
import { AllianzLogo } from "@/components/AllianzLogo";
import { Button } from "@/components/ui/button";
import { useState, useEffect } from "react";
import { toast } from "sonner";
import { SearchBar } from "@/components/SearchBar";
import { BrowserView } from "@/components/BrowserView";
import { CommandPanel } from "@/components/CommandPanel";
import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";

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

  // Kullanıcı adresi yazıp "Git"e tıklayınca iframe'de göster
  const handleGo = (address: string) => {
    let url = address.trim();
    if (!url) return;
    if (!/^https?:\/\//i.test(url)) {
      url = "https://" + url;
    }
    setIframeUrl(url);
    setStatus(statusMessages[1]);
    setLoading(true);
    setResult(null);
    setCommandLog(logs => [
      { icon: "🟡", message: `Site açılıyor: ${url}`, color: "text-yellow-600 dark:text-yellow-300" },
      ...logs,
    ]);
  };

  // Iframe yüklendiğinde
  const handleIframeLoad = () => {
    setStatus(statusMessages[2]);
    setLoading(false);
    setCommandLog(logs => [
      { icon: "🟢", message: "Web sitesi başarıyla yüklendi.", color: "text-green-600 dark:text-green-300" },
      ...logs,
    ]);
  };

  // Otomasyon başlat
  const handleAutomation = async () => {
    if (!iframeUrl) return;
    // JPEG yüklenmeden otomasyon başlatılırsa hata ver
    if (!result || result === statusMessages[0] || result === statusMessages[1]) {
      setCommandLog(logs => [
        { icon: "🔴", message: "Hata: Ruhsat fotoğrafı yüklenmedi!", color: "text-red-600 dark:text-red-400" },
        ...logs,
      ]);
      setStatus("Hata: Ruhsat fotoğrafı yüklenmedi!");
      toast.error("Ruhsat fotoğrafı yüklenmedi!");
      return;
    }
    setAutomation(true);
    setStatus(statusMessages[3]);
    setResult(null);
    setCommandLog(logs => [
      { icon: "🟡", message: "Otomasyon başlatıldı.", color: "text-yellow-600 dark:text-yellow-300" },
      ...logs,
    ]);
    try {
      const resp = await fetch(`${BACKEND_URL}/api/automation`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: iframeUrl }),
      });
      if (!resp.ok) throw new Error("Otomasyon başlatılamadı.");
      const data = await resp.json();
      setResult(data.result || "Otomasyon tamamlandı.");
      setStatus(statusMessages[6]);
      setCommandLog(logs => [
        { icon: "🟢", message: "Otomasyon tamamlandı.", color: "text-green-600 dark:text-green-300" },
        ...logs,
      ]);
      toast.success("Otomasyon tamamlandı!");
    } catch (e) {
      setStatus(statusMessages[7]);
      setCommandLog(logs => [
        { icon: "🔴", message: "Otomasyon sırasında hata oluştu.", color: "text-red-600 dark:text-red-400" },
        ...logs,
      ]);
      toast.error("Otomasyon sırasında hata oluştu.");
    }
    setAutomation(false);
  };

  // JPG yükle
  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setStatus(statusMessages[4]);
    setResult(null);
    setCommandLog(logs => [
      { icon: "🟡", message: "JPEG yükleniyor...", color: "text-yellow-600 dark:text-yellow-300" },
      ...logs,
    ]);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const resp = await fetch(`${BACKEND_URL}/api/upload`, {
        method: "POST",
        body: formData,
      });
      if (!resp.ok) throw new Error("Yükleme başarısız.");
      const data = await resp.json();
      setResult(data.result || "JPG başarıyla yüklendi.");
      setStatus(statusMessages[5]);
      setCommandLog(logs => [
        { icon: "🟢", message: "JPEG başarıyla yüklendi.", color: "text-green-600 dark:text-green-300" },
        ...logs,
      ]);
      toast.success("JPG başarıyla yüklendi!");
    } catch (e) {
      setStatus(statusMessages[7]);
      setCommandLog(logs => [
        { icon: "🔴", message: "JPEG yüklenirken hata oluştu.", color: "text-red-600 dark:text-red-400" },
        ...logs,
      ]);
      toast.error("JPG yüklenirken hata oluştu.");
    }
    setUploading(false);
    // input'u sıfırla
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

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
      {/* Top Bar */}
      <Header
        appName={APP_NAME}
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

      {/* Main Area */}
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

  {/* Status/Info Area */}
  <Footer fontStack={fontStack} status={status} darkMode={darkMode} />
  {/* Sayfa sonu boşluğu kaldırıldı, footer her zaman görünür */}
    </div>
  );
};

export default Index;

/*
*/