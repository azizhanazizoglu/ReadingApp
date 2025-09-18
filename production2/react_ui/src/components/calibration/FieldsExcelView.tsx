import React from 'react';

export interface FieldsExcelViewProps {
  fields: string[];
  fieldSelectors: Record<string, string | string[]>;
  aliasStatus: Record<string,'unknown'|'checking'|'ok'|'missing'>;
  liteMode: boolean;
  readMode: boolean;
  darkMode: boolean;
  inputBg: string;
  inputBorder: string;
  chipBorder: string;
  headerBorder: string;
  textSub: string;
  addRowEnd: (k:string)=>void;
  clearRow: (k:string, idx:number)=>void;
  handlePickAssign: (k:string, idx:number)=>void;
  handleChange: (k:string,v:string,idx:number)=>void;
  keyIdx: (k:string,idx:number)=>string;
}

export const FieldsExcelView: React.FC<FieldsExcelViewProps> = ({
  fields, fieldSelectors, aliasStatus, liteMode, readMode, darkMode,
  inputBg, inputBorder, chipBorder, headerBorder, textSub,
  addRowEnd, clearRow, handlePickAssign, handleChange, keyIdx
}) => {
  const maxAliases = fields.reduce((m,k)=>{ const v=fieldSelectors[k]; const len=Array.isArray(v)?v.length: (v?1:1); return Math.max(m,len); },1);
  const aliasIndices = Array.from({length:maxAliases},(_,i)=>i);
  return (
    <div style={{ maxHeight:260, overflow:'auto', border:`1px solid ${headerBorder}`, borderRadius:10, background: darkMode?'rgba(2,6,23,0.35)':'#ffffff' }}>
      <table style={{ width:'100%', borderCollapse:'collapse', fontSize:11 }}>
        <thead>
          <tr>
            <th style={{ position:'sticky', top:0, background:darkMode?'#0f172a':'#f1f5f9', textAlign:'left', padding:6, borderBottom:`1px solid ${headerBorder}` }}>Field</th>
            {aliasIndices.map(i=> <th key={i} style={{ position:'sticky', top:0, background:darkMode?'#0f172a':'#f1f5f9', textAlign:'left', padding:6, borderBottom:`1px solid ${headerBorder}` }}>Alias {i+1}</th>)}
            {!readMode && <th style={{ position:'sticky', top:0, background:darkMode?'#0f172a':'#f1f5f9', padding:6 }} />}
          </tr>
        </thead>
        <tbody>
          {fields.map(k=>{ const vals = Array.isArray(fieldSelectors[k])? [...fieldSelectors[k] as string[]] : [String(fieldSelectors[k]||'')]; while(vals.length<aliasIndices.length) vals.push(''); return (
            <tr key={k} style={{ borderBottom:`1px solid ${headerBorder}` }}>
              <td style={{ padding:6, fontWeight:500, color:textSub }}>{k}</td>
              {vals.map((val,idx)=>{ const sk=keyIdx(k,idx); return (
                <td key={sk} style={{ padding:4, minWidth:120 }}>
                  <input value={val||''} onChange={e=>handleChange(k,e.target.value,idx)} placeholder={`#id or .cls`} style={{ width:'100%', fontSize:11, padding:'4px 6px', background: inputBg, border:`1px solid ${inputBorder}`, borderRadius:6 }} disabled={readMode} />
                  {!liteMode && aliasStatus[sk]==='ok' && <span style={{ fontSize:9, color:'#10b981' }}>ok</span>}
                  {!liteMode && aliasStatus[sk]==='missing' && <span style={{ fontSize:9, color:'#ef4444' }}>missing</span>}
                </td>
              ); })}
              {!readMode && <td style={{ padding:4, display:'flex', gap:4 }}>
                <button onClick={()=> addRowEnd(k)} style={{ fontSize:10, padding:'4px 6px', border:`1px solid ${chipBorder}`, borderRadius:8, background:darkMode? '#0b1220':'#eef2ff' }}>+A</button>
                <button onClick={()=> clearRow(k,0)} style={{ fontSize:10, padding:'4px 6px', border:`1px solid ${inputBorder}`, borderRadius:8, background:'transparent', color:textSub }}>Clr</button>
                <button onClick={()=> handlePickAssign(k,0)} style={{ fontSize:10, padding:'4px 6px', border:`1px solid ${chipBorder}`, borderRadius:8, background:darkMode? '#0b1220':'#eef2ff' }}>Pick</button>
              </td>}
            </tr>
          ); })}
        </tbody>
      </table>
    </div>
  );
};

export default FieldsExcelView;
