import { AutomationHandlersProps } from "./useAutomationHandlers";

export function handleAutomationFactory({
  iframeUrl,
  setAutomation,
  setStatus,
  setResult,
  setCommandLog,
  result,
  statusMessages,
  BACKEND_URL,
}: Pick<AutomationHandlersProps, 'iframeUrl' | 'setAutomation' | 'setStatus' | 'setResult' | 'setCommandLog' | 'result' | 'statusMessages' | 'BACKEND_URL'>) {
  return async () => {
    if (typeof window !== 'undefined') {
      if (!window.__DEV_LOGS) window.__DEV_LOGS = [];
      window.__DEV_LOGS.push({
        time: new Date().toISOString(),
        component: 'useAutomationHandlers.handleAutomation',
        state: 'event',
        code: 'UAH-1301',
        message: 'handleAutomation çağrıldı.'
      });
    }
    if (!iframeUrl) {
      if (typeof window !== 'undefined') {
        window.__DEV_LOGS.push({
          time: new Date().toISOString(),
          component: 'useAutomationHandlers.handleAutomation',
          state: 'error',
          code: 'UAH-9301',
          message: 'handleAutomation: iframeUrl boş.'
        });
      }
      return;
    }
    if (!result || result === statusMessages[0] || result === statusMessages[1]) {
      setCommandLog((logs: any) => [
        { icon: "🔴", message: "Hata: Ruhsat fotoğrafı yüklenmedi!", color: "text-red-600 dark:text-red-400" },
        ...logs,
      ]);
  setStatus("Hata: Ruhsat fotoğrafı yüklenmedi!");
      if (typeof window !== 'undefined') {
        window.__DEV_LOGS.push({
          time: new Date().toISOString(),
          component: 'useAutomationHandlers.handleAutomation',
          state: 'error',
          code: 'UAH-9302',
          message: 'handleAutomation: Ruhsat fotoğrafı yüklenmedi!'
        });
      }
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
      if (!resp.ok) {
        if (typeof window !== 'undefined') {
          window.__DEV_LOGS.push({
            time: new Date().toISOString(),
            component: 'useAutomationHandlers.handleAutomation',
            state: 'error',
            code: 'UAH-9303',
            message: 'Otomasyon başlatılamadı (backend response not ok).'
          });
        }
        throw new Error("Otomasyon başlatılamadı.");
      }
      const data = await resp.json();
      setResult(data.result || "Otomasyon tamamlandı.");
      setStatus(statusMessages[6]);
      setCommandLog((logs: any) => [
        { icon: "🟢", message: "Otomasyon tamamlandı.", color: "text-green-600 dark:text-green-300" },
        ...logs,
      ]);
  // toaster removed
    } catch (e) {
      if (typeof window !== 'undefined') {
        window.__DEV_LOGS.push({
          time: new Date().toISOString(),
          component: 'useAutomationHandlers.handleAutomation',
          state: 'error',
          code: 'UAH-9304',
          message: `Otomasyon sırasında hata: ${e?.message || e}`
        });
      }
      setStatus(statusMessages[7]);
      setCommandLog((logs: any) => [
        { icon: "🔴", message: "Otomasyon sırasında hata oluştu.", color: "text-red-600 dark:text-red-400" },
        ...logs,
      ]);
  // toaster removed
    }
    setAutomation(false);
  };
}
