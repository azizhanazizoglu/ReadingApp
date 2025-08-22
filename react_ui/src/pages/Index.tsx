import { ThemeToggle } from "@/components/ThemeToggle";
import { AllianzLogo } from "@/components/AllianzLogo";
import { Button } from "@/components/ui/button";
import { Search, Zap, UploadCloud } from "lucide-react";
import { useState, useEffect, useRef } from "react";
import { toast } from "sonner";

const APP_NAME = "Zirve Sigorta";
const BACKEND_URL = "http://localhost:5000"; // Python backend adresi

const statusMessages = [
  "Bir web sitesi adresi girin ve 'Git' ile görüntüleyin.",
  "Yükleniyor...",
  "Web sitesi başarıyla yüklendi.",
  "Otomasyon başlatıldı.",
  "JPG yükleniyor...",
  "JPG başarıyla yüklendi.",
  "Otomasyon sonucu alındı.",
  "Bir hata oluştu.",
];

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
  const [iframeUrl, setIframeUrl] = useState("");
  const [status, setStatus] = useState(statusMessages[0]);
  const [loading, setLoading] = useState(false);
  const [automation, setAutomation] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const darkMode = useDarkMode();

  // Kullanıcı adresi yazıp "Git"e tıklayınca iframe'de göster
  const handleGo = () => {
    let url = address.trim();
    if (!url) return;
    if (!/^https?:\/\//i.test(url)) {
      url = "https://" + url;
    }
    setIframeUrl(url);
    setStatus(statusMessages[1]);
    setLoading(true);
    setResult(null);
  };

  // Iframe yüklendiğinde
  const handleIframeLoad = () => {
    setStatus(statusMessages[2]);
    setLoading(false);
  };

  // Otomasyon başlat
  const handleAutomation = async () => {
    if (!iframeUrl) return;
    setAutomation(true);
    setStatus(statusMessages[3]);
    setResult(null);
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
      toast.success("Otomasyon tamamlandı!");
    } catch (e) {
      setStatus(statusMessages[7]);
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
      toast.success("JPG başarıyla yüklendi!");
    } catch (e) {
      setStatus(statusMessages[7]);
      toast.error("JPG yüklenirken hata oluştu.");
    }
    setUploading(false);
    // input'u sıfırla
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-between bg-gradient-to-br from-[#f8fafc] to-[#e6f0fa] dark:from-[#1a2233] dark:to-[#223a5e] transition-colors"
      style={{
        fontFamily: fontStack,
        minHeight: "800px",
        minWidth: "100vw",
      }}
    >
      {/* Top Bar */}
      <header
        className="w-full flex items-center justify-between px-10 py-4 bg-white/80 dark:bg-[#223A5E]/90 shadow-md rounded-b-3xl transition-colors border-b border-[#e6f0fa] dark:border-[#335C81]"
        style={{
          fontFamily: fontStack,
          height: 80,
          maxWidth: 1400,
          margin: "0 auto",
        }}
      >
        {/* Logo & App Name */}
        <div className="flex items-center gap-3 min-w-[220px]">
          <AllianzLogo className="h-9 w-9" darkMode={darkMode} />
          <span className="text-xl font-semibold tracking-tight text-[#003366] dark:text-[#E6F0FA] select-none">
            {APP_NAME}
          </span>
        </div>
        {/* Search Bar + Buttons */}
        <div className="flex items-center gap-2 flex-1 justify-center">
          <div className="relative flex items-center">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#7B8FA1] dark:text-[#B3C7E6]" size={16} />
            <input
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Site adresi (örn: www.allianz.com.tr)"
              className="pl-8 pr-2 py-1 w-[180px] rounded-lg bg-[#f8fafc] dark:bg-[#335C81] text-sm shadow focus:ring-2 focus:ring-[#0057A0] dark:focus:ring-[#E6F0FA] focus:outline-none transition-all border border-[#B3C7E6] dark:border-[#335C81] placeholder:text-[#7B8FA1] dark:placeholder:text-[#B3C7E6]"
              style={{ fontFamily: fontStack, color: "#003366" }}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleGo();
              }}
              autoFocus
              disabled={loading}
            />
          </div>
          <Button
            className="px-4 py-1 text-sm rounded-lg bg-[#0057A0] hover:bg-[#003366] active:bg-[#002244] text-white font-semibold shadow transition-all"
            style={{
              fontFamily: fontStack,
              minWidth: 48,
              boxShadow: "0 2px 12px 0 rgba(0,87,160,0.10)",
            }}
            onClick={handleGo}
            disabled={loading || !address.trim()}
            tabIndex={0}
          >
            Git
          </Button>
          <Button
            className="px-3 py-1 text-sm rounded-lg bg-[#E6F0FA] hover:bg-[#B3C7E6] active:bg-[#B3C7E6] text-[#0057A0] dark:bg-[#335C81] dark:hover:bg-[#223A5E] dark:text-[#E6F0FA] font-semibold shadow transition-all flex items-center"
            style={{
              fontFamily: fontStack,
              minWidth: 40,
              boxShadow: "0 2px 12px 0 rgba(0,87,160,0.10)",
            }}
            onClick={handleAutomation}
            disabled={automation || !iframeUrl}
            tabIndex={0}
            aria-label="Otomasyonu Başlat"
          >
            <Zap className={`w-5 h-5 ${automation ? "animate-pulse" : ""}`} />
          </Button>
          <Button
            className="px-3 py-1 text-sm rounded-lg bg-[#E6F0FA] hover:bg-[#B3C7E6] active:bg-[#B3C7E6] text-[#0057A0] dark:bg-[#335C81] dark:hover:bg-[#223A5E] dark:text-[#E6F0FA] font-semibold shadow transition-all flex items-center"
            style={{
              fontFamily: fontStack,
              minWidth: 40,
              boxShadow: "0 2px 12px 0 rgba(0,87,160,0.10)",
            }}
            onClick={handleUploadClick}
            disabled={uploading}
            tabIndex={0}
            aria-label="JPG Yükle"
          >
            <UploadCloud className={`w-5 h-5 ${uploading ? "animate-pulse" : ""}`} />
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg"
              className="hidden"
              onChange={handleFileChange}
              disabled={uploading}
            />
          </Button>
        </div>
        {/* Theme Toggle */}
        <div className="flex items-center min-w-[48px] justify-end">
          <ThemeToggle />
        </div>
      </header>

      {/* Main Area */}
      <main
        className="flex flex-col items-center w-full flex-1 px-8"
        style={{ maxWidth: 1400, width: "100%" }}
      >
        {/* Browser View */}
        <div
          className="flex-1 w-full max-w-6xl bg-[#e6f0fa] dark:bg-[#223A5E] rounded-3xl shadow-2xl border border-[#B3C7E6] dark:border-[#335C81] flex items-center justify-center transition-colors overflow-hidden"
          style={{
            minHeight: 540,
            marginBottom: 32,
            marginTop: 48,
            position: "relative",
          }}
        >
          {iframeUrl ? (
            <iframe
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
        </div>
        {/* Sonuç veya bilgi mesajı */}
        {result && (
          <div className="w-full max-w-3xl mb-8 p-4 rounded-xl bg-white/80 dark:bg-[#335C81]/80 shadow text-[#003366] dark:text-[#E6F0FA] text-center text-base break-words">
            {result}
          </div>
        )}
      </main>

      {/* Status/Info Area */}
      <footer
        className="w-full px-8 py-4 bg-white/90 dark:bg-[#223A5E]/90 rounded-t-2xl shadow-sm flex items-center justify-center transition-colors"
        style={{
          fontFamily: fontStack,
          maxWidth: 1400,
          margin: "0 auto",
          borderTop: `2px solid #0057A0`,
        }}
      >
        <span className="text-[#7B8FA1] dark:text-[#E6F0FA] text-base">{status}</span>
      </footer>
    </div>
  );
};

export default Index;

/*
- Allianz logosu gece/gündüz moduna göre renk değiştirir.
- Arama çubuğu ve butonlar üst menüde, ortada ve kompakt.
- Otomasyon ve JPG yükleme butonları, backend'e REST API çağrısı yapar.
- Sonuçlar ve durumlar arayüzde gösterilir.
- Modern, Apple tarzı ve ferah tasarım.
*/