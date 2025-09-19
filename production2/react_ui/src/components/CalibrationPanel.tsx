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
	// (Old onAddField removed; new duplicate-aware version defined later.)
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
	
	// Rename only a specific occurrence by row index (for individual field freedom)
	const onRenameFieldOccurrence = (rowIdx:number, newK:string) => {
		if(!newK) return;
		setFieldKeys(prev=> {
			const next = [...prev];
			const oldK = next[rowIdx];
			if(oldK === newK) return prev; // no change
			next[rowIdx] = newK;
			logInfo(`Field occurrence renamed: ${oldK} -> ${newK} (row ${rowIdx})`);
			return next;
		});
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
	// Alias management removed. We now treat duplicate field names as separate occurrences.
	// Helper to ensure updating correct occurrence of k when multiple duplicates exist.
	const ensureOccurrence = (k:string, occIdx:number, updater:(arr:string[])=>string[]) => {
		setFieldSelectors(prev=>{
			const cur = prev[k];
			let arr: string[] = Array.isArray(cur)? [...cur] : [String(cur||'')];
			// pad if needed
			while(arr.length <= occIdx) arr.push('');
			arr = updater(arr);
			const cleaned = arr.length===1 ? (arr[0]||'') : arr;
			const next = { ...prev, [k]: cleaned };
			syncFieldSelectorsToPage(next);
			return next;
		});
	};
	const cleanFieldSelectors = (fs: Record<string,string|string[]>) => { const out:Record<string,string|string[]>={}; for(const [k,v] of Object.entries(fs)){ const add=(list:string[])=>{ const seen=new Set<string>(); const dedup:string[]=[]; for(const s of list){ const n=normalizeSelector(s); if(n && !seen.has(n)){ seen.add(n); dedup.push(n);} } if(!dedup.length) return ''; if(dedup.length===1) return dedup[0]; return dedup; }; out[k]=Array.isArray(v)?add(v):add([v]); } return out; };
	const handleChange = (k:string, v:string, occIdx=0) => {
		const norm = normalizeSelector(v);
		ensureOccurrence(k, occIdx, arr=>{ arr[occIdx]=norm; return arr; });
		if(liteMode) return;
		const statusKey=keyIdx(k,occIdx); setStatus(s=>({...s,[statusKey]:norm? 'checking':'unknown'})); const val=norm;
		setTimeout(async ()=>{ const cur=fieldSelectors[k]; const currentVal=Array.isArray(cur)?(cur[occIdx]??''):(occIdx===0?String(cur||''):'' ); if(currentVal!==val) return; if(!val){ setStatus(s=>({...s,[statusKey]:'unknown'})); return;} try { const ok= await (window as any).checkSelectorInWebview?.(val); setStatus(s=>({...s,[statusKey]: ok?'ok':'missing'})); if(ok){ const info= await (window as any).previewSelectorInWebview?.(val); if(info && typeof info==='string') setPreviews(p=>({...p,[statusKey]:info})); const html= await (window as any).getElementHtmlInWebview?.(val,1600); if(html && typeof html==='string') setHtmlSnippets(h=>({...h,[statusKey]:html})); } } catch { setStatus(s=>({...s,[statusKey]:'missing'})); } },220);
	};
	// When adding a field that already exists, we treat it as a new occurrence.
	const onAddField = () => {
		setFieldKeys(prev=>{
			// Just push the first available key (even if duplicate) for fast workflow
			const candidate = availableKeys[0] || 'field';
			const nextKeys = [...prev, candidate];
			// ensure underlying array size for occurrences if duplicate
			const occCount = nextKeys.filter(k=>k===candidate).length - 1; // index of new occ
			ensureOccurrence(candidate, occCount, arr=>{ while(arr.length<=occCount) arr.push(''); return arr; });
			logInfo(`Field occurrence added: ${candidate} (#${occCount+1})`);
			return nextKeys;
		});
	};
	// Remove ALL occurrences of field key from UI and selectors
	const onRemoveFieldWrapper = (k:string) => {
		setFieldKeys(prev=> prev.filter(f=>f!==k));
		setFieldSelectors(fs=>{ const next={...fs}; delete next[k]; syncFieldSelectorsToPage(next); return next; });
		logWarn(`All occurrences removed for field ${k}`);
	};
	// Remove only a single occurrence (occIdx) of field key k
	const removeOccurrence = (k:string, occIdx:number) => {
		setFieldKeys(prev=>{
			// Build new list by walking and skipping only the target occurrence instance
			let seen = 0;
			const next: string[] = [];
			for(const fk of prev){
				if(fk===k){
					if(seen===occIdx){ seen++; continue; } // skip this one
					seen++;
				}
				next.push(fk);
			}
			// Update selector storage array
			setFieldSelectors(fs=>{
				const cur = fs[k];
				if(cur===undefined) return fs; // nothing to do
				let arr = Array.isArray(cur)? [...cur] : [String(cur||'')];
				if(occIdx < arr.length){
					arr.splice(occIdx,1);
				}
				const nextSelectors = { ...fs } as Record<string,string|string[]>;
				if(arr.length===0 || (arr.length===1 && !arr[0])){
					// no meaningful occurrences left -> blank it instead of delete to keep possible future duplicates stable
					nextSelectors[k] = '';
				}else if(arr.length===1){
					nextSelectors[k] = arr[0];
				}else{
					nextSelectors[k] = arr;
				}
				syncFieldSelectorsToPage(nextSelectors);
				return nextSelectors;
			});
			logInfo(`Occurrence removed for ${k} (index ${occIdx})`);
			return next;
		});
	};
	const handlePickAssign = async (k:string, idx=0) => { try { const sel = await (window as any).pickSelectorFromWebview?.(); if(sel && typeof sel==='string'){ handleChange(k, sel, idx); if(!liteMode){ try { const info = await (window as any).previewSelectorInWebview?.(normalizeSelector(sel)); if(info && typeof info==='string') setPreviews(p=>({...p,[keyIdx(k,idx)]:info})); } catch {} } } } catch {} };
	const handleShowField = async (k:string, idx=0) => { const cur=fieldSelectors[k]; const sel=Array.isArray(cur)?(cur[idx]||''):String(cur||''); if(!sel) return; try { const info= await (window as any).previewSelectorInWebview?.(sel); if(!liteMode && info && typeof info==='string') setPreviews(p=>({...p,[keyIdx(k,idx)]:info})); if(!liteMode){ const html= await (window as any).getElementHtmlInWebview?.(sel,1600); if(html && typeof html==='string') setHtmlSnippets(h=>({...h,[keyIdx(k,idx)]:html})); } } catch {} };
	const handleShowElement = async (selector: string, fieldName: string) => { 
		if (!selector.trim()) return; 
		try { 
			// Highlight the element on the page using the provided selector
			await (window as any).highlightElementInWebview?.(selector);
			logInfo(`Highlighting element: ${selector} for field: ${fieldName}`);
		} catch (err) { 
			logWarn(`Could not highlight element: ${selector} for field: ${fieldName}`);
		} 
	};
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

	// IMPORTANT: applyDraft must be defined BEFORE any hooks/callbacks that reference it in their dependency arrays
	// to avoid a runtime "Cannot access 'applyDraft' (minified as 'hn') before initialization" error (TDZ issue).
	const applyDraft = React.useCallback((draft:any, opts?:{preservePage?:boolean; forceReplace?:boolean}) => {
		if(!draft|| typeof draft!=='object') return;
		try {
			const incomingPages = Array.isArray(draft.pages)? draft.pages : [];
			if(incomingPages.length){
				setPages(prev => {
					// Only do smart merge if forceReplace is not set (i.e., during initial load)
					// For explicit Update operations, always replace with server data
					if(!opts?.forceReplace && prev.length > incomingPages.length && incomingPages.length === 1){
						// Update first page data only, keep extra pages (optimistic UI)
						const updated = prev.map((p,i)=> i===0 ? { ...p, ...incomingPages[0] } : p);
						logInfo(`Draft merged (kept ${updated.length} local pages, backend had 1)`);
						return updated;
					}
					logInfo(`Draft with ${incomingPages.length} page(s) applied${opts?.forceReplace ? ' (force replace)' : ''}`);
					return incomingPages;
				});
				const preserve = !!opts?.preservePage;
				if (!preserve) {
					const chosenRaw:any = incomingPages.find(p=>p && p.id===currentPageId) || incomingPages[0];
					const chosen:any = chosenRaw || incomingPages[0];
					if(chosen){
						setCurrentPageId(chosen.id||`p_${Date.now().toString(36)}`);
						setPageName(chosen.name||'Page 1');
						setUrlPattern(chosen.urlPattern||'');
						setUrlSample(chosen.urlSample||'');
						setFieldSelectors(chosen.fieldSelectors||{});
						setFieldKeys(Array.isArray(chosen.fieldKeys)? chosen.fieldKeys : Object.keys(chosen.fieldSelectors||{}));
						setExecutionOrder(Array.isArray(chosen.executionOrder)? chosen.executionOrder : []);
						const actsArr = Array.isArray(chosen.actionsDetail)? chosen.actionsDetail : [];
						setActionsDetail(actsArr.length? actsArr : (Array.isArray(draft.actions)? draft.actions.map((lbl:string,i:number)=>({ id:`a${i+1}`, label:String(lbl), selector:'' })) : [{ id:'a1', label:'Action 1', selector:'' }]));
						setCriticalFields(Array.isArray(chosen.criticalFields)? chosen.criticalFields : (Array.isArray(draft.criticalFields)? draft.criticalFields : criticalFields));
					}
				}
			} else {
				// Single-page legacy shape
				const fs = (draft.fieldSelectors && typeof draft.fieldSelectors==='object')? draft.fieldSelectors : {};
				const fks = Array.isArray(draft.fieldKeys)? draft.fieldKeys : Object.keys(fs);
				const eo = Array.isArray(draft.executionOrder)? draft.executionOrder : [];
				const actsL: string[] = Array.isArray(draft.actions)? draft.actions : [];
				const actsD: any[] = Array.isArray(draft.actionsDetail)? draft.actionsD : (actsL.length? actsL.map((lbl:string,i:number)=>({id:`a${i+1}`, label:String(lbl), selector:''})) : []);
				const crit = Array.isArray(draft.criticalFields)? draft.criticalFields : criticalFields;
				const pgId = `p_${Date.now().toString(36)}`;
				const one:CalibPage = { id:pgId, name:'Page 1', fieldSelectors: fs, fieldKeys: fks, executionOrder: eo, actionsDetail: actsD, criticalFields: crit };
				setPages([one]);
				setCurrentPageId(pgId);
				setPageName(one.name);
				setFieldSelectors(fs);
				setFieldKeys(fks);
				setExecutionOrder(eo);
				setActionsDetail(actsD.length?actsD:[{ id:'a1', label:'Action 1', selector:'' }]);
				setCriticalFields(crit);
				logInfo('Single-page draft applied');
			}
		} catch { logError('Failed applying draft'); }
	}, [criticalFields, currentPageId]);
	const handleSaveInternal = React.useCallback(async ()=>{ const draft = buildDraftPayload(); try { await fetch(`${BACKEND_URL}/api/calib`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ op:'saveDraft', mapping:{ host, task: selectedTask, draft } }) }); flash('Saved'); logInfo(`Draft saved for task ${selectedTask}`); onSaveDraft?.(draft); } catch { flash('Error'); logError(`Save failed for task ${selectedTask}`); } }, [buildDraftPayload, host, selectedTask, onSaveDraft]);
	const handleTestPlanInternal = React.useCallback(async ()=>{ try { await fetch(`${BACKEND_URL}/api/calib`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ op:'testFillPlan', mapping:{ host, task: selectedTask } }) }); flash('Planned'); logInfo(`Test plan triggered for ${selectedTask}`); onTestPlan?.(); } catch { flash('Error'); logError(`Test plan failed for ${selectedTask}`); } }, [host, selectedTask, onTestPlan]);
	const handleFinalizeInternal = React.useCallback(async ()=>{ try { await fetch(`${BACKEND_URL}/api/calib`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ op:'finalizeToConfig', mapping:{ host, task: selectedTask } }) }); flash('Finalized'); logInfo(`Finalize requested for ${selectedTask}`); onFinalize?.(); } catch { flash('Error'); logError(`Finalize failed for ${selectedTask}`); } }, [host, selectedTask, onFinalize]);

	// Manual save mode: remove autosave; expose explicit Save / Finalize / Load buttons
	const [autoStatus, setAutoStatus] = React.useState<'idle'|'saving'|'saved'|'error'>('idle');
	// Keep a snapshot of last pulled/pushed draft for Revert
	const lastPulledRef = React.useRef<any>(null);
	const pushDraft = React.useCallback(async ()=>{
		if(!host || host==='unknown'){ logWarn('Push skipped: missing host'); return; }
		try{
			setAutoStatus('saving');
			commitCurrentPage();
			const draft = buildDraftPayload();
			await fetch(`${BACKEND_URL}/api/calib`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ op:'saveDraft', mapping:{ host, task: selectedTask, draft } }) });
			lastPulledRef.current = JSON.parse(JSON.stringify(draft));
			setAutoStatus('saved');
			flash('Pushed');
			logInfo('Draft pushed to calib.json');
			setTimeout(()=> setAutoStatus('idle'), 1500);
		}catch(e){ setAutoStatus('error'); flash('Push Error'); logError('Push failed'); }
	}, [buildDraftPayload, host, selectedTask, commitCurrentPage]);

	const updateFromServer = React.useCallback(async ()=>{
		try {
			const r= await fetch(`${BACKEND_URL}/api/calib`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ op:'load', mapping:{ host, task: selectedTask } }) });
			const j= await r.json();
			if(j?.ok && j?.data){
				applyDraft(j.data, { preservePage:false, forceReplace: true });
				lastPulledRef.current = JSON.parse(JSON.stringify(j.data));
				flash('Updated');
				logInfo('Pulled draft from calib.json (complete replace)');
			}else{
				flash('No Data'); logWarn('No draft on server');
			}
		}catch{ flash('Update Error'); logError('Update failed'); }
	}, [host, selectedTask, applyDraft]);

	const revertToLastPulled = React.useCallback(()=>{
		const snap = lastPulledRef.current;
		if(!snap){ flash('No revert point'); logWarn('No last pulled snapshot'); return; }
		applyDraft(snap, { preservePage:false, forceReplace: true });
		flash('Reverted');
		logInfo('Local state reverted to last pulled snapshot (complete replace)');
	}, [applyDraft]);

	// Memo current draft snapshot for render-safe usage (avoid calling buildDraftPayload inside JSX repeatedly)
	const currentDraft = React.useMemo(()=> buildDraftPayload(), [buildDraftPayload]);
	const handleAddNextPage = () => {
		// Build/commit current page inline using freshest state to avoid stale closure issues
		setPages(prev => {
			const existingIdx = prev.findIndex(p=>p.id===currentPageId);
			const cleaned = cleanFieldSelectors(fieldSelectors);
			const current: CalibPage = {
				id: currentPageId,
				name: pageName,
				urlPattern,
				urlSample,
				fieldSelectors: cleaned,
				fieldKeys: fieldKeys.slice(),
				executionOrder: executionOrder.slice(),
				actionsDetail: actionsDetail.slice(),
				criticalFields: criticalFields.slice(),
				isLast: prev[existingIdx]?.isLast
			};
			let base = existingIdx>=0 ? prev.map(p=> p.id===current.id? current : p) : [...prev, current];
			const newId = `p_${Date.now().toString(36)}`;
			const newPageName = `Page ${base.length+1}`; // after adding current (maybe) base length is page count so next index = length+1
			const newPage: CalibPage = {
				id: newId,
				name: newPageName,
				urlPattern: '',
				urlSample: '',
				fieldSelectors: {},
				fieldKeys: [],
				executionOrder: [],
				actionsDetail: [{ id: 'a1', label: 'Action 1', selector: ''}],
				criticalFields: criticalFields.slice(),
				isLast: false
			};
			// Update local state for new page (outside setPages via side-effects after return)
			setCurrentPageId(newPage.id);
			setPageName(newPage.name);
			setUrlPattern('');
			setUrlSample('');
			setFieldSelectors({});
			setFieldKeys([]);
			setExecutionOrder([]);
			setActionsDetail([{ id: 'a1', label: 'Action 1', selector: '' }]);
			// Try capturing URL asynchronously (non-blocking)
			getDomAndUrlFromWebview().then(info=>{ try { setUrlSample(info.url||''); } catch {} }).catch(()=>{});
			logInfo(`Added ${newPage.name} (ID ${newPage.id}) - local only (push with Save)`);
			return [...base, newPage];
		});
	};

	// New function: Delete individual page
	const handleDeletePage = async (pageId: string) => {
		if (pages.length <= 1) {
			logWarn('Cannot delete the last page');
			return;
		}
		
		const pageToDelete = pages.find(p => p.id === pageId);
		if (!pageToDelete) return;
		
		// Remove the page from array
		const updatedPages = pages.filter(p => p.id !== pageId);
		
		// Renumber remaining pages
		const renumberedPages = updatedPages.map((p, index) => ({
			...p,
			name: `Page ${index + 1}`
		}));
		
		setPages(renumberedPages);
		
		// If we deleted the current page, switch to first page
		if (currentPageId === pageId) {
			const firstPage = renumberedPages[0];
			setCurrentPageId(firstPage.id);
			setPageName(firstPage.name);
			setUrlPattern(firstPage.urlPattern || '');
			setUrlSample(firstPage.urlSample || '');
			setFieldSelectors(firstPage.fieldSelectors || {});
			setFieldKeys(firstPage.fieldKeys || []);
			setExecutionOrder(firstPage.executionOrder || []);
			setActionsDetail(firstPage.actionsDetail || [{ id: 'a1', label: 'Action 1', selector: '' }]);
		}
		
		// LOCAL ONLY - no automatic save, wait for Push button
		logInfo(`${pageToDelete.name} deleted - local only (push to save)`);
	};
	const handleMarkLastPage = () => { const committed = commitCurrentPage({ isLast:true }); logInfo(`Marked page as last: ${committed.name}`); setPages(prev=> prev.map(p=> p.id===committed.id ? { ...committed, isLast:true } : p)); };
	const handleCaptureUrl = async () => { const info= await getDomAndUrlFromWebview(); setUrlSample(info.url||''); };
	const onDragStart = (i:number)=> setDragIdx(i); const onDragOver=(e:React.DragEvent)=> e.preventDefault(); const onDrop=(i:number)=>{ if(dragIdx===null) return; const arr=[...displayedOrder]; const [item]=arr.splice(dragIdx,1); arr.splice(i,0,item); setExecutionOrder(arr); setDragIdx(null); };
	// Actions helpers & validation (skip if liteMode)
	const syncActionsToPage = (next:ActionItem[]) => setPages(prev=> prev.map(p=> p.id===currentPageId ? { ...p, actionsDetail: next } : p));
	const handleActionChange = (id:string, field:'label'|'selector', value:string) => { setActionsDetail(prev=>{ const next = prev.map(a=> a.id===id ? { ...a, [field]: value } : a); syncActionsToPage(next); return next; }); if(field==='label') logInfo(`Action label changed (${id}) => ${value}`); if(field==='selector') logInfo(`Action selector changed (${id})`); if(field==='selector' && !liteMode){ setActStatus(s=>({...s,[id]: value? 'checking':'unknown'})); const current=value; setTimeout(async ()=>{ const still = actionsDetail.find(a=>a.id===id)?.selector || ''; if(still!==current) return; if(!current){ setActStatus(s=>({...s,[id]:'unknown'})); return;} try { const ok= await (window as any).checkSelectorInWebview?.(current); setActStatus(s=>({...s,[id]: ok?'ok':'missing'})); if(ok){ const info= await (window as any).previewSelectorInWebview?.(current); if(info && typeof info==='string') setActPreviews(p=>({...p,[id]:info})); const html= await (window as any).getElementHtmlInWebview?.(current,1600); if(html && typeof html==='string') setActHtmlSnippets(h=>({...h,[id]:html})); } } catch { setActStatus(s=>({...s,[id]:'missing'})); } },200); } };
	const handlePickAction = async (id:string) => { try { const sel = await (window as any).pickSelectorFromWebview?.(); if(sel && typeof sel==='string'){ handleActionChange(id,'selector',sel); if(!liteMode){ try { const info= await (window as any).previewSelectorInWebview?.(sel); if(info && typeof info==='string') setActPreviews(p=>({...p,[id]:info})); } catch {} } } } catch {} };
	const handleShowAction = async (id:string) => { const cur=actionsDetail.find(a=>a.id===id)?.selector||''; if(!cur) return; try { const info= await (window as any).previewSelectorInWebview?.(cur); if(!liteMode && info && typeof info==='string') setActPreviews(p=>({...p,[id]:info})); if(!liteMode){ const html= await (window as any).getElementHtmlInWebview?.(cur,1600); if(html && typeof html==='string') setActHtmlSnippets(h=>({...h,[id]:html})); } } catch {} };
	const addAction = () => { const idx=actionsDetail.length+1; const id=`a${Date.now().toString(36)}_${idx}`; setActionsDetail(prev=>{ const next=[...prev,{ id, label:`Action ${idx}`, selector:'' }]; syncActionsToPage(next); logInfo(`Action added (${id})`); return next; }); };
	const deleteAction = (id:string) => { setActionsDetail(prev=>{ const next=prev.filter(a=>a.id!==id); syncActionsToPage(next); logInfo(`Action deleted (${id})`); return next; }); };
	const onActionDragStart=(i:number)=> setActDragIdx(i); const onActionDrop=(i:number)=>{ if(actDragIdx===null) return; const arr=[...actionsDetail]; const [item]=arr.splice(actDragIdx,1); arr.splice(i,0,item); setActionsDetail(arr); syncActionsToPage(arr); setActDragIdx(null); };
	
	// Use ref to avoid dependency cycles that cause excessive applyDraft calls
	const applyDraftRef = React.useRef(applyDraft);
	applyDraftRef.current = applyDraft;
	React.useEffect(()=>{ 
		if(existingDraft) {
			logInfo('Applying existingDraft (initial load only)');
			applyDraftRef.current(existingDraft); 
		}
	}, [existingDraft]); // Only depend on existingDraft, not applyDraft
	const lastLoadRef = React.useRef<number>(0);
	const loadLatestDraft = React.useCallback(async ()=>{ 
		try { 
			const now=Date.now(); 
			if(now - lastLoadRef.current < 500) return; 
			lastLoadRef.current = now; 
			
			const r= await fetch(`${BACKEND_URL}/api/calib`, { 
				method:'POST', 
				headers:{'Content-Type':'application/json'}, 
				body: JSON.stringify({ op:'load', mapping:{ host, task: selectedTask } }) 
			}); 
			const j= await r.json(); 
			
			if(j?.ok && j?.data){ 
				// COMPLETE RESET: Apply draft data from calib.json as single source of truth
				applyDraft(j.data, {preservePage: false}); // Force reset, don't preserve page
				logInfo('Latest draft loaded from calib.json - complete reset'); 
			} else { 
				// calib.json is empty or no data - reset to single blank page
				logWarn('No draft found in calib.json - resetting to blank state');
				const cleanPageId = `p_${Date.now().toString(36)}`;
				const cleanPage: CalibPage = {
					id: cleanPageId,
					name: 'Page 1',
					urlPattern: '',
					urlSample: '',
					fieldSelectors: {},
					fieldKeys: [],
					executionOrder: [],
					actionsDetail: [{ id: 'a1', label: 'Action 1', selector: '' }],
					criticalFields: [],
					isLast: false
				};
				
				// COMPLETE STATE RESET
				setPages([cleanPage]);
				setCurrentPageId(cleanPageId);
				setPageName('Page 1');
				setUrlPattern('');
				setUrlSample('');
				setFieldSelectors({});
				setFieldKeys([]);
				setExecutionOrder([]);
				setActionsDetail([{ id: 'a1', label: 'Action 1', selector: '' }]);
				setCriticalFields([]);
				
				logInfo('Reset to single blank Page 1 - no data in calib.json');
			} 
		} catch { 
			logError('Error loading latest draft'); 
		} 
	}, [host, selectedTask, applyDraft]);
	// REMOVED: Auto-loading on mount to prevent page switching issues
	// React.useEffect(()=>{ loadLatestDraft(); }, [loadLatestDraft]);
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
						statusLabel={autoStatus==='saving'? 'Saving': autoStatus==='saved'? 'Saved': autoStatus==='error'? 'Error':'Manual'}
						onTaskMenu={()=> setTaskMenuOpen(v=>!v)}
						taskMenuOpen={taskMenuOpen}
						loadTaskSuggestions={loadTaskSuggestions}
						onPush={pushDraft}
						onUpdate={updateFromServer}
						onClear={async ()=>{ 
						try { 
							logInfo('Manual clear: clearing backend AND frontend completely');
							
							// Clear backend
							await fetch(`${BACKEND_URL}/api/calib`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ op:'clear', mapping:{ host, task: selectedTask } }) }); 
							
							// COMPLETE FRONTEND RESET - ignore any cached data
							const cleanPageId = `p_${Date.now().toString(36)}`;
							const cleanPage: CalibPage = {
								id: cleanPageId,
								name: 'Page 1',
								urlPattern: '',
								urlSample: '',
								fieldSelectors: {},
								fieldKeys: [],
								executionOrder: [],
								actionsDetail: [{ id: 'a1', label: 'Action 1', selector: '' }],
								criticalFields: [],
								isLast: false
							};
							
							// Reset ALL state completely
							setPages([cleanPage]);
							setCurrentPageId(cleanPageId);
							setPageName('Page 1');
							setUrlPattern('');
							setUrlSample('');
							setFieldSelectors({});
							setFieldKeys([]);
							setExecutionOrder([]);
							setActionsDetail([{ id: 'a1', label: 'Action 1', selector: '' }]);
							setCriticalFields([]);
							
							// Clear any additional caches
							setPreviews({});
							setStatus({});
							setHtmlSnippets({});
							setActPreviews({});
							setActStatus({});
							setActHtmlSnippets({});
							
							flash('Cleared - both backend and frontend reset'); 
							logInfo('Complete clear: backend + frontend reset to single Page 1');
						} catch { 
							flash('Clear error'); 
							logError('Clear operation failed');
						} 
					}}
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
						{/* Manual Save / Load Controls */}
						{/* Legacy save/load buttons removed: Push/Update/Revert now in top bar */}
						<div style={{ display:'grid', gridTemplateColumns:'1fr', gap:6 }}>
							<input value={urlPattern} onChange={e=>setUrlPattern(e.target.value)} placeholder="URL pattern (optional)" style={{ fontSize:12, padding:'8px 10px', background: inputBg, border:`1px solid ${inputBorder}`, borderRadius:10 }} />
							<div style={{ display:'flex', gap:8 }}>
								<input value={urlSample} onChange={e=>setUrlSample(e.target.value)} placeholder="URL sample" style={{ flex:1, fontSize:12, padding:'8px 10px', background: inputBg, border:`1px solid ${inputBorder}`, borderRadius:10 }} />
								<button onClick={handleCaptureUrl} style={{ fontSize:12, padding:'8px 10px', border:`1px solid ${chipBorder}`, borderRadius:10, background:chipBg }}>Capture URL</button>
							</div>
							<div style={{ display:'flex', gap:8 }}>
								<button onClick={handleAddNextPage} style={{ fontSize:12, padding:'8px 10px', border:`1px solid ${chipBorder}`, borderRadius:10, background:chipBg }}>+ Add Next Page</button>
								<button onClick={handleMarkLastPage} style={{ fontSize:12, padding:'8px 10px', border:`1px solid ${chipBorder}`, borderRadius:10, background: darkMode?'#052e2b':'#ccfbf1' }}>Mark Last</button>
							</div>
							<div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
								{pages.map((p,i)=> (
									<div key={p.id} style={{ display:'flex', alignItems:'center', gap:2 }}>
										<button 
											onClick={()=>{ logInfo(`Page click: switching to ${p.name} (${p.id}), current=${currentPageId}`); commitCurrentPage(); switchToPage(p); }} 
											style={{ fontSize:11, padding:'6px 10px', border:`1px solid ${p.id===currentPageId?'#22d3ee':chipBorder}`, borderRadius:16, background:chipBg }}
										>
											{i+1}. {p.name||`Page ${i+1}`}{p.isLast?' (last)':''}
										</button>
										{pages.length > 1 && (
											<button 
												onClick={(e) => { e.stopPropagation(); handleDeletePage(p.id); }} 
												style={{ fontSize:10, padding:'4px 6px', border:`1px solid #dc2626`, borderRadius:12, background:'#dc2626', color:'white', cursor:'pointer' }}
												title={`Delete ${p.name}`}
											>
												×
											</button>
										)}
									</div>
								))}
							</div>
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
							// Sync field keys
							setFieldKeys(prev=>{
								const set=new Set(prev);
								for(const k of [...DEFAULT_RUHSAT_KEYS, ...Object.keys(ruhsat||{})]) set.add(k);
								return Array.from(set);
							});
							// Auto-populate critical fields from available data
							setCriticalFields(prev=>{
								const availableFields = [...DEFAULT_RUHSAT_KEYS, ...Object.keys(ruhsat||{})];
								// Use Set to ensure no duplicates - combine existing and new fields
								const combinedFields = new Set([...prev, ...availableFields]);
								return Array.from(combinedFields);
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
						onRemoveOccurrence={removeOccurrence}
						onRenameField={onRenameField}
						onRenameFieldOccurrence={onRenameFieldOccurrence}
						handleChange={handleChange}
						handlePickAssign={handlePickAssign}
						handleShowElement={handleShowElement}
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
						deleteAction={deleteAction}
					/>
					<CriticalFieldsEditor
						criticalFields={criticalFields}
						setCriticalFields={setCriticalFields}
						availableFields={availableKeys}
						inputBg={inputBg}
						inputBorder={inputBorder}
						chipBorder={chipBorder}
						textSub={textSub}
						darkMode={darkMode}
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
