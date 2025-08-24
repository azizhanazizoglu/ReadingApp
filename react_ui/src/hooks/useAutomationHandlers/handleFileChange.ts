import { toast } from "sonner";
import { AutomationHandlersProps } from "./useAutomationHandlers";

export function handleFileChangeFactory({
  setUploading,
  setStatus,
  setResult,
  setCommandLog,
  statusMessages,
  BACKEND_URL,
  fileInputRef,
}: Pick<AutomationHandlersProps, 'setUploading' | 'setStatus' | 'setResult' | 'setCommandLog' | 'statusMessages' | 'BACKEND_URL' | 'fileInputRef'>) {
  return async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) {
      if (typeof window !== 'undefined') {
        window.__DEV_LOGS.push({
          time: new Date().toISOString(),
          component: 'useAutomationHandlers.handleFileChange',
          state: 'error',
          code: 'UAH-9501',
          message: 'handleFileChange: Dosya seçilmedi.'
        });
      }
      return;
    }
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
      if (!resp.ok) {
        if (typeof window !== 'undefined') {
          window.__DEV_LOGS.push({
            time: new Date().toISOString(),
            component: 'useAutomationHandlers.handleFileChange',
            state: 'error',
            code: 'UAH-9502',
            message: 'JPEG yükleme başarısız (backend response not ok).'
          });
        }
        throw new Error("Yükleme başarısız.");
      }
      const data = await resp.json();
      setResult(data.result || "JPG başarıyla yüklendi.");
      setStatus(statusMessages[5]);
      setCommandLog((logs: any) => [
        { icon: "🟢", message: "JPEG başarıyla yüklendi.", color: "text-green-600 dark:text-green-300" },
        ...logs,
      ]);
      toast.success("JPG başarıyla yüklendi!");
    } catch (e) {
      if (typeof window !== 'undefined') {
        window.__DEV_LOGS.push({
          time: new Date().toISOString(),
          component: 'useAutomationHandlers.handleFileChange',
          state: 'error',
          code: 'UAH-9503',
          message: `JPEG yüklenirken hata: ${e?.message || e}`
        });
      }
      setStatus(statusMessages[7]);
      setCommandLog((logs: any) => [
        { icon: "🔴", message: "JPEG yüklenirken hata oluştu.", color: "text-red-600 dark:text-red-400" },
        ...logs,
      ]);
      toast.error("JPEG yüklenirken hata oluştu.");
    }
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };
}
