import React from 'react';

export interface FieldFormViewProps {
  fields: string[];
  fieldSelectors: Record<string, string | string[]>;
  liteMode: boolean;
  readMode: boolean;
  darkMode: boolean;
  previews: Record<string,string>;
  status: Record<string,'unknown'|'checking'|'ok'|'missing'>;
  htmlSnippets: Record<string,string>;
  openHtml: Record<string,boolean>;
  chipBorder: string;
  inputBg: string;
  inputBorder: string;
  textSub: string;
  textMain: string;
  headerBorder: string;
  handleChange: (k:string,v:string,idx:number)=>void;
  insertRowAfter: (k:string,idx:number)=>void;
  handlePickAssign: (k:string,idx:number)=>void;
  clearRow: (k:string,idx:number)=>void;
  removeRow: (k:string,idx:number)=>void;
  moveRow: (k:string,idx:number,dir:-1|1)=>void;
  handleShowField: (k:string,idx:number)=>void;
  addRowEnd: (k:string)=>void;
  keyIdx: (k:string,idx:number)=>string;
}

export const FieldsFormView: React.FC<FieldFormViewProps> = ({
  fields, fieldSelectors, liteMode, readMode, darkMode,
  previews, status, htmlSnippets, openHtml,
  chipBorder, inputBg, inputBorder, textSub, textMain, headerBorder,
  handleChange, insertRowAfter, handlePickAssign, clearRow, removeRow, moveRow, handleShowField, addRowEnd, keyIdx
}) => {
  return (
    <div style={{ maxHeight:260, overflowY:'auto', border:`1px solid ${headerBorder}`, borderRadius:10, padding:10, background: darkMode?'rgba(2,6,23,0.35)':'#ffffff' }}>
      {fields.map(k=>{ const vals = Array.isArray(fieldSelectors[k])? fieldSelectors[k] as string[] : [String(fieldSelectors[k]||'')]; const rows = vals.length? vals : ['']; return (
        <div key={k} style={{ display:'flex', flexDirection:'column', gap:6, marginBottom:8 }}>
          <div style={{ display:'flex', alignItems:'center', gap:8 }}>
            <div style={{ width:160, fontSize:12, color:textSub, display:'flex', alignItems:'center', gap:8 }}>
              <span>{k}</span>
              {!readMode && <button onClick={()=> addRowEnd(k)} style={{ fontSize:11, padding:'2px 8px', border:`1px solid ${chipBorder}`, borderRadius:10, background:darkMode? '#0b1220':'#eef2ff' }}>+ Add</button>}
            </div>
          </div>
          {rows.map((val,idx)=>{ const sk=keyIdx(k,idx); return (
            <div key={sk} style={{ display:'flex', alignItems:'flex-start', gap:6 }}>
              {!liteMode && <div style={{ width:8 }}>
                {status[sk]==='ok' && <span title='Selector found' style={{ width:8, height:8, background:'#10b981', borderRadius:9999, display:'inline-block' }} />}
                {status[sk]==='missing' && <span title='No match' style={{ width:8, height:8, background:'#ef4444', borderRadius:9999, display:'inline-block' }} />}
                {status[sk]==='checking' && <span title='Checking' style={{ width:8, height:8, background:'#f59e0b', borderRadius:9999, display:'inline-block' }} />}
              </div>}
              <div style={{ flex:1, display:'flex', flexDirection:'column', gap:4 }}>
                <input value={val||''} onChange={e=>handleChange(k,e.target.value,idx)} onKeyDown={e=>{ if(!readMode && e.key==='Enter'){ e.preventDefault(); insertRowAfter(k,idx); } }} data-field={k} data-idx={idx} placeholder={`CSS selector for ${k}${idx>0?` (alias ${idx+1})`:''}`} style={{ fontSize:12, padding:'8px 10px', background: inputBg, border:`1px solid ${inputBorder}`, borderRadius:10, color:textMain }} disabled={readMode} />
                {!liteMode && previews[sk] && <div style={{ fontSize:11, color:textSub }}>{previews[sk]}</div>}
                {!liteMode && htmlSnippets[sk] && <div style={{ fontSize:11, color:textSub }}>
                  <button onClick={()=> {/* consumer toggles openHtml externally if needed */}} style={{ fontSize:11, padding:'2px 6px', marginRight:6, borderRadius:8, border:`1px solid ${inputBorder}`, background:'transparent', color:textSub }}>HTML</button>
                </div>}
              </div>
              {!readMode && <>
                <button onClick={()=>handlePickAssign(k,idx)} style={{ fontSize:12, padding:'8px 10px', border:`1px solid ${chipBorder}`, borderRadius:10, background:darkMode? '#0b1220':'#eef2ff' }}>Pick</button>
                <button onClick={()=>clearRow(k,idx)} style={{ fontSize:12, padding:'8px 10px', border:`1px solid ${inputBorder}`, borderRadius:10, background:'transparent', color:textSub }}>Clear</button>
                {rows.length>1 && <button onClick={()=> removeRow(k,idx)} style={{ fontSize:12, padding:'8px 10px', border:`1px solid ${inputBorder}`, borderRadius:10, background:'transparent', color:textSub }}>Remove</button>}
                <div style={{ display:'inline-flex', gap:4 }}>
                  <button onClick={()=>moveRow(k,idx,-1)} style={{ fontSize:12, padding:'6px 8px', border:`1px solid ${inputBorder}`, borderRadius:8, background:'transparent', color:textSub }}>▲</button>
                  <button onClick={()=>moveRow(k,idx,1)} style={{ fontSize:12, padding:'6px 8px', border:`1px solid ${inputBorder}`, borderRadius:8, background:'transparent', color:textSub }}>▼</button>
                </div>
              </>}
              <button onClick={()=>handleShowField(k,idx)} style={{ fontSize:12, padding:'8px 10px', border:`1px dashed ${chipBorder}`, borderRadius:10, background:'transparent', color:textMain }}>Show</button>
            </div> ); })}
        </div>
      ); })}
    </div>
  );
};

export default FieldsFormView;
