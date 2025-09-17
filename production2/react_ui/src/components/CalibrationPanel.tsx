import React from "react";

type Props = {
  host: string;
  task: string;
  ruhsat: Record<string, string>;
  candidates: any[];
  darkMode?: boolean;
  onClose: () => void;
  onSaveDraft: (draft: any) => void;
  onTestPlan?: () => void;
  onFinalize?: () => void;
};

export const CalibrationPanel: React.FC<Props> = ({ host, task, ruhsat, candidates, darkMode = false, onClose, onSaveDraft, onTestPlan, onFinalize }) => {
  const [fieldSelectors, setFieldSelectors] = React.useState<Record<string, string>>({});
  const [executionOrder, setExecutionOrder] = React.useState<string[]>([]);
  const [actions, setActions] = React.useState<string[]>([]);
  const [criticalFields, setCriticalFields] = React.useState<string[]>(["plaka_no","model_yili","sasi_no","motor_no"]);
  const [liveAssignKey, setLiveAssignKey] = React.useState<string | null>(null);

  const fields = React.useMemo(() => Object.keys(ruhsat || {}), [ruhsat]);
  // Persistent panel: Only X closes. No ESC to close.
  const [previews, setPreviews] = React.useState<Record<string, string>>({});
  const [status, setStatus] = React.useState<Record<string, 'unknown'|'checking'|'ok'|'missing'>>({});
  const [htmlSnippets, setHtmlSnippets] = React.useState<Record<string, string>>({});
  const [openHtml, setOpenHtml] = React.useState<Record<string, boolean>>({});

  // No entrance animation to keep it snappy


  // Drag-and-drop for execution order
  const [dragIdx, setDragIdx] = React.useState<number | null>(null);
  const displayedOrder = executionOrder.length ? executionOrder : fields;

  const handleChange = (k: string, v: string) => {
    setFieldSelectors((prev) => ({ ...prev, [k]: v }));
    // debounce-check this selector
    setStatus((s) => ({ ...s, [k]: v ? 'checking' : 'unknown' }));
    const val = v;
    setTimeout(async () => {
      if (fieldSelectors[k] !== val) return; // stale
      if (!val) { setStatus((s)=>({ ...s, [k]: 'unknown' })); return; }
      try {
        const ok = await (window as any).checkSelectorInWebview?.(val);
        setStatus((s)=>({ ...s, [k]: ok ? 'ok' : 'missing' }));
        if (ok) {
          const info = await (window as any).previewSelectorInWebview?.(val);
          if (info && typeof info === 'string') setPreviews((p)=>({ ...p, [k]: info }));
          const html = await (window as any).getElementHtmlInWebview?.(val, 1600);
          if (html && typeof html === 'string') setHtmlSnippets((h)=>({ ...h, [k]: html }));
        }
      } catch {
        setStatus((s)=>({ ...s, [k]: 'missing' }));
      }
    }, 220);
  };

  // Pick element in webview, assign selector to field, and show a small descriptor preview
  const handlePickAssign = async (k: string) => {
    try {
      const sel = await (window as any).pickSelectorFromWebview?.();
      if (sel && typeof sel === 'string') {
        handleChange(k, sel);
        try {
          const info = await (window as any).previewSelectorInWebview?.(sel);
          if (info && typeof info === 'string') setPreviews((p) => ({ ...p, [k]: info }));
        } catch {}
      }
    } catch {}
  };

  const handleSave = () => {
    onSaveDraft({ fieldSelectors, actions, executionOrder, criticalFields });
  };

  const onDragStart = (idx: number) => setDragIdx(idx);
  const onDragOver = (e: React.DragEvent<HTMLDivElement>) => { e.preventDefault(); };
  const onDrop = (idx: number) => {
    if (dragIdx === null) return;
    const arr = [...displayedOrder];
    const [item] = arr.splice(dragIdx, 1);
    arr.splice(idx, 0, item);
    setExecutionOrder(arr);
    setDragIdx(null);
  };

  const bgPanel = darkMode ? 'rgba(17,24,39,0.85)' : '#ffffff';
  const borderCol = darkMode ? 'rgba(148,163,184,0.25)' : '#cbd5e1';
  const headerBorder = darkMode ? 'rgba(148,163,184,0.25)' : '#e2e8f0';
  const textMain = darkMode ? '#E6F0FA' : '#0f172a';
  const textSub = darkMode ? '#cbd5e1' : '#334155';
  const inputBg = darkMode ? 'rgba(30,41,59,0.7)' : '#ffffff';
  const inputBorder = darkMode ? 'rgba(148,163,184,0.35)' : '#cbd5e1';
  const chipBg = darkMode ? '#0b1220' : '#eef2ff';
  const chipBorder = darkMode ? 'rgba(99,102,241,0.6)' : '#94a3b8';
  const scrimBg = 'rgba(0,0,0,0.35)';
  const glassShadow = '0 20px 50px rgba(0,0,0,0.45)';

  return (
    <>
      {/* scrim overlay */}
  {/* scrim overlay (visual only; does not block clicks to iframe) */}
  <div style={{ position: 'fixed', inset: 0, background: scrimBg, zIndex: 1999, pointerEvents: 'none' }} />
  <div style={{ position: 'fixed', right: 24, top: 80, width: 560, height: 620, background: bgPanel, backdropFilter: 'blur(12px)', border: `1px solid ${borderCol}`, borderRadius: 16, boxShadow: glassShadow, zIndex: 2000, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div style={{ padding: '12px 14px', borderBottom: `1px solid ${headerBorder}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ color: textMain, fontWeight: 600, letterSpacing: 0.2 }}>Calibration</div>
          <button onClick={onClose} title="Close" style={{ color: textSub, background: 'transparent', border: 'none', fontSize: 18, padding: 6, borderRadius: 8, cursor: 'pointer' }}>✕</button>
        </div>
        <div style={{ padding: 12, overflow: 'auto', color: textMain }}>
          <div style={{ fontSize: 12, color: textSub, marginBottom: 8 }}>
            Host: <b style={{ color: textMain }}>{host}</b> — Task: <b style={{ color: textMain }}>{task}</b>
          </div>
          <div style={{ fontSize: 12, marginBottom: 8, color: textSub, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Ruhsat fields:</span>
            {liveAssignKey ? (
              <span style={{ fontSize: 11, color: '#22d3ee' }}>Live assign: click a target input… (Esc to cancel)</span>
            ) : null}
          </div>
          <div style={{ maxHeight: 260, overflowY: 'auto', border: `1px solid ${headerBorder}`, borderRadius: 10, padding: 10, background: darkMode ? 'rgba(2,6,23,0.35)' : '#ffffff' }}>
          {fields.map((k) => (
            <div key={k} style={{ display: 'flex', alignItems: 'center', marginBottom: 6, gap: 6 }}>
              <div style={{ width: 160, fontSize: 12, color: textSub, display: 'flex', alignItems: 'center', gap: 8 }} title="Tip: Double-click chip below to assign via picker. Drag chips to set order.">
                <span>{k}</span>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 11, color: textSub }}>
                  {status[k] === 'ok' && <span title="Selector found" style={{ width: 8, height: 8, background: '#10b981', borderRadius: 9999, display: 'inline-block' }} />}
                  {status[k] === 'missing' && <span title="No match" style={{ width: 8, height: 8, background: '#ef4444', borderRadius: 9999, display: 'inline-block' }} />}
                  {status[k] === 'checking' && <span title="Checking…" style={{ width: 8, height: 8, background: '#f59e0b', borderRadius: 9999, display: 'inline-block' }} />}
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', flex: 1, gap: 4 }}>
                <input value={fieldSelectors[k] || ''} onChange={(e)=>handleChange(k, e.target.value)} placeholder={`CSS selector for ${k}`} style={{ width: '100%', fontSize: 12, padding: '8px 10px', color: textMain, background: inputBg, border: `1px solid ${inputBorder}`, borderRadius: 10, outline: 'none' }} />
                {previews[k] && <div style={{ fontSize: 11, color: textSub }}>{previews[k]}</div>}
                {htmlSnippets[k] && (
                  <div style={{ fontSize: 11, color: textSub }}>
                    <button onClick={()=>setOpenHtml((o)=>({ ...o, [k]: !o[k] }))} style={{ fontSize: 11, padding: '2px 6px', marginRight: 6, borderRadius: 8, border: `1px solid ${inputBorder}`, background: 'transparent', color: textSub, cursor: 'pointer' }}>
                      {openHtml[k] ? '▾ HTML' : '▸ HTML'}
                    </button>
                    <button onClick={()=>{ try { navigator.clipboard.writeText(htmlSnippets[k]); } catch {} }} style={{ fontSize: 11, padding: '2px 6px', borderRadius: 8, border: `1px solid ${inputBorder}`, background: 'transparent', color: textSub, cursor: 'pointer' }}>Copy</button>
                    {openHtml[k] && (
                      <pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', marginTop: 6, padding: 8, border: `1px solid ${inputBorder}`, borderRadius: 8, background: darkMode ? 'rgba(2,6,23,0.5)' : '#f8fafc', color: textSub, maxHeight: 220, overflowY: 'auto' }}>{htmlSnippets[k]}</pre>
                    )}
                  </div>
                )}
              </div>
              <button title="Pick a field from the page" onClick={()=>handlePickAssign(k)} style={{ fontSize: 12, padding: '8px 10px', border: `1px solid ${chipBorder}`, borderRadius: 10, background: chipBg, color: textMain, cursor: 'pointer' }}>Pick</button>
              <button title="Enable live assign for this field" onClick={async ()=>{
                setLiveAssignKey(k);
                try {
                  await handlePickAssign(k);
                } finally {
                  setLiveAssignKey(null);
                }
              }} style={{ fontSize: 12, padding: '8px 10px', border: `1px solid ${chipBorder}`, borderRadius: 10, background: darkMode ? '#0b1220' : '#f8fafc', color: textMain, cursor: 'pointer' }}>Live</button>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 10, fontSize: 12, color: textSub }}>Execution order (comma-separated keys):</div>
        <input value={executionOrder.join(',')} onChange={(e)=>setExecutionOrder(e.target.value.split(',').map(s=>s.trim()).filter(Boolean))} placeholder="e.g. sasi_no,motor_no,plaka_no,model_yili" style={{ width: '100%', fontSize: 12, padding: '8px 10px', color: textMain, background: inputBg, border: `1px solid ${inputBorder}`, borderRadius: 10 }} />
        <div style={{ marginTop: 6, fontSize: 12, color: textSub }}>Or drag to reorder:</div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', border: `1px dashed ${inputBorder}`, borderRadius: 10, padding: 8, minHeight: 44 }}>
          {displayedOrder.map((k, idx) => (
            <div key={`${k}-${idx}`} title="Drag to reorder. Double-click to assign on page." onDoubleClick={async ()=>{
                try {
                  const sel = await (window as any).pickSelectorFromWebview?.();
                  if (sel && typeof sel === 'string') setFieldSelectors((prev) => ({ ...prev, [k]: sel }));
                } catch {}
              }} draggable onDragStart={()=>onDragStart(idx)} onDragOver={onDragOver} onDrop={()=>onDrop(idx)}
              style={{ cursor: 'grab', fontSize: 11, padding: '6px 10px', border: `1px solid ${chipBorder}`, borderRadius: 16, background: chipBg, color: textMain }}>
              ☰ {k}
            </div>
          ))}
        </div>
  <div style={{ marginTop: 6, fontSize: 11, color: textSub }}>Note: Dragging directly onto the iframe isn’t supported. Use “Pick” or double-click a chip to assign a selector, and drag chips here to define order.</div>
        <div style={{ marginTop: 10, fontSize: 12, color: textSub }}>Actions (comma-separated button texts):</div>
        <input value={actions.join(',')} onChange={(e)=>setActions(e.target.value.split(',').map(s=>s.trim()).filter(Boolean))} placeholder="e.g. Devam,İleri" style={{ width: '100%', fontSize: 12, padding: '8px 10px', color: textMain, background: inputBg, border: `1px solid ${inputBorder}`, borderRadius: 10 }} />
        <div style={{ marginTop: 10, fontSize: 12, color: textSub }}>Critical fields (comma-separated):</div>
        <input value={criticalFields.join(',')} onChange={(e)=>setCriticalFields(e.target.value.split(',').map(s=>s.trim()).filter(Boolean))} placeholder="plaka_no,model_yili,sasi_no,motor_no" style={{ width: '100%', fontSize: 12, padding: '8px 10px', color: textMain, background: inputBg, border: `1px solid ${inputBorder}`, borderRadius: 10 }} />
        <div style={{ marginTop: 12, display: 'flex', gap: 10 }}>
          <button title="Save a draft of your mapping without changing config.json" onClick={handleSave} style={{ fontSize: 12, padding: '8px 12px', border: `1px solid ${inputBorder}`, borderRadius: 12, background: darkMode ? '#0f172a' : '#e2e8f0', color: textMain, cursor: 'pointer' }}>Save Draft</button>
          {onTestPlan && <button title="Build a dry-run plan from your draft to verify" onClick={onTestPlan} style={{ fontSize: 12, padding: '8px 12px', border: `1px solid ${inputBorder}`, borderRadius: 12, background: darkMode ? '#0f172a' : '#e2e8f0', color: textMain, cursor: 'pointer' }}>Test Plan</button>}
          {onFinalize && <button title="Merge current mapping into config.json for this host/task" onClick={onFinalize} style={{ fontSize: 12, padding: '8px 12px', border: `1px solid ${chipBorder}`, borderRadius: 12, background: darkMode ? '#052e2b' : '#ccfbf1', color: textMain, cursor: 'pointer' }}>Finalize to Config</button>}
        </div>
        <div style={{ marginTop: 12, fontSize: 11, color: textSub }}>Tip: Click Pick and then the target input inside the page to capture selector. Use drag area to adjust execution order.</div>
        </div>
      </div>
    </>
  );
};
