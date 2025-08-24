import { AutomationHandlersProps } from "./useAutomationHandlers";

export function handleIframeLoadFactory({
  setStatus,
  setLoading,
  setCommandLog,
  statusMessages,
}: Pick<AutomationHandlersProps, 'setStatus' | 'setLoading' | 'setCommandLog' | 'statusMessages'>) {
  return () => {
    if (typeof window !== 'undefined') {
      if (!window.__DEV_LOGS) window.__DEV_LOGS = [];
      window.__DEV_LOGS.push({
        time: new Date().toISOString(),
        component: 'useAutomationHandlers.handleIframeLoad',
        state: 'event',
        code: 'UAH-1201',
        message: 'handleIframeLoad çağrıldı.'
      });
    }
    try {
      setStatus(statusMessages[2]);
      setLoading(false);
      setCommandLog((logs: any) => [
        { icon: "🟢", message: "Web sitesi başarıyla yüklendi.", color: "text-green-600 dark:text-green-300" },
        ...logs,
      ]);
    } catch (err: any) {
      if (typeof window !== 'undefined') {
        window.__DEV_LOGS.push({
          time: new Date().toISOString(),
          component: 'useAutomationHandlers.handleIframeLoad',
          state: 'error',
          code: 'UAH-9201',
          message: `handleIframeLoad: Beklenmeyen hata: ${err?.message || err}`
        });
      }
    }
  };
}
