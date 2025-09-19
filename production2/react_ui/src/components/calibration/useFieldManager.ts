import { useState, useMemo, useCallback } from 'react';

// Standard ruhsat fields for static heuristic mapping
const DEFAULT_RUHSAT_KEYS = [
	'plaka_no','marka','model','model_yili','sasi_no','motor_no','yakit','renk'
];

export interface FieldManagerOptions {
	ruhsat: Record<string, string>;
	logInfo: (msg: string) => void;
	logWarn: (msg: string) => void;
	logError: (msg: string) => void;
	liteMode: boolean;
}

export const useFieldManager = (options: FieldManagerOptions) => {
	const { ruhsat, logInfo, logWarn, logError, liteMode } = options;
	
	const [fieldKeys, setFieldKeys] = useState<string[]>(() => Object.keys(ruhsat || {}));
	const [fieldSelectors, setFieldSelectors] = useState<Record<string, string | string[]>>(() => {
		const init: Record<string, string | string[]> = {};
		for (const k of Object.keys(ruhsat || {})) init[k] = '';
		return init;
	});
	
	// Status and preview states (only used when not in lite mode)
	const [status, setStatus] = useState<Record<string, 'unknown' | 'checking' | 'ok' | 'missing'>>({});
	const [previews, setPreviews] = useState<Record<string, string>>({});
	const [htmlSnippets, setHtmlSnippets] = useState<Record<string, string>>({});
	const [openHtml, setOpenHtml] = useState<Record<string, boolean>>({});

	// Available keys for field selection
	const availableKeys = useMemo(() => {
		const used = new Set(fieldKeys);
		const candidates = Object.keys(ruhsat || {});
		const missing = DEFAULT_RUHSAT_KEYS.filter(k => !used.has(k));
		const extra = candidates.filter(k => !used.has(k) && !DEFAULT_RUHSAT_KEYS.includes(k));
		return [...missing, ...extra];
	}, [fieldKeys, ruhsat]);

	// Utility functions
	const keyIdx = useCallback((k: string, idx: number) => `${k}::${idx}`, []);
	
	const focusFieldRow = useCallback((k: string, idx: number) => { 
		try { 
			document.querySelector<HTMLInputElement>(`input[data-field="${k}"][data-idx="${idx}"]`)?.focus(); 
		} catch {} 
	}, []);

	const normalizeSelector = useCallback((s: string) => {
		if (!s) return '';
		const clean = s.trim();
		if (!clean) return '';
		const parts = clean.split(/\s*,\s*/).filter(Boolean);
		return parts.length === 1 ? parts[0] : parts.join(', ');
	}, []);

	const clearCachesForField = useCallback((k: string) => {
		if (liteMode) return; // skip heavy cleanup in lite
		const pref = `${k}::`;
		setStatus(s => { const n: any = {}; for (const [kk, v] of Object.entries(s)) if (!kk.startsWith(pref)) n[kk] = v; return n; });
		setPreviews(p => { const n: any = {}; for (const [kk, v] of Object.entries(p)) if (!kk.startsWith(pref)) n[kk] = v; return n; });
		setHtmlSnippets(h => { const n: any = {}; for (const [kk, v] of Object.entries(h)) if (!kk.startsWith(pref)) n[kk] = v; return n; });
		setOpenHtml(o => { const n: any = {}; for (const [kk, v] of Object.entries(o)) if (!kk.startsWith(pref)) n[kk] = v; return n; });
	}, [liteMode]);

	// Field operations
	const onAddField = useCallback(() => {
		const used = new Set(fieldKeys);
		const nextKey = availableKeys.find(k => !used.has(k));
		if (nextKey) {
			setFieldKeys(prev => [...prev, nextKey]);
			setFieldSelectors(prev => ({ ...prev, [nextKey]: '' }));
			logInfo(`Field added: ${nextKey}`);
		}
	}, [fieldKeys, availableKeys, logInfo]);

	const onRemoveField = useCallback((k: string) => {
		setFieldKeys(prev => prev.filter(fk => fk !== k));
		setFieldSelectors(prev => { const next = { ...prev }; delete next[k]; return next; });
		clearCachesForField(k);
		logInfo(`Field removed: ${k}`);
	}, [clearCachesForField, logInfo]);

	const onRenameField = useCallback((oldK: string, newK: string) => {
		if (!newK || oldK === newK) return;
		setFieldKeys(prev => prev.map(k => k === oldK ? newK : k));
		setFieldSelectors(fs => { 
			const next: typeof fs = {}; 
			for (const [k, v] of Object.entries(fs)) { 
				next[k === oldK ? newK : k] = v; 
			} 
			return next; 
		});
		
		// Migrate validation caches
		if (!liteMode) {
			setStatus(s => { 
				const n: typeof s = {}; 
				for (const [k, v] of Object.entries(s)) { 
					if (k.startsWith(oldK + '::')) { 
						const idx = k.split('::')[1]; 
						n[newK + '::' + idx] = v; 
					} else n[k] = v; 
				} 
				return n; 
			});
			setPreviews(p => { 
				const n: typeof p = {}; 
				for (const [k, v] of Object.entries(p)) { 
					if (k.startsWith(oldK + '::')) { 
						const idx = k.split('::')[1]; 
						n[newK + '::' + idx] = v; 
					} else n[k] = v; 
				} 
				return n; 
			});
			setHtmlSnippets(h => { 
				const n: typeof h = {}; 
				for (const [k, v] of Object.entries(h)) { 
					if (k.startsWith(oldK + '::')) { 
						const idx = k.split('::')[1]; 
						n[newK + '::' + idx] = v; 
					} else n[k] = v; 
				} 
				return n; 
			});
			setOpenHtml(o => { 
				const n: typeof o = {}; 
				for (const [k, v] of Object.entries(o)) { 
					if (k.startsWith(oldK + '::')) { 
						const idx = k.split('::')[1]; 
						n[newK + '::' + idx] = v; 
					} else n[k] = v; 
				} 
				return n; 
			});
		}
		logInfo(`Field renamed: ${oldK} -> ${newK}`);
	}, [liteMode, logInfo]);

	// Field selector operations
	const addRowEnd = useCallback((k: string) => {
		setFieldSelectors(prev => { 
			const cur = prev[k]; 
			const arr = Array.isArray(cur) ? [...cur] : [String(cur || '')]; 
			arr.push(''); 
			const next = { ...prev, [k]: arr }; 
			setTimeout(() => focusFieldRow(k, arr.length - 1), 0); 
			logInfo(`Alias added (end) for ${k}; total=${arr.length}`); 
			return next; 
		});
	}, [focusFieldRow, logInfo]);

	const insertRowAfter = useCallback((k: string, idx: number) => {
		setFieldSelectors(prev => { 
			const cur = prev[k]; 
			const arr = Array.isArray(cur) ? [...cur] : [String(cur || '')]; 
			const at = Math.max(0, Math.min(idx + 1, arr.length)); 
			arr.splice(at, 0, ''); 
			const next = { ...prev, [k]: arr }; 
			setTimeout(() => focusFieldRow(k, at), 0); 
			logInfo(`Alias inserted after index ${idx} for ${k}; total=${arr.length}`); 
			return next; 
		});
	}, [focusFieldRow, logInfo]);

	const clearRow = useCallback((k: string, _idx: number) => { 
		setFieldSelectors(prev => { 
			const next = { ...prev, [k]: [''] }; 
			clearCachesForField(k); 
			logInfo(`Field ${k} cleared (aliases collapsed to one empty)`); 
			return next; 
		}); 
	}, [clearCachesForField, logInfo]);

	const removeRow = useCallback((k: string, idx: number) => {
		setFieldSelectors(prev => {
			const cur = prev[k];
			let arr = Array.isArray(cur) ? [...cur] : [String(cur || '')];
			if (arr.length <= 1) {
				// Only one alias: blank it instead of removing field
				arr = [''];
				logWarn(`Single alias cleared for ${k}`);
			} else {
				if (idx >= 0 && idx < arr.length) { arr.splice(idx, 1); }
				logInfo(`Alias ${idx} removed for ${k}; remaining=${arr.length}`);
			}
			clearCachesForField(k);
			const next = { ...prev, [k]: arr };
			return next;
		});
	}, [clearCachesForField, logWarn, logInfo]);

	const moveRow = useCallback((k: string, idx: number, dir: -1 | 1) => {
		setFieldSelectors(prev => { 
			const cur = prev[k]; 
			const arr = Array.isArray(cur) ? [...cur] : [String(cur || '')]; 
			const to = idx + dir; 
			if (to < 0 || to >= arr.length) return prev; 
			[arr[idx], arr[to]] = [arr[to], arr[idx]]; 
			clearCachesForField(k); 
			setTimeout(() => focusFieldRow(k, to), 0); 
			const next = { ...prev, [k]: arr }; 
			logInfo(`Alias moved for ${k}: ${idx} -> ${to}`); 
			return next; 
		});
	}, [clearCachesForField, focusFieldRow, logInfo]);

	const handleChange = useCallback((k: string, v: string, idx = 0) => {
		const norm = normalizeSelector(v);
		setFieldSelectors(prev => { 
			const cur = prev[k]; 
			if (Array.isArray(cur)) { 
				const arr = [...cur]; 
				arr[idx] = norm; 
				const next = { ...prev, [k]: arr }; 
				return next;
			} 
			if (idx > 0) { 
				const base = String(cur || ''); 
				const pad = Array(Math.max(0, idx - 1)).fill(''); 
				const next = { ...prev, [k]: [base, ...pad, norm] }; 
				return next;
			} 
			const next = { ...prev, [k]: norm }; 
			return next; 
		});
		
		if (liteMode) return;
		
		// Live validation (only in non-lite mode)
		const statusKey = keyIdx(k, idx); 
		setStatus(s => ({ ...s, [statusKey]: norm ? 'checking' : 'unknown' })); 
		const val = norm;
		setTimeout(async () => { 
			const cur = fieldSelectors[k]; 
			const currentVal = Array.isArray(cur) ? (cur[idx] ?? '') : (idx === 0 ? String(cur || '') : ''); 
			if (currentVal !== val) return; 
			if (!val) { 
				setStatus(s => ({ ...s, [statusKey]: 'unknown' })); 
				return;
			} 
			try { 
				const ok = await (window as any).checkSelectorInWebview?.(val); 
				setStatus(s => ({ ...s, [statusKey]: ok ? 'ok' : 'missing' })); 
				if (ok) { 
					const info = await (window as any).previewSelectorInWebview?.(val); 
					if (info && typeof info === 'string') setPreviews(p => ({ ...p, [statusKey]: info })); 
					const html = await (window as any).getElementHtmlInWebview?.(val, 1600); 
					if (html && typeof html === 'string') setHtmlSnippets(h => ({ ...h, [statusKey]: html })); 
				} 
			} catch { 
				setStatus(s => ({ ...s, [statusKey]: 'missing' })); 
			} 
		}, 220);
	}, [normalizeSelector, liteMode, keyIdx, fieldSelectors]);

	const cleanFieldSelectors = useCallback((fs: Record<string, string | string[]>) => { 
		const out: Record<string, string | string[]> = {}; 
		for (const [k, v] of Object.entries(fs)) { 
			const add = (list: string[]) => { 
				const seen = new Set<string>(); 
				const dedup: string[] = []; 
				for (const s of list) { 
					const n = normalizeSelector(s); 
					if (n && !seen.has(n)) { 
						seen.add(n); 
						dedup.push(n);
					} 
				} 
				if (!dedup.length) return ''; 
				if (dedup.length === 1) return dedup[0]; 
				return dedup; 
			}; 
			out[k] = Array.isArray(v) ? add(v) : add([v]); 
		} 
		return out; 
	}, [normalizeSelector]);

	const normalizeAllFields = useCallback(() => {
		setFieldSelectors(prev => {
			const cleaned = cleanFieldSelectors(prev);
			logInfo('All field selectors normalized');
			return cleaned;
		});
	}, [cleanFieldSelectors, logInfo]);

	const resetAllFields = useCallback(() => {
		const reset: Record<string, string> = {};
		for (const k of fieldKeys) reset[k] = '';
		setFieldSelectors(reset);
		if (!liteMode) {
			setStatus({});
			setPreviews({});
			setHtmlSnippets({});
		}
		logInfo('All fields reset to empty');
	}, [fieldKeys, liteMode, logInfo]);

	return {
		// State
		fieldKeys,
		fieldSelectors,
		availableKeys,
		status,
		previews,
		htmlSnippets,
		openHtml,
		
		// Setters
		setFieldKeys,
		setFieldSelectors,
		setStatus,
		setPreviews,
		setHtmlSnippets,
		setOpenHtml,
		
		// Operations
		onAddField,
		onRemoveField,
		onRenameField,
		addRowEnd,
		insertRowAfter,
		clearRow,
		removeRow,
		moveRow,
		handleChange,
		cleanFieldSelectors,
		normalizeAllFields,
		resetAllFields,
		clearCachesForField,
		
		// Utilities
		keyIdx,
		focusFieldRow,
		normalizeSelector,
	};
};