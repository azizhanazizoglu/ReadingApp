import React from 'react';

export interface ActionItem { id:string; label:string; selector?:string }

export interface ActionsEditorProps {
  actions: ActionItem[];
  liteMode: boolean;
  readMode: boolean;
  darkMode: boolean;
  actStatus: Record<string,'unknown'|'checking'|'ok'|'missing'>;
  actPreviews: Record<string,string>;
  actHtmlSnippets: Record<string,string>;
  actOpenHtml: Record<string,boolean>;
  inputBg: string;
  inputBorder: string;
  chipBorder: string;
  textSub: string;
  textMain: string;
  headerBorder: string;
  onActionChange: (id:string, field:'label'|'selector', v:string)=>void;
  onPick: (id:string)=>void;
  onShow: (id:string)=>void;
  onDragStart: (i:number)=>void;
  onDrop: (i:number)=>void;
  onDragOver: (e:React.DragEvent)=>void;
  addAction: ()=>void;
}

export const ActionsEditor: React.FC<ActionsEditorProps> = ({ actions, liteMode, readMode, darkMode, actStatus, actPreviews, actHtmlSnippets, actOpenHtml, inputBg, inputBorder, chipBorder, textSub, textMain, headerBorder, onActionChange, onPick, onShow, onDragStart, onDrop, onDragOver, addAction }) => {
  return (
    <>
      <div style={{ marginTop:14, fontSize:12, color:textSub, display:'flex', justifyContent:'space-between', alignItems:'center' }}>
        <span>Actions:</span>
        {!readMode && <button onClick={addAction} style={{ fontSize:12, padding:'6px 10px', border:`1px solid ${chipBorder}`, borderRadius:10, background:darkMode? '#0b1220':'#eef2ff' }}>+ Add Action</button>}
      </div>
      <div style={{ maxHeight:220, overflowY:'auto', border:`1px solid ${headerBorder}`, borderRadius:10, padding:10, background: darkMode?'rgba(2,6,23,0.35)':'#ffffff' }}>
        {actions.map((a,idx)=>(<div key={a.id} style={{ display:'flex', alignItems:'center', marginBottom:6, gap:6 }}>
          <div style={{ width:160, display:'flex', flexDirection:'column', gap:4 }}>
            <input value={a.label} onChange={e=>onActionChange(a.id,'label',e.target.value)} placeholder={`Action ${idx+1} label`} style={{ fontSize:12, padding:'6px 8px', background: inputBg, border:`1px solid ${inputBorder}`, borderRadius:10 }} disabled={readMode} />
            {!liteMode && <div style={{ display:'flex', alignItems:'center', gap:6, fontSize:11, color:textSub }}>
              {actStatus[a.id]==='ok' && <span style={{ width:8,height:8,background:'#10b981',borderRadius:9999,display:'inline-block' }} />}
              {actStatus[a.id]==='missing' && <span style={{ width:8,height:8,background:'#ef4444',borderRadius:9999,display:'inline-block' }} />}
              {actStatus[a.id]==='checking' && <span style={{ width:8,height:8,background:'#f59e0b',borderRadius:9999,display:'inline-block' }} />}
            </div>}
          </div>
          <div style={{ flex:1, display:'flex', flexDirection:'column', gap:4 }}>
            <input value={a.selector||''} onChange={e=>onActionChange(a.id,'selector',e.target.value)} placeholder={`CSS selector for ${a.label||('Action '+(idx+1))}`} style={{ fontSize:12, padding:'8px 10px', background: inputBg, border:`1px solid ${inputBorder}`, borderRadius:10 }} disabled={readMode} />
            {!liteMode && actPreviews[a.id] && <div style={{ fontSize:11, color:textSub }}>{actPreviews[a.id]}</div>}
            {!liteMode && actHtmlSnippets[a.id] && <div style={{ fontSize:11, color:textSub }}>
              <button onClick={()=>{/* consumer toggles html open */}} style={{ fontSize:11, padding:'2px 6px', marginRight:6, borderRadius:8, border:`1px solid ${inputBorder}`, background:'transparent', color:textSub }}>{actOpenHtml[a.id]? '▾ HTML':'▸ HTML'}</button>
              <button onClick={()=>{ try { navigator.clipboard.writeText(actHtmlSnippets[a.id]); } catch {} }} style={{ fontSize:11, padding:'2px 6px', borderRadius:8, border:`1px solid ${inputBorder}`, background:'transparent', color:textSub }}>Copy</button>
            </div>}
          </div>
          {!readMode && <button onClick={()=>onPick(a.id)} style={{ fontSize:12, padding:'8px 10px', border:`1px solid ${chipBorder}`, borderRadius:10, background:darkMode? '#0b1220':'#eef2ff' }}>Pick</button>}
          <button onClick={()=>onShow(a.id)} style={{ fontSize:12, padding:'8px 10px', border:`1px dashed ${chipBorder}`, borderRadius:10, background:'transparent', color:textMain }}>Show</button>
        </div>))}
      </div>
      {!readMode ? (
        <div style={{ marginTop:6, fontSize:12, color:textSub }}>Actions: drag to reorder
          <div style={{ display:'flex', gap:8, flexWrap:'wrap', border:`1px dashed ${inputBorder}`, borderRadius:10, padding:8, minHeight:44 }}>
            {actions.map((a,idx)=>(<div key={`${a.id}-chip`} draggable onDragStart={()=>onDragStart(idx)} onDragOver={onDragOver} onDrop={()=>onDrop(idx)} style={{ cursor:'grab', fontSize:11, padding:'6px 10px', border:`1px solid ${chipBorder}`, borderRadius:16, background:darkMode? '#0b1220':'#eef2ff' }}>☰ {a.label||`Action ${idx+1}`}</div>))}
          </div>
        </div>
      ) : (
        <div style={{ marginTop:6, fontSize:12, color:textSub }}>Actions:
          <div style={{ display:'flex', gap:8, flexWrap:'wrap', border:`1px solid ${inputBorder}`, borderRadius:10, padding:8, minHeight:44, background: darkMode?'rgba(2,6,23,0.35)':'#ffffff' }}>
            {actions.map((a,idx)=>(<div key={`ro-act-${a.id}-${idx}`} style={{ fontSize:11, padding:'6px 10px', border:`1px solid ${chipBorder}`, borderRadius:16, background:darkMode? '#0b1220':'#eef2ff' }}>{a.label||`Action ${idx+1}`}</div>))}
          </div>
        </div>
      )}
    </>
  );
};

export default ActionsEditor;
