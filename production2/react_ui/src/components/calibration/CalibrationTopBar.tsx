import React from 'react';

interface Props {
  host: string;
  task: string;
  darkMode: boolean;
  chipBorder: string;
  headerBorder: string;
  textMain: string;
  textSub: string;
  statusLabel: string; // manual / saving / saved / error
  onTaskMenu: () => void;
  taskMenuOpen: boolean;
  loadTaskSuggestions: () => void;
  onClear: () => void; // Clear backend + local
  onPush: () => void;  // Save local -> backend
  onUpdate: () => void; // Pull backend -> overwrite local
  onRevert: () => void; // Revert local to last pulled snapshot
  onToggleLogs: () => void;
  showLogs: boolean;
  onClose?: () => void;
  docked?: boolean;
}

const CalibrationTopBar: React.FC<Props> = ({ host, task, darkMode, chipBorder, headerBorder, textMain, textSub, statusLabel, onTaskMenu, taskMenuOpen, loadTaskSuggestions, onClear, onPush, onUpdate, onRevert, onToggleLogs, showLogs, onClose, docked }) => {
  return (
    <div style={{ padding:'12px 14px', borderBottom:`1px solid ${headerBorder}`, display:'flex', justifyContent:'space-between', alignItems:'center', gap:8 }}>
      <div style={{ color: textMain, fontWeight:600, display:'flex', alignItems:'center', gap:10 }}>
        <span>Calibration</span>
        <span style={{ fontSize:10, padding:'2px 6px', borderRadius:999, border:`1px solid ${statusLabel==='Error'? '#dc2626': statusLabel==='Saving'? '#f59e0b': '#10b981'}`, background: statusLabel==='Error'? (darkMode?'#450a0a':'#fee2e2'): statusLabel==='Saving'? (darkMode?'#3b2f1a':'#fef3c7'): (darkMode?'#064e3b':'#d1fae5'), color: textMain }}>{statusLabel}</span>
      </div>
      <div style={{ display:'flex', gap:8, alignItems:'center', position:'relative' }}>
        <button title="Task" onClick={()=>{ onTaskMenu(); if(!taskMenuOpen) loadTaskSuggestions(); }} style={{ fontSize:12, padding:'6px 10px', border:`1px solid ${chipBorder}`, borderRadius:10, background:darkMode?'#0b1220':'#eef2ff', color:textMain, cursor:'pointer' }}>{task}</button>
        <button onClick={onPush} style={{ fontSize:12, padding:'6px 10px', border:`1px solid ${chipBorder}`, borderRadius:10, background: darkMode? '#064e3b':'#d1fae5' }}>Push</button>
        <button onClick={onUpdate} style={{ fontSize:12, padding:'6px 10px', border:`1px solid ${chipBorder}`, borderRadius:10, background: darkMode? '#1e3a8a':'#dbeafe' }}>Update</button>
        <button onClick={onRevert} style={{ fontSize:12, padding:'6px 10px', border:`1px solid ${chipBorder}`, borderRadius:10, background: darkMode? '#3f3f46':'#f4f4f5' }}>Revert</button>
        <button onClick={onClear} style={{ fontSize:12, padding:'6px 10px', border:`1px solid ${chipBorder}`, borderRadius:10, background: darkMode? '#3b2f1a':'#fef3c7' }}>Clear</button>
        <button onClick={onToggleLogs} style={{ fontSize:12, padding:'6px 10px', border:`1px solid ${chipBorder}`, borderRadius:10, background: showLogs? (darkMode?'#052e2b':'#ccfbf1'): 'transparent', color:textMain }}>Logs</button>
        {!docked && <button title="Close" onClick={onClose} style={{ background:'transparent', border:'none', fontSize:18, padding:6, color:textSub, cursor:'pointer' }}>✕</button>}
      </div>
    </div>
  );
};

export default CalibrationTopBar;
