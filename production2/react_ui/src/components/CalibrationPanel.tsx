import React from "react";
import FieldsExcelSimple from './calibration/FieldsExcelSimple';
import ActionsEditor from './calibration/ActionsEditor';
import LogViewer from './calibration/LogViewer';
import CalibrationTopBar from './calibration/CalibrationTopBar';
import ExecutionOrderEditor from './calibration/ExecutionOrderEditor';
import CriticalFieldsEditor from './calibration/CriticalFieldsEditor';
import { useCalibLog } from './calibration/useCalibLog';
// TODO: integrate useSelectorValidation to replace inline validation state.
import { getDomAndUrlFromWebview } from "../services/webviewDom";
import { BACKEND_URL } from "@/config";

// Standard ruhsat fields for static heuristic mapping (ensures user always sees core set)
const DEFAULT_RUHSAT_KEYS = [
	'plaka_no','marka','model','model_yili','sasi_no','motor_no','yakit','renk'
];

type Props = {
	host: string;
	task: string;
	ruhsat: Record<string, string>;
	candidates?: any[];
	darkMode?: boolean;
	onClose: () => void;
	onSaveDraft?: (draft: any) => void;
	onTestPlan?: () => void;
	onFinalize?: () => void;
	existingDraft?: any;
  docked?: boolean; // when true, render inline (push iframe) instead of overlay modal
};

// Combined panel: Full features + Lite (Excel) mode
// Lite mode disables live validation (status, previews, html) to reduce overhead

