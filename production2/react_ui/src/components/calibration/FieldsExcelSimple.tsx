import React from 'react';

interface Props {
  fieldKeys: string[];
  fieldSelectors: Record<string,string|string[]>;
  values?: Record<string,string>;
  availableKeys: string[];
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
  onRemoveField: (k:string)=>void; // removes ALL occurrences of k (simple impl)
  onRenameField: (oldK:string,newK:string)=>void; // renames THIS row's key (may create duplicates)
  handleChange: (k:string,v:string,idx:number)=>void; // idx = occurrence index of key
  handlePickAssign: (k:string,idx:number)=>void;
  keyIdx: (k:string,idx:number)=>string;
}

// NOTE: Alias UI removed. Duplicate rows with the same field key now represent multiple selectors
// (occurrences) for that key. Occurrence index maps into the underlying string|string[] in fieldSelectors.
const FieldsExcelSimple: React.FC<Props> = ({ fieldKeys, fieldSelectors, values, availableKeys, readMode, liteMode, darkMode, status, inputBg, inputBorder, chipBorder, headerBorder, textSub, onAddField, onRemoveField, onRenameField, handleChange, handlePickAssign, keyIdx }) => {
  // Pre-compute occurrence indices for each row
  const occurrenceCounter: Record<string, number> = {};
  const rows = fieldKeys.map(k => {
    const occ = occurrenceCounter[k] ?? 0;
    occurrenceCounter[k] = occ + 1;
    return { k, occIdx: occ };
  });

  return (
    <div style={{ maxHeight:260, overflow:'auto', border:`1px solid ${headerBorder}`, borderRadius:10, background: darkMode?'rgba(2,6,23,0.35)':'#ffffff' }}>
      <table style={{ width:'100%', borderCollapse:'collapse', fontSize:11 }}>
        <thead>
          <tr>
            <th style={{ position:'sticky', top:0, background:darkMode?'#0f172a':'#f1f5f9', textAlign:'left', padding:6, borderBottom:`1px solid ${headerBorder}` }}>Field Name</th>
            <th style={{ position:'sticky', top:0, background:darkMode?'#0f172a':'#f1f5f9', textAlign:'left', padding:6, borderBottom:`1px solid ${headerBorder}` }}>Value</th>
            <th style={{ position:'sticky', top:0, background:darkMode?'#0f172a':'#f1f5f9', textAlign:'left', padding:6, borderBottom:`1px solid ${headerBorder}` }}>Selector</th>
            {!readMode && <th style={{ position:'sticky', top:0, background:darkMode?'#0f172a':'#f1f5f9', padding:6 }}>
              <button onClick={onAddField} style={{ fontSize:10, padding:'4px 6px', border:`1px solid ${chipBorder}`, borderRadius:8, background: darkMode?'#0b1220':'#eef2ff' }}>+ Field</button>
            </th>}
          </tr>
        </thead>
        <tbody>
          {rows.map(({k, occIdx}, rowIdx)=>{
            const rawVal = values?.[k];
            const rawSel = fieldSelectors[k];
            const val = Array.isArray(rawSel)
              ? (rawSel[occIdx] || '')
              : (occIdx === 0 ? String(rawSel || '') : '');
            const sk = keyIdx(k, occIdx);
            return (
              <tr key={sk} style={{ borderBottom:`1px solid ${headerBorder}` }}>
                <td style={{ padding:4, minWidth:140 }}>
                  {readMode ? (
                    <div style={{ fontSize:11 }}>{k}{occIdx>0 && <span style={{ opacity:0.6 }}> #{occIdx+1}</span>}</div>
                  ) : (
                    <select defaultValue={k} onChange={e=>{ const nv=e.target.value; if(nv && nv!==k) onRenameField(k,nv); }} style={{ width:'100%', fontSize:11, padding:'4px 6px', background: inputBg, border:`1px solid ${inputBorder}`, borderRadius:6 }}>
                      {[...new Set([k,...availableKeys])].map(opt=> (
                        <option key={opt} value={opt}>{opt}</option>
                      ))}
                    </select>
                  )}
                </td>
                <td style={{ padding:4, minWidth:140, fontSize:11, color:textSub, opacity:0.85 }} title={rawVal||''}>
                  {rawVal ? (rawVal.length>32? rawVal.slice(0,32)+'…': rawVal) : <span style={{ opacity:0.4 }}>—</span>}
                </td>
                <td style={{ padding:4, minWidth:160, position:'relative' }}>
                  <input value={val} disabled={readMode} onChange={e=>handleChange(k,e.target.value,occIdx)} placeholder="#id or .cls" style={{ width:'100%', fontSize:11, padding:'4px 6px', background: inputBg, border:`1px solid ${inputBorder}`, borderRadius:6 }} />
                  {!liteMode && status[sk]==='ok' && <span style={{ position:'absolute', left:4, top:4, fontSize:9, color:'#10b981' }}>ok</span>}
                  {!liteMode && status[sk]==='missing' && <span style={{ position:'absolute', left:4, top:4, fontSize:9, color:'#ef4444' }}>missing</span>}
                </td>
                {!readMode && <td style={{ padding:4, display:'flex', flexDirection:'column', gap:4 }}>
                  <button onClick={()=>handlePickAssign(k,occIdx)} style={{ fontSize:10, padding:'4px 6px', border:`1px solid ${chipBorder}`, borderRadius:8, background: darkMode?'#0b1220':'#eef2ff' }}>Pick</button>
                  <button onClick={()=>handleChange(k,'',occIdx)} style={{ fontSize:10, padding:'4px 6px', border:`1px solid ${inputBorder}`, borderRadius:8, background:'transparent', color:textSub }}>Clear</button>
                  <button onClick={()=>onRemoveField(k)} style={{ fontSize:10, padding:'4px 6px', border:`1px solid ${inputBorder}`, borderRadius:8, background:'transparent', color:'#ef4444' }}>Del</button>
                </td>}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default FieldsExcelSimple;
