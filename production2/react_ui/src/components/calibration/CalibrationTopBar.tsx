import React from 'react';

interface Props {
  host: string;
  task: string;
  darkMode: boolean;
  chipBorder: string;
  headerBorder: string;
  textMain: string;
  textSub: string;
  autoStatus: 'idle'|'saving'|'saved'|'error';
  onTaskMenu: () => void;
  taskMenuOpen: boolean;
  loadTaskSuggestions: () => void;
  onClear: () => void;
  onToggleLogs: () => void;
  showLogs: boolean;
  onClose?: () => void;
  docked?: boolean;
}

const CalibrationTopBar: React.FC<Props> = ({ host, task, darkMode, chipBorder, headerBorder, textMain, textSub, autoStatus, onTaskMenu, taskMenuOpen, loadTaskSuggestions, onClear, onToggleLogs, showLogs, onClose, docked }) => {
  return (
    <div style={{ padding:'12px 14px', borderBottom:`1px solid ${headerBorder}`, display:'flex', justifyContent:'space-between', alignItems:'center', gap:8 }}>
      <div style={{ color: textMain, fontWeight:600, display:'flex', alignItems:'center', gap:10 }}>
        <span>Calibration</span>
        <span style={{ fontSize:10, padding:'2px 6px', borderRadius:999, border:`1px solid #6366f1`, background: darkMode?'#1e1b4b':'#e0e7ff', color: textMain }}>LIVE</span>
        <span style={{ fontSize:10, padding:'2px 6px', borderRadius:999, border:`1px solid ${autoStatus==='error'? '#dc2626': autoStatus==='saving'? '#f59e0b': '#10b981'}`, background: autoStatus==='error'? (darkMode?'#450a0a':'#fee2e2'): autoStatus==='saving'? (darkMode?'#3b2f1a':'#fef3c7'): (darkMode?'#064e3b':'#d1fae5'), color: textMain }}>
          {autoStatus==='saving' && 'Saving...'}
          {autoStatus==='saved' && 'Saved'}
          {autoStatus==='idle' && 'Idle'}
          {autoStatus==='error' && 'Error'}
        </span>
      </div>
      <div style={{ display:'flex', gap:8, alignItems:'center', position:'relative' }}>
        <button onClick={()=>{ onTaskMenu(); if(!taskMenuOpen) loadTaskSuggestions(); }} style={{ fontSize:12, padding:'6px 10px', border:`1px solid ${chipBorder}`, borderRadius:10, background:darkMode?'#0b1220':'#eef2ff', color:textMain, cursor:'pointer' }}>☰</button>
        <button onClick={onClear} style={{ fontSize:12, padding:'6px 10px', border:`1px solid ${chipBorder}`, borderRadius:10, background: darkMode? '#3b2f1a':'#fef3c7' }}>Clean</button>
        <button onClick={onToggleLogs} style={{ fontSize:12, padding:'6px 10px', border:`1px solid ${chipBorder}`, borderRadius:10, background: showLogs? (darkMode?'#052e2b':'#ccfbf1'): 'transparent', color:textMain }}>Logs</button>
        {!docked && <button onClick={onClose} style={{ background:'transparent', border:'none', fontSize:18, padding:6, color:textSub, cursor:'pointer' }}>✕</button>}
      </div>
    </div>
  );
};

export default CalibrationTopBar;
