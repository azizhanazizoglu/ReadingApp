import React from 'react';

export interface SelectorValidationState {
  status: Record<string,'unknown'|'checking'|'ok'|'missing'>;
  previews: Record<string,string>;
  htmlSnippets: Record<string,string>;
  openHtml: Record<string,boolean>;
  actStatus: Record<string,'unknown'|'checking'|'ok'|'missing'>;
  actPreviews: Record<string,string>;
  actHtmlSnippets: Record<string,string>;
  actOpenHtml: Record<string,boolean>;
}

export interface SelectorValidationAPI extends SelectorValidationState {
  resetFieldCaches: (fieldKey:string)=>void;
  markFieldChecking: (kIdx:string)=>void;
  updateFieldResult: (kIdx:string, ok:boolean, preview?:string, html?:string)=>void;
  clearFieldEntry: (kIdx:string)=>void;
  markActionChecking: (id:string)=>void;
  updateActionResult: (id:string, ok:boolean, preview?:string, html?:string)=>void;
  clearAction: (id:string)=>void;
  toggleFieldHtml: (kIdx:string)=>void;
  toggleActionHtml: (id:string)=>void;
}

export function useSelectorValidation(liteMode:boolean){
  const [status,setStatus] = React.useState<SelectorValidationState['status']>({});
  const [previews,setPreviews] = React.useState<SelectorValidationState['previews']>({});
  const [htmlSnippets,setHtmlSnippets] = React.useState<SelectorValidationState['htmlSnippets']>({});
  const [openHtml,setOpenHtml] = React.useState<SelectorValidationState['openHtml']>({});
  const [actStatus,setActStatus] = React.useState<SelectorValidationState['actStatus']>({});
  const [actPreviews,setActPreviews] = React.useState<SelectorValidationState['actPreviews']>({});
  const [actHtmlSnippets,setActHtmlSnippets] = React.useState<SelectorValidationState['actHtmlSnippets']>({});
  const [actOpenHtml,setActOpenHtml] = React.useState<SelectorValidationState['actOpenHtml']>({});

  const resetFieldCaches = React.useCallback((field:string)=>{
    if(liteMode) return;
    const pref = field + '::';
    setStatus(s=>{ const n:any={}; for(const [k,v] of Object.entries(s)) if(!k.startsWith(pref)) n[k]=v; return n; });
    setPreviews(s=>{ const n:any={}; for(const [k,v] of Object.entries(s)) if(!k.startsWith(pref)) n[k]=v; return n; });
    setHtmlSnippets(s=>{ const n:any={}; for(const [k,v] of Object.entries(s)) if(!k.startsWith(pref)) n[k]=v; return n; });
    setOpenHtml(s=>{ const n:any={}; for(const [k,v] of Object.entries(s)) if(!k.startsWith(pref)) n[k]=v; return n; });
  },[liteMode]);

  const markFieldChecking = React.useCallback((kIdx:string)=>{ if(liteMode) return; setStatus(s=>({...s,[kIdx]:'checking'})); },[liteMode]);
  const updateFieldResult = React.useCallback((kIdx:string, ok:boolean, preview?:string, html?:string)=>{ if(liteMode) return; setStatus(s=>({...s,[kIdx]:ok?'ok':'missing'})); if(ok && preview) setPreviews(p=>({...p,[kIdx]:preview})); if(ok && html) setHtmlSnippets(h=>({...h,[kIdx]:html})); },[liteMode]);
  const clearFieldEntry = React.useCallback((kIdx:string)=>{ if(liteMode) return; setStatus(s=>({...s,[kIdx]:'unknown'})); setPreviews(p=>{ const n={...p}; delete (n as any)[kIdx]; return n; }); setHtmlSnippets(h=>{ const n={...h}; delete (n as any)[kIdx]; return n; }); setOpenHtml(o=>{ const n={...o}; delete (n as any)[kIdx]; return n; }); },[liteMode]);
  const markActionChecking = React.useCallback((id:string)=>{ if(liteMode) return; setActStatus(s=>({...s,[id]:'checking'})); },[liteMode]);
  const updateActionResult = React.useCallback((id:string, ok:boolean, preview?:string, html?:string)=>{ if(liteMode) return; setActStatus(s=>({...s,[id]: ok?'ok':'missing'})); if(ok && preview) setActPreviews(p=>({...p,[id]:preview})); if(ok && html) setActHtmlSnippets(h=>({...h,[id]:html})); },[liteMode]);
  const clearAction = React.useCallback((id:string)=>{ if(liteMode) return; setActStatus(s=>({...s,[id]:'unknown'})); setActPreviews(p=>{ const n={...p}; delete (n as any)[id]; return n; }); setActHtmlSnippets(h=>{ const n={...h}; delete (n as any)[id]; return n; }); setActOpenHtml(o=>{ const n={...o}; delete (n as any)[id]; return n; }); },[liteMode]);
  const toggleFieldHtml = React.useCallback((kIdx:string)=> setOpenHtml(o=>({...o,[kIdx]: !o[kIdx]})),[]);
  const toggleActionHtml = React.useCallback((id:string)=> setActOpenHtml(o=>({...o,[id]: !o[id]})),[]);

  return { status, previews, htmlSnippets, openHtml, actStatus, actPreviews, actHtmlSnippets, actOpenHtml, resetFieldCaches, markFieldChecking, updateFieldResult, clearFieldEntry, markActionChecking, updateActionResult, clearAction, toggleFieldHtml, toggleActionHtml } as SelectorValidationAPI;
}
