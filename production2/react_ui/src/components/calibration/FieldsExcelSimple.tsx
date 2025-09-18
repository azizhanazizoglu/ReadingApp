import React from 'react';

interface Props {
  fieldKeys: string[];
  fieldSelectors: Record<string,string|string[]>;
  values?: Record<string,string>; // extracted OCR / JSON values for user reference
  availableKeys: string[]; // allowed selectable keys
  readMode: boolean;
  liteMode: boolean;
  darkMode: boolean;
  status: Record<string,'unknown'|'checking'|'ok'|'missing'>;
  inputBg: string;
  inputBorder: string;
  chipBorder: string;
  headerBorder: string;
  textSub: string;
  onAddField: ()=>void;
  onRemoveField: (k:string)=>void;
  onRenameField: (oldK:string,newK:string)=>void;
  handleChange: (k:string,v:string,idx:number)=>void;
  addRowEnd: (k:string)=>void;
  clearRow: (k:string,idx:number)=>void;
  removeRow: (k:string,idx:number)=>void;
  handlePickAssign: (k:string,idx:number)=>void;
  keyIdx: (k:string,idx:number)=>string;
}

const FieldsExcelSimple: React.FC<Props> = ({ fieldKeys, fieldSelectors, values, availableKeys, readMode, liteMode, darkMode, status, inputBg, inputBorder, chipBorder, headerBorder, textSub, onAddField, onRemoveField, onRenameField, handleChange, addRowEnd, clearRow, removeRow, handlePickAssign, keyIdx }) => {
  const maxAliases = fieldKeys.reduce((m,k)=>{ const v=fieldSelectors[k]; const len=Array.isArray(v)?v.length:(v?1:1); return Math.max(m,len); },1);
  const aliasIndices = Array.from({length:maxAliases},(_,i)=>i);
  const used = new Set(fieldKeys);
  return (
    <div style={{ maxHeight:260, overflow:'auto', border:`1px solid ${headerBorder}`, borderRadius:10, background: darkMode?'rgba(2,6,23,0.35)':'#ffffff' }}>
      <table style={{ width:'100%', borderCollapse:'collapse', fontSize:11 }}>
        <thead>
          <tr>
            <th style={{ position:'sticky', top:0, background:darkMode?'#0f172a':'#f1f5f9', textAlign:'left', padding:6, borderBottom:`1px solid ${headerBorder}` }}>Field Name</th>
            <th style={{ position:'sticky', top:0, background:darkMode?'#0f172a':'#f1f5f9', textAlign:'left', padding:6, borderBottom:`1px solid ${headerBorder}` }}>Value</th>
            {aliasIndices.map(i=> <th key={i} style={{ position:'sticky', top:0, background:darkMode?'#0f172a':'#f1f5f9', textAlign:'left', padding:6, borderBottom:`1px solid ${headerBorder}` }}>Alias {i+1}</th>)}
            {!readMode && <th style={{ position:'sticky', top:0, background:darkMode?'#0f172a':'#f1f5f9', padding:6 }}>
              <button onClick={onAddField} style={{ fontSize:10, padding:'4px 6px', border:`1px solid ${chipBorder}`, borderRadius:8, background: darkMode?'#0b1220':'#eef2ff' }}>+ Field</button>
            </th>}
          </tr>
        </thead>
        <tbody>
          {fieldKeys.map(k=>{ const vals = Array.isArray(fieldSelectors[k])? [...fieldSelectors[k] as string[]] : [String(fieldSelectors[k]||'')]; while(vals.length<aliasIndices.length) vals.push(''); const rawVal = values?.[k]; return (
            <tr key={k} style={{ borderBottom:`1px solid ${headerBorder}` }}>
              <td style={{ padding:4, minWidth:140 }}>
                {readMode ? (
                  <div style={{ fontSize:11 }}>{k}</div>
                ) : (
                  <select defaultValue={k} onChange={e=>{ const nv=e.target.value; if(nv && nv!==k) onRenameField(k,nv); }} style={{ width:'100%', fontSize:11, padding:'4px 6px', background: inputBg, border:`1px solid ${inputBorder}`, borderRadius:6 }}>
                    {[...new Set([k,...availableKeys])].map(opt=>{
                      const disabled = opt!==k && used.has(opt);
                      return <option key={opt} value={opt} disabled={disabled}>{opt}{disabled?' (used)':''}</option>;
                    })}
                  </select>
                )}
              </td>
              <td style={{ padding:4, minWidth:140, fontSize:11, color:textSub, opacity:0.85 }} title={rawVal||''}>
                {rawVal ? (rawVal.length>32? rawVal.slice(0,32)+'…': rawVal) : <span style={{ opacity:0.4 }}>—</span>}
              </td>
              {vals.map((val,idx)=>{ const sk=keyIdx(k,idx); return (
                <td key={sk} style={{ padding:4, minWidth:120, position:'relative' }}>
                  <input value={val||''} disabled={readMode} onChange={e=>handleChange(k,e.target.value,idx)} placeholder="#id or .cls" style={{ width:'100%', fontSize:11, padding:'4px 6px', background: inputBg, border:`1px solid ${inputBorder}`, borderRadius:6 }} />
                  {!readMode && idx===vals.length-1 && <button onClick={()=>addRowEnd(k)} style={{ position:'absolute', top:2, right:2, fontSize:10, padding:'2px 4px', border:`1px solid ${chipBorder}`, borderRadius:6, background: darkMode?'#0b1220':'#eef2ff' }}>+A</button>}
                  {!readMode && vals.length>1 && <button onClick={()=>removeRow(k,idx)} style={{ position:'absolute', bottom:2, right:2, fontSize:10, padding:'2px 4px', border:`1px solid ${inputBorder}`, borderRadius:6, background:'transparent', color:textSub }}>×</button>}
                  {!liteMode && status[sk]==='ok' && <span style={{ position:'absolute', left:4, top:4, fontSize:9, color:'#10b981' }}>ok</span>}
                  {!liteMode && status[sk]==='missing' && <span style={{ position:'absolute', left:4, top:4, fontSize:9, color:'#ef4444' }}>missing</span>}
                </td>
              ); })}
              {!readMode && <td style={{ padding:4, display:'flex', flexDirection:'column', gap:4 }}>
                <button onClick={()=>handlePickAssign(k,0)} style={{ fontSize:10, padding:'4px 6px', border:`1px solid ${chipBorder}`, borderRadius:8, background: darkMode?'#0b1220':'#eef2ff' }}>Pick</button>
                <button onClick={()=>clearRow(k,0)} style={{ fontSize:10, padding:'4px 6px', border:`1px solid ${inputBorder}`, borderRadius:8, background:'transparent', color:textSub }}>Clear</button>
                <button onClick={()=>onRemoveField(k)} style={{ fontSize:10, padding:'4px 6px', border:`1px solid ${inputBorder}`, borderRadius:8, background:'transparent', color:'#ef4444' }}>Del</button>
              </td>}
            </tr>
          ); })}
        </tbody>
      </table>
    </div>
  );
};

export default FieldsExcelSimple;
