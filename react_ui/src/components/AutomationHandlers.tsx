import { toast } from "sonner";

export interface AutomationHandlersProps {
  iframeUrl: string;
  setIframeUrl: (v: string) => void;
  setStatus: (v: string) => void;
  setLoading: (v: boolean) => void;
  setResult: (v: any) => void;
  setCommandLog: (fn: any) => void;
  setAutomation: (v: boolean) => void;
  result: any;
  statusMessages: string[];
  fileInputRef: React.RefObject<HTMLInputElement>;
  setUploading: (v: boolean) => void;
  BACKEND_URL: string;
}

export function useAutomationHandlers({
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
}: AutomationHandlersProps) {
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
    setCommandLog((logs: any) => [
      { icon: "🟡", message: `Site açılıyor: ${url}`, color: "text-yellow-600 dark:text-yellow-300" },
      ...logs,
    ]);
  };

  // Iframe yüklendiğinde
  const handleIframeLoad = () => {
    setStatus(statusMessages[2]);
    setLoading(false);
    setCommandLog((logs: any) => [
      { icon: "🟢", message: "Web sitesi başarıyla yüklendi.", color: "text-green-600 dark:text-green-300" },
      ...logs,
    ]);
  };

  // Otomasyon başlat
  const handleAutomation = async () => {
    if (!iframeUrl) return;
    if (!result || result === statusMessages[0] || result === statusMessages[1]) {
      setCommandLog((logs: any) => [
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
    setCommandLog((logs: any) => [
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
      setCommandLog((logs: any) => [
        { icon: "🟢", message: "Otomasyon tamamlandı.", color: "text-green-600 dark:text-green-300" },
        ...logs,
      ]);
      toast.success("Otomasyon tamamlandı!");
    } catch (e) {
      setStatus(statusMessages[7]);
      setCommandLog((logs: any) => [
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
    setCommandLog((logs: any) => [
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
      setCommandLog((logs: any) => [
        { icon: "🟢", message: "JPEG başarıyla yüklendi.", color: "text-green-600 dark:text-green-300" },
        ...logs,
      ]);
      toast.success("JPG başarıyla yüklendi!");
    } catch (e) {
      setStatus(statusMessages[7]);
      setCommandLog((logs: any) => [
        { icon: "🔴", message: "JPEG yüklenirken hata oluştu.", color: "text-red-600 dark:text-red-400" },
        ...logs,
      ]);
      toast.error("JPG yüklenirken hata oluştu.");
    }
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return {
    handleGo,
    handleIframeLoad,
    handleAutomation,
    handleUploadClick,
    handleFileChange,
  };
}
