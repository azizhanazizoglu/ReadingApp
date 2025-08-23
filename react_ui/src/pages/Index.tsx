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
  const [commandLog, setCommandLog] = useState<{icon: string, message: string, color: string}[]>([]);
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
          <div className="relative flex items-center w-full max-w-2xl mx-auto">
            <input
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              className="pl-0 pr-4 py-3 w-full rounded-full bg-[#f5faff] dark:bg-[#223A5E] text-lg shadow focus:ring-2 focus:ring-[#0057A0] dark:focus:ring-[#E6F0FA] focus:outline-none transition-all border border-[#B3C7E6] dark:border-[#335C81] text-[#003366] dark:text-[#E6F0FA] font-semibold text-center"
              style={{ fontFamily: fontStack, minWidth: 320, maxWidth: '100%' }}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleGo();
              }}
              autoFocus
              disabled={loading}
            />
            <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-[#7B8FA1] dark:text-[#B3C7E6] pointer-events-none">
              <Search size={28} strokeWidth={2.5} />
            </span>
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
        {/* Browser View */}
        <div
          className="w-full max-w-6xl rounded-3xl shadow-2xl border border-[#B3C7E6] dark:border-[#335C81] flex items-center justify-center transition-colors overflow-hidden"
          style={{
            minHeight: 340,
            maxHeight: 700,
            height: '40vh',
            marginBottom: 32,
            marginTop: 48,
            position: "relative",
            background: darkMode ? undefined : "rgba(245,250,255,0.97)",
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
          <div className="w-full max-w-6xl mb-4 p-4 rounded-xl bg-white/80 dark:bg-[#335C81]/80 shadow text-[#003366] dark:text-[#E6F0FA] text-center text-base break-words">
            {result}
          </div>
        )}

        {/* Command Output Panel */}
        <div
          className="w-full max-w-6xl mb-16 px-6 py-3 rounded-xl shadow border border-[#B3C7E6] dark:border-[#335C81] transition-colors flex items-center justify-center"
          style={{
            fontFamily: fontStack,
            minHeight: 48,
            maxHeight: 48,
            background: darkMode ? undefined : "rgba(245,250,255,0.97)",
            color: darkMode ? undefined : "#0057A0",
            boxShadow: darkMode ? undefined : "0 4px 24px 0 rgba(0,87,160,0.08)",
            borderTop: darkMode ? undefined : "2px solid #B3C7E6",
            overflow: 'hidden',
          }}
        >
          {commandLog.length === 0 ? (
            <span className="text-[#7B8FA1] dark:text-[#B3C7E6] text-base font-medium" style={{fontFamily: fontStack}}>
              Komut çıktısı burada görünecek.
            </span>
          ) : (
            <div className="flex items-center gap-3 w-full justify-center animate-fade-in">
              <span style={{ fontSize: 22, animation: commandLog[0].icon === '🟢' ? 'pop 0.5s' : commandLog[0].icon === '🔴' ? 'shake 0.5s' : 'none' }}>{commandLog[0].icon}</span>
              <span
                className="text-base font-semibold truncate"
                style={{
                  color: darkMode ? '#B3C7E6' : '#0057A0',
                  fontFamily: fontStack,
                  letterSpacing: 0.1,
                  maxWidth: 420,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {commandLog[0].message}
              </span>
            </div>
          )}
          <style>{`
            @keyframes pop { 0% { transform: scale(1); } 50% { transform: scale(1.25); } 100% { transform: scale(1); } }
            @keyframes shake { 0% { transform: translateX(0); } 20% { transform: translateX(-4px); } 40% { transform: translateX(4px); } 60% { transform: translateX(-2px); } 80% { transform: translateX(2px); } 100% { transform: translateX(0); } }
            .animate-fade-in { animation: fadeIn 0.5s; }
            @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
          `}</style>
        </div>
      </main>

      {/* Status/Info Area */}
      <footer
        className="w-full px-8 py-4 bg-white/95 dark:bg-[#223A5E]/95 rounded-t-2xl shadow-sm flex items-center justify-between transition-colors border-t-2 border-[#0057A0] dark:border-[#335C81]"
        style={{
          fontFamily: fontStack,
          maxWidth: 1400,
          margin: "0 auto",
          minHeight: 60,
          flexShrink: 0,
        }}
      >
        <span className="text-xl font-semibold tracking-tight text-[#003366] dark:text-[#E6F0FA] select-none">
          Zirve Sigorta
        </span>
        <span className="text-[#7B8FA1] dark:text-[#E6F0FA] text-base">{status}</span>
        <span className="text-[#0057A0] dark:text-[#B3C7E6] text-base font-medium select-none">
          Acil Destek: <a href="mailto:azizhanazizoglu@gmail.com" className="underline hover:text-[#003366] dark:hover:text-white">azizhanazizoglu@gmail.com</a>
        </span>
      </footer>
  {/* Sayfa sonu boşluğu kaldırıldı, footer her zaman görünür */}
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