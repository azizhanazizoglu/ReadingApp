import React from 'react';

export interface LogEntry { id:number; ts:number; level:'info'|'warn'|'error'; msg:string }
export interface LogViewerProps {
  logs: LogEntry[];
  darkMode: boolean;
  headerBorder: string;
  inputBorder: string;
  textSub: string;
  onClear: ()=>void;
}

export const LogViewer: React.FC<LogViewerProps> = ({ logs, darkMode, headerBorder, inputBorder, textSub, onClear }) => {
  return (
    <div style={{ marginTop:12, border:`1px solid ${headerBorder}`, borderRadius:10, padding:8, background: darkMode?'rgba(2,6,23,0.55)':'#ffffff', maxHeight:120, overflow:'auto' }}>
      <div style={{ fontSize:11, marginBottom:4, display:'flex', justifyContent:'space-between' }}>
        <span>Logs ({logs.length})</span>
        <button onClick={onClear} style={{ fontSize:10, padding:'2px 6px', border:`1px solid ${inputBorder}`, borderRadius:8, background:'transparent', color:textSub }}>Clear</button>
      </div>
      {logs.slice().reverse().map(l=> <div key={l.id} style={{ fontSize:10, lineHeight:1.4, color: l.level==='error'?'#ef4444': (l.level==='warn'?'#f59e0b':textSub) }}>[{new Date(l.ts).toLocaleTimeString()}] {l.level.toUpperCase()} — {l.msg}</div>)}
    </div>
  );
};

export default LogViewer;
