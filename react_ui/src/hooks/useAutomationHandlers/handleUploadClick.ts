import { AutomationHandlersProps } from "./useAutomationHandlers";

export function handleUploadClickFactory({ fileInputRef }: Pick<AutomationHandlersProps, 'fileInputRef'>) {
  return () => {
    try {
      fileInputRef.current?.click();
      if (typeof window !== 'undefined') {
        if (!window.__DEV_LOGS) window.__DEV_LOGS = [];
        window.__DEV_LOGS.push({
          time: new Date().toISOString(),
          component: 'useAutomationHandlers.handleUploadClick',
          state: 'event',
          code: 'UAH-1401',
          message: 'handleUploadClick çağrıldı.'
        });
      }
    } catch (err: any) {
      if (typeof window !== 'undefined') {
        window.__DEV_LOGS.push({
          time: new Date().toISOString(),
          component: 'useAutomationHandlers.handleUploadClick',
          state: 'error',
          code: 'UAH-9401',
          message: `handleUploadClick: Beklenmeyen hata: ${err?.message || err}`
        });
      }
    }
  };
}
