import React from 'react';

export type LogLevel = 'info' | 'warn' | 'error';
export interface LogEntry { id:number; ts:number; level:LogLevel; msg:string }

export function useCalibLog(ringSize:number=400) {
  const [logs, setLogs] = React.useState<LogEntry[]>([]);
  const seqRef = React.useRef(0);
  const push = React.useCallback((level:LogLevel, msg:string)=>{
    setLogs(prev=>{
      const id = ++seqRef.current;
      const entry:LogEntry = { id, ts: Date.now(), level, msg };
      const next = [...prev, entry];
      return next.length>ringSize ? next.slice(next.length-ringSize) : next;
    });
  },[ringSize]);
  return {
    logs,
    logInfo: (m:string)=>push('info',m),
    logWarn: (m:string)=>push('warn',m),
    logError: (m:string)=>push('error',m),
    clear: ()=> setLogs([])
  };
}
