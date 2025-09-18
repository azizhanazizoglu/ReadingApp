import React from 'react';

interface Props {
  executionOrder: string[];
  setExecutionOrder: (v: string[]) => void;
  displayedOrder: string[];
  onDragStart: (i:number)=>void;
  onDragOver: (e:React.DragEvent)=>void;
  onDrop: (i:number)=>void;
  chipBorder: string;
  inputBorder: string;
  inputBg: string;
  textSub: string;
  darkMode: boolean;
  onPickSelector: (k:string)=>void;
}

const ExecutionOrderEditor: React.FC<Props> = ({ executionOrder, setExecutionOrder, displayedOrder, onDragStart, onDragOver, onDrop, chipBorder, inputBorder, inputBg, textSub, darkMode, onPickSelector }) => {
  return (
    <div style={{ marginTop:10 }}>
      <div style={{ fontSize:12, color:textSub, marginBottom:4 }}>Execution order (comma-separated keys):</div>
      <input value={executionOrder.join(',')} onChange={e=> setExecutionOrder(e.target.value.split(',').map(s=>s.trim()).filter(Boolean))} style={{ width:'100%', fontSize:12, padding:'8px 10px', background: inputBg, border:`1px solid ${inputBorder}`, borderRadius:10 }} />
      <div style={{ marginTop:6, fontSize:12, color:textSub }}>Or drag to reorder:</div>
      <div style={{ display:'flex', gap:8, flexWrap:'wrap', border:`1px dashed ${inputBorder}`, borderRadius:10, padding:8, minHeight:44 }}>
        {displayedOrder.map((k,idx)=>(
          <div key={`${k}-${idx}`} draggable onDragStart={()=>onDragStart(idx)} onDragOver={onDragOver} onDrop={()=>onDrop(idx)} onDoubleClick={async ()=>onPickSelector(k)} style={{ cursor:'grab', fontSize:11, padding:'6px 10px', border:`1px solid ${chipBorder}`, borderRadius:16, background:darkMode?'#0b1220':'#eef2ff' }}>☰ {k}</div>
        ))}
      </div>
    </div>
  );
};

export default ExecutionOrderEditor;