export const CalibrationPanel: React.FC<Props> = ({ host, task, ruhsat, darkMode = false, onClose, onSaveDraft, onTestPlan, onFinalize, existingDraft, docked=false }) => {
	// Simplified single-mode panel: always excel-style & lite validation (no heavy live preview by default)
	const [liteMode] = React.useState<boolean>(true);
	// Logging (moved to reusable hook)
	const { logs, logInfo, logWarn, logError, clear: clearLogs } = useCalibLog(400);
	const [showLogs, setShowLogs] = React.useState<boolean>(false);
	// Task selection
	const [selectedTask, setSelectedTask] = React.useState<string>(task || "Yeni Trafik");
	const [taskMenuOpen, setTaskMenuOpen] = React.useState<boolean>(false);
	const [taskInput, setTaskInput] = React.useState<string>(task || "Yeni Trafik");
	const [taskSuggestions, setTaskSuggestions] = React.useState<string[]>([]);
	const loadTaskSuggestions = React.useCallback(async () => {
		try {
			const r = await fetch(`${BACKEND_URL}/api/calib`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ op: 'list', mapping: { host } }) });
			const j = await r.json();
			const items = Array.isArray(j?.items) ? j.items : [];
			setTaskSuggestions(items.filter((s: any) => typeof s === 'string'));
		} catch {
			setTaskSuggestions([]);
		}
	}, [host]);
	React.useEffect(() => { setSelectedTask(task || "Yeni Trafik"); setTaskInput(task || "Yeni Trafik"); }, [task]);
	// Field selectors / pages
	const [fieldSelectors, setFieldSelectors] = React.useState<Record<string, string | string[]>>({});
	const [executionOrder, setExecutionOrder] = React.useState<string[]>([]);
	type ActionItem = { id: string; label: string; selector?: string };
	const [actionsDetail, setActionsDetail] = React.useState<ActionItem[]>([{ id: 'a1', label: 'Action 1', selector: '' }]);
	const [criticalFields, setCriticalFields] = React.useState<string[]>(["plaka_no","model_yili","sasi_no","motor_no"]);
	type CalibPage = { id: string; name: string; urlPattern?: string; urlSample?: string; fieldSelectors: Record<string,string|string[]>; fieldKeys?: string[]; executionOrder: string[]; actionsDetail: ActionItem[]; criticalFields: string[]; isLast?: boolean };
	const [pages, setPages] = React.useState<CalibPage[]>([]);
	const [pageName, setPageName] = React.useState<string>("Page 1");
	const [urlPattern, setUrlPattern] = React.useState<string>("");
	const [urlSample, setUrlSample] = React.useState<string>("");
	const [currentPageId, setCurrentPageId] = React.useState<string>(() => `p_${Date.now().toString(36)}`);
	// Dynamic field keys user can edit. Initialize from ruhsat keys on first mount; then merge in any new ruhsat keys if prop changes.
	const [fieldKeys, setFieldKeys] = React.useState<string[]>(() => Object.keys(ruhsat || {}));
	// All selectable keys (user will choose from these instead of free typing)
	const availableKeys = React.useMemo(()=>{
		const set = new Set<string>([...DEFAULT_RUHSAT_KEYS, ...Object.keys(ruhsat||{})]);
		return Array.from(set);
	},[ruhsat]);
	const [fieldFilter, setFieldFilter] = React.useState<string>('');
	React.useEffect(()=>{
		const base = [...DEFAULT_RUHSAT_KEYS, ...Object.keys(ruhsat||{})];
		setFieldKeys(prev=>{
			let changed=false; const set=new Set(prev);
			for(const k of base){ if(!set.has(k)){ set.add(k); changed=true; } }
			return changed? Array.from(set): prev;
		});
	},[ruhsat]);
	// Backward compatibility variable used by existing subcomponents.
	const fields = fieldKeys;
	// UI caches
	const [previews, setPreviews] = React.useState<Record<string, string>>({});
	const [status, setStatus] = React.useState<Record<string, 'unknown'|'checking'|'ok'|'missing'>>({});
	const [htmlSnippets, setHtmlSnippets] = React.useState<Record<string, string>>({});
	const [openHtml, setOpenHtml] = React.useState<Record<string, boolean>>({});
	// Actions caches
	const [actStatus, setActStatus] = React.useState<Record<string, 'unknown'|'checking'|'ok'|'missing'>>({});
	const [actPreviews, setActPreviews] = React.useState<Record<string, string>>({});
	const [actHtmlSnippets, setActHtmlSnippets] = React.useState<Record<string, string>>({});
	const [actOpenHtml, setActOpenHtml] = React.useState<Record<string, boolean>>({});
	const [actDragIdx, setActDragIdx] = React.useState<number | null>(null);
	// Modes
	const readMode = false; // kept as constant for minimal code changes where prop expected
	const [taskMenuOpenBody, setTaskMenuOpenBody] = React.useState<boolean>(false);
	const [flashMsg, setFlashMsg] = React.useState<string>("");
	const flash = (msg: string) => { setFlashMsg(msg); setTimeout(()=> setFlashMsg(""), 1500); };
	// Drag order
	const [dragIdx, setDragIdx] = React.useState<number | null>(null);
	const displayedOrder = executionOrder.length ? executionOrder : fieldKeys;
	const filteredFieldKeys = React.useMemo(()=>{
		if(!fieldFilter.trim()) return fieldKeys;
		const f = fieldFilter.toLowerCase();
		return fieldKeys.filter(k=> k.toLowerCase().includes(f) || String((ruhsat as any)[k]||'').toLowerCase().includes(f));
	},[fieldFilter, fieldKeys, ruhsat]);
	// Normalizer
	const normalizeSelector = (s: string) => {
		let t = String(s || '').trim();
		if (!t) return t;
		t = t.replace(/^[ ]*input\s+#/i, '#');
		const m = t.match(/^[^#]*#([A-Za-z_][\w\-:.]*)$/);
		if (m) t = `#${m[1]}`;
		return t;
	};
	const normalizeAllFields = () => {
		setFieldSelectors(prev=>{
			const out: typeof prev = {};
			for(const [k,v] of Object.entries(prev)){
				const list = Array.isArray(v)? v : [v];
				const seen = new Set<string>();
				const cleaned: string[] = [];
				for(const raw of list){
					const n = normalizeSelector(String(raw||''));
					if(n && !seen.has(n)) { seen.add(n); cleaned.push(n); }
				}
				out[k] = cleaned.length === 0 ? '' : (cleaned.length === 1 ? cleaned[0] : cleaned);
			}
			syncFieldSelectorsToPage(out);
			logInfo('Global normalize applied to all field selectors');
			return out;
		});
	};
	const resetAllFields = () => {
		setFieldSelectors(prev=>{
			const out: typeof prev = {};
			for(const k of Object.keys(prev)) out[k] = '';
			syncFieldSelectorsToPage(out);
			logWarn('All field selectors reset to blank');
			return out;
		});
	};
	const keyIdx = (k: string, idx: number) => `${k}::${idx}`;
	const focusFieldRow = (k: string, idx: number) => { try { document.querySelector<HTMLInputElement>(`input[data-field="${k}"][data-idx="${idx}"]`)?.focus(); } catch {} };
	// Dynamic field list handlers
	const onAddField = () => {
		setFieldKeys(prev=>{
			const used = new Set(prev);
			const nextKey = availableKeys.find(k=> !used.has(k));
			if(!nextKey){ logWarn('All available fields already added'); return prev; }
			setFieldSelectors(fs=>{ const next={...fs,[nextKey]:''}; syncFieldSelectorsToPage(next); return next; });
			logInfo(`Field added: ${nextKey}`);
			return [...prev,nextKey];
		});
	};
	const onRemoveField = (k:string) => {
		setFieldKeys(prev=> prev.filter(f=>f!==k));
		setFieldSelectors(fs=>{ const next={...fs}; delete next[k]; syncFieldSelectorsToPage(next); return next; });
		setExecutionOrder(o=> o.filter(f=>f!==k));
		setCriticalFields(c=> c.filter(f=>f!==k));
		clearCachesForField(k);
		logWarn(`Field removed: ${k}`);
	};
	const onRenameField = (oldK:string,newK:string) => {
		if(!newK || oldK===newK) return;
		setFieldKeys(prev=> prev.map(k=> k===oldK? newK : k));
		setFieldSelectors(fs=>{ const next: typeof fs = {}; for(const [k,v] of Object.entries(fs)){ next[k===oldK?newK:k]=v; } syncFieldSelectorsToPage(next); return next; });
		setExecutionOrder(o=> o.map(k=> k===oldK? newK : k));
		setCriticalFields(c=> c.map(k=> k===oldK? newK : k));
		// migrate validation caches
		if(!liteMode){
			setStatus(s=>{ const n: typeof s = {}; for(const [k,v] of Object.entries(s)){ if(k.startsWith(oldK+'::')){ const idx = k.split('::')[1]; n[newK+'::'+idx]=v; } else n[k]=v; } return n; });
			setPreviews(p=>{ const n: typeof p = {}; for(const [k,v] of Object.entries(p)){ if(k.startsWith(oldK+'::')){ const idx = k.split('::')[1]; n[newK+'::'+idx]=v; } else n[k]=v; } return n; });
			setHtmlSnippets(h=>{ const n: typeof h = {}; for(const [k,v] of Object.entries(h)){ if(k.startsWith(oldK+'::')){ const idx = k.split('::')[1]; n[newK+'::'+idx]=v; } else n[k]=v; } return n; });
			setOpenHtml(o=>{ const n: typeof o = {}; for(const [k,v] of Object.entries(o)){ if(k.startsWith(oldK+'::')){ const idx = k.split('::')[1]; n[newK+'::'+idx]=v; } else n[k]=v; } return n; });
		}
		logInfo(`Field renamed: ${oldK} -> ${newK}`);
	};
	const clearCachesForField = (k: string) => {
		if (liteMode) return; // skip heavy cleanup in lite
		const pref = `${k}::`;
		setStatus(s=>{ const n:any={}; for(const [kk,v] of Object.entries(s)) if(!kk.startsWith(pref)) n[kk]=v; return n; });
		setPreviews(p=>{ const n:any={}; for(const [kk,v] of Object.entries(p)) if(!kk.startsWith(pref)) n[kk]=v; return n; });
		setHtmlSnippets(h=>{ const n:any={}; for(const [kk,v] of Object.entries(h)) if(!kk.startsWith(pref)) n[kk]=v; return n; });
		setOpenHtml(o=>{ const n:any={}; for(const [kk,v] of Object.entries(o)) if(!kk.startsWith(pref)) n[kk]=v; return n; });
	};
	const syncFieldSelectorsToPage = (next: Record<string,string|string[]>) => setPages(prev=> prev.map(p=> p.id===currentPageId ? { ...p, fieldSelectors: next } : p));
	const addRowEnd = (k: string) => setFieldSelectors(prev=>{ const cur = prev[k]; const arr = Array.isArray(cur)?[...cur]:[String(cur||'')]; arr.push(''); const next={...prev,[k]:arr}; setTimeout(()=>focusFieldRow(k,arr.length-1),0); syncFieldSelectorsToPage(next); logInfo(`Alias added (end) for ${k}; total=${arr.length}`); return next; });
	const insertRowAfter = (k: string, idx:number) => setFieldSelectors(prev=>{ const cur=prev[k]; const arr=Array.isArray(cur)?[...cur]:[String(cur||'')]; const at=Math.max(0,Math.min(idx+1,arr.length)); arr.splice(at,0,''); const next={...prev,[k]:arr}; setTimeout(()=>focusFieldRow(k,at),0); syncFieldSelectorsToPage(next); logInfo(`Alias inserted after index ${idx} for ${k}; total=${arr.length}`); return next; });
	// Clear semantics: collapse ALL aliases for field to a single empty string (intuitive reset)
	const clearRow = (k:string, _idx:number) => { setFieldSelectors(prev=>{ const next={...prev,[k]:['']}; clearCachesForField(k); syncFieldSelectorsToPage(next); logInfo(`Field ${k} cleared (aliases collapsed to one empty)`); return next; }); };
	const removeRow = (k:string, idx:number) => setFieldSelectors(prev=>{ const cur=prev[k]; let arr=Array.isArray(cur)?[...cur]:[String(cur||'')]; if(arr.length<=1){ // if last, just clear
		arr=[''];
		logWarn(`Attempted remove on single alias for ${k}; reset to empty`);
	}else{
		arr.splice(idx,1);
		logInfo(`Alias ${idx} removed for ${k}; remaining=${arr.length}`);
	}
	clearCachesForField(k); const next={...prev,[k]:arr}; syncFieldSelectorsToPage(next); return next; });
	const moveRow = (k:string, idx:number, dir:-1|1) => setFieldSelectors(prev=>{ const cur=prev[k]; const arr=Array.isArray(cur)?[...cur]:[String(cur||'')]; const to=idx+dir; if(to<0||to>=arr.length) return prev; [arr[idx],arr[to]]=[arr[to],arr[idx]]; clearCachesForField(k); setTimeout(()=>focusFieldRow(k,to),0); const next={...prev,[k]:arr}; syncFieldSelectorsToPage(next); logInfo(`Alias moved for ${k}: ${idx} -> ${to}`); return next; });
	const cleanFieldSelectors = (fs: Record<string,string|string[]>) => { const out:Record<string,string|string[]>={}; for(const [k,v] of Object.entries(fs)){ const add=(list:string[])=>{ const seen=new Set<string>(); const dedup:string[]=[]; for(const s of list){ const n=normalizeSelector(s); if(n && !seen.has(n)){ seen.add(n); dedup.push(n);} } if(!dedup.length) return ''; if(dedup.length===1) return dedup[0]; return dedup; }; out[k]=Array.isArray(v)?add(v):add([v]); } return out; };
	const handleChange = (k:string, v:string, idx=0) => {
		const norm = normalizeSelector(v);
		setFieldSelectors(prev=>{ const cur=prev[k]; if(Array.isArray(cur)){ const arr=[...cur]; arr[idx]=norm; const next={...prev,[k]:arr}; syncFieldSelectorsToPage(next); return next;} if(idx>0){ const base=String(cur||''); const pad=Array(Math.max(0,idx-1)).fill(''); const next={...prev,[k]:[base,...pad,norm]}; syncFieldSelectorsToPage(next); return next;} const next={...prev,[k]:norm}; syncFieldSelectorsToPage(next); return next; });
		if(liteMode) return;
		const statusKey=keyIdx(k,idx); setStatus(s=>({...s,[statusKey]:norm? 'checking':'unknown'})); const val=norm;
		setTimeout(async ()=>{ const cur=fieldSelectors[k]; const currentVal=Array.isArray(cur)?(cur[idx]??''):(idx===0?String(cur||''):'' ); if(currentVal!==val) return; if(!val){ setStatus(s=>({...s,[statusKey]:'unknown'})); return;} try { const ok= await (window as any).checkSelectorInWebview?.(val); setStatus(s=>({...s,[statusKey]: ok?'ok':'missing'})); if(ok){ const info= await (window as any).previewSelectorInWebview?.(val); if(info && typeof info==='string') setPreviews(p=>({...p,[statusKey]:info})); const html= await (window as any).getElementHtmlInWebview?.(val,1600); if(html && typeof html==='string') setHtmlSnippets(h=>({...h,[statusKey]:html})); } } catch { setStatus(s=>({...s,[statusKey]:'missing'})); } },220);
	};
	const handlePickAssign = async (k:string, idx=0) => { try { const sel = await (window as any).pickSelectorFromWebview?.(); if(sel && typeof sel==='string'){ handleChange(k, sel, idx); if(!liteMode){ try { const info = await (window as any).previewSelectorInWebview?.(normalizeSelector(sel)); if(info && typeof info==='string') setPreviews(p=>({...p,[keyIdx(k,idx)]:info})); } catch {} } } } catch {} };
	const handleShowField = async (k:string, idx=0) => { const cur=fieldSelectors[k]; const sel=Array.isArray(cur)?(cur[idx]||''):String(cur||''); if(!sel) return; try { const info= await (window as any).previewSelectorInWebview?.(sel); if(!liteMode && info && typeof info==='string') setPreviews(p=>({...p,[keyIdx(k,idx)]:info})); if(!liteMode){ const html= await (window as any).getElementHtmlInWebview?.(sel,1600); if(html && typeof html==='string') setHtmlSnippets(h=>({...h,[keyIdx(k,idx)]:html})); } } catch {} };
	const commitCurrentPage = (overrides?: Partial<CalibPage>) => { const cleaned = cleanFieldSelectors(fieldSelectors); setFieldSelectors(cleaned); const current:CalibPage={ id: currentPageId, name: pageName, urlPattern, urlSample, fieldSelectors: cleaned, fieldKeys: fieldKeys.slice(), executionOrder, actionsDetail, criticalFields, ...(overrides||{}) }; setPages(prev=>{ const i=prev.findIndex(p=>p.id===currentPageId); if(i>=0){ const copy=[...prev]; copy[i]=current; return copy; } return [...prev,current]; }); return current; };
	const switchToPage = (p:CalibPage) => { setCurrentPageId(p.id); setPageName(p.name||''); setUrlPattern(p.urlPattern||''); setUrlSample(p.urlSample||''); setFieldSelectors(p.fieldSelectors||{}); setExecutionOrder(Array.isArray(p.executionOrder)?p.executionOrder:[]); setActionsDetail(Array.isArray(p.actionsDetail)?p.actionsDetail:[]); setCriticalFields(Array.isArray(p.criticalFields)?p.criticalFields:[]); };
	// Pure builder (does not call commitCurrentPage to avoid state changes during render/autosave diffing)
	const buildDraftPayload = React.useCallback(()=> {
		const current: CalibPage = {
			id: currentPageId,
			name: pageName,
			urlPattern,
			urlSample,
			fieldSelectors,
			fieldKeys: fieldKeys.slice(),
			executionOrder: executionOrder.slice(),
			actionsDetail: actionsDetail.slice(),
			criticalFields: criticalFields.slice(),
			isLast: pages.find(p=>p.id===currentPageId)?.isLast
		};
		const ordered = pages.some(p=>p.id===current.id) ? pages.map(p=> p.id===current.id ? current : p) : [...pages, current];
		const first = ordered[0] || current;
		return {
			fieldSelectors: first.fieldSelectors,
			fieldKeys: first.fieldKeys || fieldKeys.slice(),
			actions: first.actionsDetail.map(a=>a.label).filter(Boolean),
			actionsDetail: first.actionsDetail,
			actionsExecutionOrder: first.actionsDetail.map(a=>a.label).filter(Boolean),
			executionOrder: first.executionOrder,
			criticalFields: first.criticalFields,
			pages: ordered,
			currentPageId: current.id
		};
	}, [currentPageId, pageName, urlPattern, urlSample, fieldSelectors, fieldKeys, executionOrder, actionsDetail, criticalFields, pages]);
	const handleSaveInternal = React.useCallback(async ()=>{ const draft = buildDraftPayload(); try { await fetch(`${BACKEND_URL}/api/calib`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ op:'saveDraft', mapping:{ host, task: selectedTask, draft } }) }); flash('Saved'); logInfo(`Draft saved for task ${selectedTask}`); onSaveDraft?.(draft); } catch { flash('Error'); logError(`Save failed for task ${selectedTask}`); } }, [buildDraftPayload, host, selectedTask, onSaveDraft]);
	const handleTestPlanInternal = React.useCallback(async ()=>{ try { await fetch(`${BACKEND_URL}/api/calib`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ op:'testFillPlan', mapping:{ host, task: selectedTask } }) }); flash('Planned'); logInfo(`Test plan triggered for ${selectedTask}`); onTestPlan?.(); } catch { flash('Error'); logError(`Test plan failed for ${selectedTask}`); } }, [host, selectedTask, onTestPlan]);
	const handleFinalizeInternal = React.useCallback(async ()=>{ try { await fetch(`${BACKEND_URL}/api/calib`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ op:'finalizeToConfig', mapping:{ host, task: selectedTask } }) }); flash('Finalized'); logInfo(`Finalize requested for ${selectedTask}`); onFinalize?.(); } catch { flash('Error'); logError(`Finalize failed for ${selectedTask}`); } }, [host, selectedTask, onFinalize]);

	// Autosave (draft -> finalize) whenever calibration data changes
	const [autoStatus, setAutoStatus] = React.useState<'idle'|'saving'|'saved'|'error'>('idle');
	const lastSavedRef = React.useRef<any>(null);
	const pendingSaveRef = React.useRef<number | null>(null);
	const buildSnapshot = () => {
		const draft = buildDraftPayload();
		return JSON.stringify({ host, task: selectedTask, draft });
	};
	const performAutosave = React.useCallback(async () => {
		// Guard: avoid backend 422 spam if host missing
		if(!host || host==='unknown') { logWarn('Autosave skipped: missing host'); return; }
		try {
			setAutoStatus('saving');
			const draft = buildDraftPayload();
			await fetch(`${BACKEND_URL}/api/calib`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ op:'saveDraft', mapping:{ host, task: selectedTask, draft } }) });
			// Immediately finalize to config for real-time behavior
			await fetch(`${BACKEND_URL}/api/calib`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ op:'finalizeToConfig', mapping:{ host, task: selectedTask } }) });
			lastSavedRef.current = buildSnapshot();
			setAutoStatus('saved');
			logInfo('Autosave+Finalize completed');
			setTimeout(()=>{ if(autoStatus==='saved') setAutoStatus('idle'); }, 2000);
		} catch (e) {
			setAutoStatus('error');
			logError('Autosave failed');
		}
	}, [buildDraftPayload, host, selectedTask]);

	// Debounce autosave on significant state changes
	React.useEffect(()=>{
		// skip initial mount until draft loaded
		const snap = buildSnapshot();
		if(lastSavedRef.current === null){
			lastSavedRef.current = snap; // initial baseline
			return;
		}
		if(snap === lastSavedRef.current) return; // no change
		if(pendingSaveRef.current) window.clearTimeout(pendingSaveRef.current);
		pendingSaveRef.current = window.setTimeout(()=>{ performAutosave(); }, 700);
		return ()=>{ if(pendingSaveRef.current) window.clearTimeout(pendingSaveRef.current); };
	// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [fieldSelectors, fieldKeys, executionOrder, actionsDetail, criticalFields, pages, selectedTask]);

	// Memo current draft snapshot for render-safe usage (avoid calling buildDraftPayload inside JSX repeatedly)
	const currentDraft = React.useMemo(()=> buildDraftPayload(), [buildDraftPayload]);
	const handleAddNextPage = async () => { const committed = commitCurrentPage(); logInfo(`Committed page ${committed.name} (${committed.id}); adding new page`); const id = `p_${Date.now().toString(36)}`; setCurrentPageId(id); setPageName(`Page ${pages.length + 2}`); const info = await getDomAndUrlFromWebview(); setUrlSample(info.url||''); setUrlPattern(''); setFieldSelectors({}); setExecutionOrder([]); setActionsDetail([{ id:'a1', label:'Action 1', selector:'' }]); };
	const handleMarkLastPage = () => { const committed = commitCurrentPage({ isLast:true }); logInfo(`Marked page as last: ${committed.name}`); setPages(prev=> prev.map(p=> p.id===committed.id ? { ...committed, isLast:true } : p)); };
	const handleCaptureUrl = async () => { const info= await getDomAndUrlFromWebview(); setUrlSample(info.url||''); };
	const onDragStart = (i:number)=> setDragIdx(i); const onDragOver=(e:React.DragEvent)=> e.preventDefault(); const onDrop=(i:number)=>{ if(dragIdx===null) return; const arr=[...displayedOrder]; const [item]=arr.splice(dragIdx,1); arr.splice(i,0,item); setExecutionOrder(arr); setDragIdx(null); };
	// Actions helpers & validation (skip if liteMode)
	const syncActionsToPage = (next:ActionItem[]) => setPages(prev=> prev.map(p=> p.id===currentPageId ? { ...p, actionsDetail: next } : p));
	const handleActionChange = (id:string, field:'label'|'selector', value:string) => { setActionsDetail(prev=>{ const next = prev.map(a=> a.id===id ? { ...a, [field]: value } : a); syncActionsToPage(next); return next; }); if(field==='label') logInfo(`Action label changed (${id}) => ${value}`); if(field==='selector') logInfo(`Action selector changed (${id})`); if(field==='selector' && !liteMode){ setActStatus(s=>({...s,[id]: value? 'checking':'unknown'})); const current=value; setTimeout(async ()=>{ const still = actionsDetail.find(a=>a.id===id)?.selector || ''; if(still!==current) return; if(!current){ setActStatus(s=>({...s,[id]:'unknown'})); return;} try { const ok= await (window as any).checkSelectorInWebview?.(current); setActStatus(s=>({...s,[id]: ok?'ok':'missing'})); if(ok){ const info= await (window as any).previewSelectorInWebview?.(current); if(info && typeof info==='string') setActPreviews(p=>({...p,[id]:info})); const html= await (window as any).getElementHtmlInWebview?.(current,1600); if(html && typeof html==='string') setActHtmlSnippets(h=>({...h,[id]:html})); } } catch { setActStatus(s=>({...s,[id]:'missing'})); } },200); } };
	const handlePickAction = async (id:string) => { try { const sel = await (window as any).pickSelectorFromWebview?.(); if(sel && typeof sel==='string'){ handleActionChange(id,'selector',sel); if(!liteMode){ try { const info= await (window as any).previewSelectorInWebview?.(sel); if(info && typeof info==='string') setActPreviews(p=>({...p,[id]:info})); } catch {} } } } catch {} };
	const handleShowAction = async (id:string) => { const cur=actionsDetail.find(a=>a.id===id)?.selector||''; if(!cur) return; try { const info= await (window as any).previewSelectorInWebview?.(cur); if(!liteMode && info && typeof info==='string') setActPreviews(p=>({...p,[id]:info})); if(!liteMode){ const html= await (window as any).getElementHtmlInWebview?.(cur,1600); if(html && typeof html==='string') setActHtmlSnippets(h=>({...h,[id]:html})); } } catch {} };
	const addAction = () => { const idx=actionsDetail.length+1; const id=`a${Date.now().toString(36)}_${idx}`; setActionsDetail(prev=>{ const next=[...prev,{ id, label:`Action ${idx}`, selector:'' }]; syncActionsToPage(next); logInfo(`Action added (${id})`); return next; }); };
	const onActionDragStart=(i:number)=> setActDragIdx(i); const onActionDrop=(i:number)=>{ if(actDragIdx===null) return; const arr=[...actionsDetail]; const [item]=arr.splice(actDragIdx,1); arr.splice(i,0,item); setActionsDetail(arr); syncActionsToPage(arr); setActDragIdx(null); };
	// Draft apply / load
	const applyDraft = React.useCallback((draft:any, opts?:{preservePage?:boolean}) => { if(!draft|| typeof draft!=='object') return; try { const pagesArr=Array.isArray(draft.pages)?draft.pages:[]; if(pagesArr.length){ setPages(pagesArr); const preserve=!!opts?.preservePage; const keep = preserve? pagesArr.find((p:any)=>p && p.id===currentPageId) : null; const chosen:any = keep || pagesArr[0]; setCurrentPageId(chosen.id||`p_${Date.now().toString(36)}`); setPageName(chosen.name||'Page 1'); setUrlPattern(chosen.urlPattern||''); setUrlSample(chosen.urlSample||''); setFieldSelectors(chosen.fieldSelectors||{}); setFieldKeys(Array.isArray(chosen.fieldKeys)? chosen.fieldKeys : Object.keys(chosen.fieldSelectors||{})); setExecutionOrder(Array.isArray(chosen.executionOrder)?chosen.executionOrder:[]); const acts = Array.isArray(chosen.actionsDetail)?chosen.actionsDetail:[]; setActionsDetail(acts.length? acts : (Array.isArray(draft.actions)? draft.actions.map((lbl:string,i:number)=>({ id:`a${i+1}`, label:String(lbl), selector:'' })) : [{ id:'a1', label:'Action 1', selector:'' }])); setCriticalFields(Array.isArray(chosen.criticalFields)?chosen.criticalFields:(Array.isArray(draft.criticalFields)?draft.criticalFields:criticalFields)); logInfo(`Draft with ${pagesArr.length} page(s) applied`); } else { const fs = (draft.fieldSelectors && typeof draft.fieldSelectors==='object')? draft.fieldSelectors : {}; const fks = Array.isArray(draft.fieldKeys)? draft.fieldKeys : Object.keys(fs); const eo = Array.isArray(draft.executionOrder)?draft.executionOrder:[]; const actsL: string[] = Array.isArray(draft.actions)?draft.actions:[]; const actsD: any[] = Array.isArray(draft.actionsDetail)?draft.actionsDetail:(actsL.length? actsL.map((lbl:string,i:number)=>({id:`a${i+1}`, label:String(lbl), selector:''})):[]); const crit = Array.isArray(draft.criticalFields)?draft.criticalFields:criticalFields; const pgId=`p_${Date.now().toString(36)}`; const one:CalibPage={ id:pgId, name:'Page 1', fieldSelectors: fs, fieldKeys: fks, executionOrder: eo, actionsDetail: actsD, criticalFields: crit }; setPages([one]); setCurrentPageId(pgId); setPageName(one.name); setFieldSelectors(fs); setFieldKeys(fks); setExecutionOrder(eo); setActionsDetail(actsD.length?actsD:[{ id:'a1', label:'Action 1', selector:'' }]); setCriticalFields(crit); logInfo('Single-page draft applied'); } } catch { logError('Failed applying draft'); } }, [criticalFields, currentPageId]);
	React.useEffect(()=>{ if(existingDraft) applyDraft(existingDraft); }, [existingDraft, applyDraft]);
	const lastLoadRef = React.useRef<number>(0);
	const loadLatestDraft = React.useCallback(async ()=>{ try { const now=Date.now(); if(now - lastLoadRef.current < 500) return; lastLoadRef.current = now; const r= await fetch(`${BACKEND_URL}/api/calib`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ op:'load', mapping:{ host, task: selectedTask } }) }); const j= await r.json(); if(j?.ok && j?.data){ applyDraft(j.data,{preservePage:true}); logInfo('Latest draft loaded'); } else { logWarn('No draft found to load'); } } catch { logError('Error loading latest draft'); } }, [host, selectedTask, applyDraft]);
	// Load latest draft once on mount (removing readMode dependency to avoid spam logs)
	React.useEffect(()=>{ loadLatestDraft(); }, [loadLatestDraft]);
	// Theming
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
	const ease = 'cubic-bezier(0.4, 0, 0.2, 1)';
	const transFast = `transform 220ms ${ease}, box-shadow 220ms ${ease}, background-color 220ms ${ease}, border-color 220ms ${ease}, opacity 220ms ${ease}`;

	return (
		<>
			{!docked && <div style={{ position:'fixed', inset:0, background: scrimBg, zIndex:1999, pointerEvents:'none' }} />}
			<div style={{
				position: docked? 'relative':'fixed',
				right: docked? undefined:24,
				top: docked? undefined:80,
				width: docked? '100%':600,
				height: docked? '100%':640,
				maxHeight: docked? '100%':undefined,
				background: bgPanel,
				backdropFilter: (readMode||liteMode)?'none':'blur(12px)',
				border:`1px solid ${borderCol}`,
				borderRadius: docked? 0:16,
				boxShadow: docked? 'none': glassShadow,
				zIndex: docked? 1:2000,
				display:'flex', flexDirection:'column', overflow:'hidden', transition: transFast
			}}>
					<CalibrationTopBar
					host={host}
					task={selectedTask}
					darkMode={darkMode}
					chipBorder={chipBorder}
					headerBorder={headerBorder}
					textMain={textMain}
					textSub={textSub}
					autoStatus={autoStatus}
					onTaskMenu={()=> setTaskMenuOpen(v=>!v)}
					taskMenuOpen={taskMenuOpen}
					loadTaskSuggestions={loadTaskSuggestions}
					onClear={async ()=>{ try { await fetch(`${BACKEND_URL}/api/calib`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ op:'clear', mapping:{ host, task: selectedTask } }) }); flash('Cleared'); } catch { flash('Error'); } }}
					onToggleLogs={()=> setShowLogs(v=>!v)}
					showLogs={showLogs}
					onClose={onClose}
					docked={docked}
					/>
				{flashMsg && <div style={{ position:'absolute', top:52, right:28, fontSize:12, padding:'6px 10px', borderRadius:999, border:`1px solid ${chipBorder}`, background: darkMode? '#052e2b':'#ccfbf1', color:textMain }}>{flashMsg}</div>}
				<div style={{ padding:12, overflow:'auto', color:textMain }}>
					<div style={{ display:'flex', flexDirection:'column', gap:8, marginBottom:10 }}>
						<div style={{ display:'flex', alignItems:'center', gap:8 }}>
							<div style={{ fontSize:12, color:textSub }}>Host: <b>{host}</b> — Task: <b>{selectedTask}</b></div>
							<div style={{ marginLeft:'auto', fontSize:11, color:textSub }}>Page {Math.max(1, pages.findIndex(p=>p.id===currentPageId)+1)} of {Math.max(1,pages.length||1)}</div>
						</div>
						<div style={{ display:'grid', gridTemplateColumns:'1fr', gap:6 }}>
							<input value={pageName} onChange={e=>setPageName(e.target.value)} placeholder="Page name" style={{ fontSize:12, padding:'8px 10px', background: inputBg, border:`1px solid ${inputBorder}`, borderRadius:10 }} />
							<input value={urlPattern} onChange={e=>setUrlPattern(e.target.value)} placeholder="URL pattern (optional)" style={{ fontSize:12, padding:'8px 10px', background: inputBg, border:`1px solid ${inputBorder}`, borderRadius:10 }} />
							<div style={{ display:'flex', gap:8 }}>
								<input value={urlSample} onChange={e=>setUrlSample(e.target.value)} placeholder="URL sample" style={{ flex:1, fontSize:12, padding:'8px 10px', background: inputBg, border:`1px solid ${inputBorder}`, borderRadius:10 }} />
								<button onClick={handleCaptureUrl} style={{ fontSize:12, padding:'8px 10px', border:`1px solid ${chipBorder}`, borderRadius:10, background:chipBg }}>Capture URL</button>
							</div>
							<div style={{ display:'flex', gap:8 }}>
								<button onClick={handleAddNextPage} style={{ fontSize:12, padding:'8px 10px', border:`1px solid ${chipBorder}`, borderRadius:10, background:chipBg }}>+ Add Next Page</button>
								<button onClick={handleMarkLastPage} style={{ fontSize:12, padding:'8px 10px', border:`1px solid ${chipBorder}`, borderRadius:10, background: darkMode?'#052e2b':'#ccfbf1' }}>Mark Last</button>
							</div>
							<div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>{pages.map((p,i)=> <button key={p.id} onClick={()=>{ commitCurrentPage(); switchToPage(p); }} style={{ fontSize:11, padding:'6px 10px', border:`1px solid ${p.id===currentPageId?'#22d3ee':chipBorder}`, borderRadius:16, background:chipBg }}>{i+1}. {p.name||`Page ${i+1}`}{p.isLast?' (last)':''}</button>)}</div>
							</div>
					</div>
					<div style={{ fontSize:12, color:textSub, marginBottom:8, display:'flex', justifyContent:'space-between', alignItems:'center' }}>
						<span>Ruhsat fields:</span>
						<div style={{ display:'flex', gap:6 }}>
							<button onClick={normalizeAllFields} style={{ fontSize:11, padding:'6px 8px', border:`1px solid ${chipBorder}`, borderRadius:8, background:darkMode?'#1e1b4b':'#e0e7ff' }}>Normalize</button>
							<button onClick={resetAllFields} style={{ fontSize:11, padding:'6px 8px', border:`1px solid ${chipBorder}`, borderRadius:8, background:darkMode?'#3b2f1a':'#fef3c7' }}>Reset</button>
						</div>
					</div>
					<div style={{ display:'flex', gap:8, alignItems:'center', marginBottom:6 }}>
						<input value={fieldFilter} onChange={e=>setFieldFilter(e.target.value)} placeholder="Search field or value" style={{ flex:1, fontSize:11, padding:'6px 8px', background: inputBg, border:`1px solid ${inputBorder}`, borderRadius:8 }} />
						{fieldFilter && <button onClick={()=>setFieldFilter('')} style={{ fontSize:11, padding:'6px 10px', border:`1px solid ${chipBorder}`, borderRadius:8, background: 'transparent', color:textSub }}>Clear</button>}
						<button onClick={()=>{
							setFieldKeys(prev=>{
								const set=new Set(prev);
								for(const k of [...DEFAULT_RUHSAT_KEYS, ...Object.keys(ruhsat||{})]) set.add(k);
								return Array.from(set);
							});
							logInfo('Field list synchronized with defaults + current OCR values');
						}} style={{ fontSize:11, padding:'6px 10px', border:`1px solid ${chipBorder}`, borderRadius:8, background:darkMode?'#1e1b4b':'#e0e7ff' }}>Sync</button>
					</div>
					<FieldsExcelSimple
						fieldKeys={filteredFieldKeys}
							fieldSelectors={fieldSelectors}
						values={ruhsat}
						availableKeys={availableKeys}
							readMode={readMode}
							liteMode={liteMode}
							darkMode={darkMode}
							status={status}
							inputBg={inputBg}
							inputBorder={inputBorder}
							chipBorder={chipBorder}
							headerBorder={headerBorder}
							textSub={textSub}
							onAddField={onAddField}
							onRemoveField={onRemoveField}
							onRenameField={onRenameField}
							handleChange={handleChange}
							addRowEnd={addRowEnd}
							clearRow={clearRow}
							removeRow={removeRow}
							handlePickAssign={handlePickAssign}
							keyIdx={keyIdx}
					/>
					<ExecutionOrderEditor
							executionOrder={executionOrder}
							setExecutionOrder={setExecutionOrder}
							displayedOrder={displayedOrder}
							onDragStart={onDragStart}
							onDragOver={onDragOver}
							onDrop={onDrop}
							chipBorder={chipBorder}
							inputBorder={inputBorder}
							inputBg={inputBg}
							textSub={textSub}
							darkMode={darkMode}
							onPickSelector={async (k:string)=>{ try { const sel = await (window as any).pickSelectorFromWebview?.(); if(sel && typeof sel==='string') setFieldSelectors(prev=>({...prev,[k]: sel})); } catch {} }}
					/>
					<ActionsEditor
						actions={actionsDetail}
						liteMode={liteMode}
						readMode={readMode}
						darkMode={darkMode}
						actStatus={actStatus}
						actPreviews={actPreviews}
						actHtmlSnippets={actHtmlSnippets}
						actOpenHtml={actOpenHtml}
						inputBg={inputBg}
						inputBorder={inputBorder}
						chipBorder={chipBorder}
						textSub={textSub}
						textMain={textMain}
						headerBorder={headerBorder}
						onActionChange={handleActionChange}
						onPick={handlePickAction}
						onShow={handleShowAction}
						onDragStart={onActionDragStart}
						onDrop={onActionDrop}
						onDragOver={onDragOver}
						addAction={addAction}
					/>
					<CriticalFieldsEditor
						criticalFields={criticalFields}
						setCriticalFields={setCriticalFields}
						inputBg={inputBg}
						inputBorder={inputBorder}
						textSub={textSub}
					/>
					<div style={{ marginTop:12, fontSize:11, color:textSub }}>Tip: Pick then click page element; Lite mode speeds editing by removing live checks.</div>
					{showLogs && (
						<LogViewer logs={logs} darkMode={darkMode} headerBorder={headerBorder} inputBorder={inputBorder} textSub={textSub} onClear={clearLogs} />
					)}
				</div>
			</div>
		</>
	);
};

export default CalibrationPanel;
