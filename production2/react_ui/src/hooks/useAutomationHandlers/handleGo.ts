import { AutomationHandlersProps } from "./useAutomationHandlers";

export function handleGoFactory({
  setIframeUrl,
  setStatus,
  setLoading,
  setResult,
  setCommandLog,
  statusMessages,
}: Pick<AutomationHandlersProps, 'setIframeUrl' | 'setStatus' | 'setLoading' | 'setResult' | 'setCommandLog' | 'statusMessages'>) {
  return (address: string) => {
    if (typeof window !== 'undefined') {
      if (!window.__DEV_LOGS) window.__DEV_LOGS = [];
      window.__DEV_LOGS.push({
        time: new Date().toISOString(),
        component: 'useAutomationHandlers.handleGo',
        state: 'event',
        code: 'UAH-1101',
        message: `handleGo çağrıldı: ${address}`
      });
    }
    try {
      let url = address.trim();
      if (!url) {
        if (typeof window !== 'undefined') {
          window.__DEV_LOGS.push({
            time: new Date().toISOString(),
            component: 'useAutomationHandlers.handleGo',
            state: 'error',
            code: 'UAH-9101',
            message: 'handleGo: Adres boş veya geçersiz.'
          });
        }
        return;
      }
      if (!/^https?:\/\//i.test(url)) {
        url = "https://" + url;
      }
      // Aynı URL ise reload için önce boş string ata, sonra tekrar url ata
      if ((window as any)?.currentIframeUrl === url) {
        if (typeof window !== 'undefined') {
          window.__DEV_LOGS.push({
            time: new Date().toISOString(),
            component: 'useAutomationHandlers.handleGo',
            state: 'debug',
            code: 'UAH-1110',
            message: `handleGo: Aynı URL tekrar girildi, iframe reload için boş string atanıyor.`
          });
        }
        setLoading(true);
        setIframeUrl("");
        (window as any).currentIframeUrl = "";
        setTimeout(() => {
          setLoading(true);
          setIframeUrl(url);
          (window as any).currentIframeUrl = url;
          if (typeof window !== 'undefined') {
            window.__DEV_LOGS.push({
              time: new Date().toISOString(),
              component: 'useAutomationHandlers.handleGo',
              state: 'debug',
              code: 'UAH-1111',
              message: `handleGo: Aynı URL tekrar atanarak iframe reload tetiklendi: '${url}'`
            });
          }
          // Timeout health check: BrowserView loading log gelmezse uyarı logu at
          setTimeout(() => {
            const found = window.__DEV_LOGS && window.__DEV_LOGS.slice(-10).some((l: any) => l.code === 'BV-1001');
            if (!found) {
              window.__DEV_LOGS.push({
                time: new Date().toISOString(),
                component: 'BrowserView',
                state: 'timeout',
                code: 'BV-9002',
                message: 'BrowserView loading state beklenen sürede gelmedi. Son action: handleGo'
              });
            }
          }, 2000);
        }, 100);
      } else {
        setLoading(true);
        setIframeUrl(url);
        (window as any).currentIframeUrl = url;
        if (typeof window !== 'undefined') {
          window.__DEV_LOGS.push({
            time: new Date().toISOString(),
            component: 'useAutomationHandlers.handleGo',
            state: 'debug',
            code: 'UAH-1112',
            message: `handleGo: setIframeUrl çağrıldı: '${url}'`
          });
          // Timeout health check: BrowserView loading log gelmezse uyarı logu at
          setTimeout(() => {
            const found = window.__DEV_LOGS && window.__DEV_LOGS.slice(-10).some((l: any) => l.code === 'BV-1001');
            if (!found) {
              window.__DEV_LOGS.push({
                time: new Date().toISOString(),
                component: 'BrowserView',
                state: 'timeout',
                code: 'BV-9002',
                message: 'BrowserView loading state beklenen sürede gelmedi. Son action: handleGo'
              });
            }
          }, 2000);
        }
      }
      setStatus(statusMessages[1]);
      setLoading(true);
      setResult(null);
      setCommandLog((logs: any) => [
        { icon: "🟡", message: `Site açılıyor: ${url}`, color: "text-yellow-600 dark:text-yellow-300" },
        ...logs,
      ]);
    } catch (err: any) {
      if (typeof window !== 'undefined') {
        window.__DEV_LOGS.push({
          time: new Date().toISOString(),
          component: 'useAutomationHandlers.handleGo',
          state: 'error',
          code: 'UAH-9102',
          message: `handleGo: Beklenmeyen hata: ${err?.message || err}`
        });
      }
    }
  };
}
