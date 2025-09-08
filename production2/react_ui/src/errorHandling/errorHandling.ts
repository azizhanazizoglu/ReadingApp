import React from "react";

export function useLoadingTimeout({ loading, setTimeoutActive, timeoutMs = 10000 }: {
  loading: boolean;
  setTimeoutActive: (v: boolean) => void;
  timeoutMs?: number;
}) {
  React.useEffect(() => {
    let timer: any;
    if (loading) {
      timer = setTimeout(() => {
        setTimeoutActive(true);
        if (typeof window !== 'undefined') {
          if (!window.__DEV_LOGS) window.__DEV_LOGS = [];
          window.__DEV_LOGS.push({
            time: new Date().toISOString(),
            component: 'BrowserView',
            state: 'timeout',
            code: 'BV-9003',
            message: 'BrowserView loading state 10sn timeout! Kullanıcıya overlay gösterildi.'
          });
        }
      }, timeoutMs);
    } else {
      setTimeoutActive(false);
    }
    return () => clearTimeout(timer);
  }, [loading, setTimeoutActive, timeoutMs]);
}
