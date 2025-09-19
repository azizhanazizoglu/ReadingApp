import { useState, useCallback } from 'react';

export interface PickingState {
	type: 'field' | 'action';
	key: string;
	index?: number;
	id?: string;
}

export interface PickingHandlerOptions {
	logInfo: (msg: string) => void;
	logWarn: (msg: string) => void;
	logError: (msg: string) => void;
}

export const usePickingHandler = (options: PickingHandlerOptions) => {
	const { logInfo, logWarn, logError } = options;
	const [activePicking, setActivePicking] = useState<PickingState | null>(null);

	// Start iframe picking mode with green selection areas
	const startIframePickingMode = useCallback(async () => {
		console.log('🔍 Starting iframe picking mode...');
		
		// Check webview availability with detailed logging
		const webview = (window as any).getWebview ? (window as any).getWebview() : null;
		console.log('🌐 Webview availability check:', {
			hasGetWebview: !!(window as any).getWebview,
			webview: !!webview,
			webviewType: typeof webview,
			hasExecuteJavaScript: webview && typeof webview.executeJavaScript === 'function'
		});
		
		if (!webview) {
			console.warn('❌ No webview found - picking mode cannot be activated');
			logWarn('No webview found - picking mode cannot be activated');
			return;
		}
		
		console.log('✅ Webview found, injecting picking script...');
		
		try {
			const script = `(() => {
				console.log('🎯 Iframe picking script starting...');
				try {
					// Clean up any existing picking state
					if (window.__PICKING_CLEANUP__) {
						console.log('🧹 Cleaning up existing picking state...');
						window.__PICKING_CLEANUP__();
						delete window.__PICKING_CLEANUP__;
					}
					
					// Clear any existing picked selector
					delete window.__PICK_SEL__;
					if (window.top) delete window.top.__PICK_SEL__;
					
					const docs = [document, ...Array.from(document.querySelectorAll('iframe')).map(f=>{ 
						try{ return f.contentDocument || (f.contentWindow&&f.contentWindow.document) }catch(e){ return null } 
					}).filter(Boolean)];
					
					console.log('📄 Found', docs.length, 'documents to overlay');
					
					const overlays = [];
					const state = { lastEl: null, lastDoc: document, lastSelector: null, hoverCount: 0, locked: false };
					
					// Store state globally so Done button can access it
					window.__PICKING_STATE__ = state;
					
					const buildDomPath = (el) => {
						if(!el) return '';
						const parts=[]; let cur=el; let depth=0;
						while(cur && cur.nodeType===1 && depth<6){
							let seg = cur.tagName.toLowerCase();
							if(cur.id){ seg += '#'+cur.id; parts.unshift(seg); break; }
							if(cur.className && typeof cur.className==='string'){
								const c = cur.className.trim().split(/\\s+/).filter(Boolean)[0];
								if(c) seg += '.'+c;
							}
							const parent = cur.parentElement;
							if(parent){
								const sibs = Array.from(parent.children).filter(s=>s.tagName===cur.tagName);
								if(sibs.length>1) seg += ':nth-of-type('+(sibs.indexOf(cur)+1)+')';
							}
							parts.unshift(seg); cur = cur.parentElement; depth++;
						}
						return parts.join(' > ');
					};
					
					const makeOverlay = (DOC) => {
						console.log('🎨 Creating overlay for document:', DOC.location?.href || 'main document');
						
						const overlay = DOC.createElement('div');
						// pointer-events:none so we don't block elementFromPoint; use outline box only
						overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;z-index:2147483645;pointer-events:none;background:rgba(0,255,0,0.04);';
						overlay.setAttribute('data-picking-overlay', 'true');
						
						const box = DOC.createElement('div');
						box.style.cssText = 'position:absolute;border:3px solid #10b981;background:rgba(16,185,129,0.2);pointer-events:none;display:none;';
						box.setAttribute('data-picking-box', 'true');
						overlay.appendChild(box);
						
						// Add visual indicator
						const indicator = DOC.createElement('div');
						indicator.style.cssText = 'position:fixed;top:10px;left:10px;background:#10b981;color:white;padding:8px 12px;border-radius:4px;font-size:14px;font-weight:bold;z-index:2147483647;';
						indicator.textContent = '🎯 PICKING MODE - Hover elements (click to lock)';
						indicator.setAttribute('data-picking-indicator', 'true');
						
						DOC.body.appendChild(overlay);
						DOC.body.appendChild(indicator);
						
						const simpleSelector = (el) => {
							if(!el) return '';
							if(el.id) return '#' + el.id;
							if(el.className && typeof el.className==='string') {
								const c = el.className.trim().split(/\\s+/).filter(Boolean)[0];
								if(c) return '.'+c;
							}
							const tag = el.tagName.toLowerCase();
							const parent = el.parentElement;
							if(parent){
								const sibs = Array.from(parent.children).filter(s=>s.tagName===el.tagName);
								if(sibs.length>1){
									return tag + ':nth-of-type(' + (sibs.indexOf(el)+1) + ')';
								}
							}
							return tag;
						};
						const move = (ev) => {
							if(state.locked) return; // do not update while locked
							try {
								const el = DOC.elementFromPoint(ev.clientX, ev.clientY);
								if(!el) return;
								if (el === overlay || el === box || el === indicator) return;
								state.lastEl = el;
								state.lastDoc = DOC;
								state.hoverCount++;
								state.lastSelector = simpleSelector(el);
								const r = el.getBoundingClientRect();
								box.style.left = r.left + 'px';
								box.style.top = r.top + 'px';
								box.style.width = r.width + 'px';
								box.style.height = r.height + 'px';
								box.style.display = 'block';
								indicator.textContent = '🎯 ' + state.lastSelector + ' ('+state.hoverCount+')';
								indicator.setAttribute('data-last-path', buildDomPath(el));
							} catch(e){ console.warn('mousemove err', e); }
						};
						const click = (ev) => {
							try {
								const el = DOC.elementFromPoint(ev.clientX, ev.clientY);
								if(!el) return;
								state.locked = !state.locked; // toggle lock
								indicator.style.background = state.locked? '#065f46' : '#10b981';
								indicator.textContent = (state.locked? '🔒 ': '🎯 ') + state.lastSelector + (state.locked? ' [locked]' : '');
							} catch(e){ console.warn('click err', e); }
						};
						DOC.addEventListener('mousemove', move, true);
						DOC.addEventListener('click', click, true);
						overlays.push({ DOC, overlay, move, click, box, indicator });
					};
					
					// Setup cleanup function
					window.__PICKING_CLEANUP__ = () => {
						console.log('🧹 Cleaning up picking overlays...');
						for (const o of overlays) {
							try { o.DOC.removeEventListener('mousemove', o.move, true); } catch {}
							try { o.DOC.removeEventListener('click', o.click, true); } catch {}
							try { o.overlay.remove(); } catch {}
							try { o.indicator.remove(); } catch {}
						}
						delete window.__PICKING_STATE__;
						console.log('✅ Picking cleanup complete');
					};
					
					// Expose debug helper
					window.__dumpPickingState = () => {
						const s = window.__PICKING_STATE__ || {}; 
						return { lastSelector: s.lastSelector, hoverCount: s.hoverCount, locked: s.locked, hasEl: !!s.lastEl };
					};
					
					for (const d of docs) makeOverlay(d);
					console.log('✅ Picking mode activated with', overlays.length, 'overlays');
					return JSON.stringify({ status:'STARTED', docs: docs.length });
				} catch(e) { 
					console.error('❌ Picking mode error:', e);
					return JSON.stringify({ status:'ERROR', error: String(e) }); 
				}
			})();`;
			
			console.log('📤 Executing picking script in webview...');
			const result = await webview.executeJavaScript(script, true);
			console.log('📥 Picking script result:', result);
			
			let parsed = null;
			try { parsed = JSON.parse(result); } catch {}
			if(!parsed || parsed.status!=='STARTED') {
				throw new Error('Failed to start picking mode: ' + result);
			}
			
			console.log('🎉 Iframe picking mode successfully activated!');
			logInfo('Iframe picking mode activated with ' + (parsed.docs || 0) + ' documents');
		} catch (e) {
			console.error('❌ Failed to start iframe picking mode:', e);
			logError('Failed to start iframe picking mode: ' + e);
			throw new Error('Failed to start iframe picking mode: ' + e);
		}
	}, [logInfo, logWarn, logError]);

	// Stop iframe picking mode and clean up green selection areas
	const stopIframePickingMode = useCallback(async () => {
		console.log('🛑 Stopping iframe picking mode...');
		const webview = (window as any).getWebview ? (window as any).getWebview() : null;
		if (!webview) {
			console.warn('❌ No webview found for stopping picking mode');
			logWarn('No webview found for stopping picking mode');
			return;
		}
		
		try {
			const script = `(() => {
				try {
					console.log('🧹 Executing cleanup in iframe...');
					if (window.__PICKING_CLEANUP__) {
						window.__PICKING_CLEANUP__();
						delete window.__PICKING_CLEANUP__;
						console.log('✅ Picking cleanup executed');
						return 'STOPPED';
					} else {
						console.log('ℹ️ No cleanup function found');
						return 'NO_CLEANUP';
					}
				} catch(e) { 
					console.error('❌ Cleanup error:', e);
					return 'ERROR: ' + e; 
				}
			})();`;
			
			const result = await webview.executeJavaScript(script, true);
			console.log('📥 Stop picking result:', result);
			logInfo('Picking mode stopped: ' + result);
		} catch (e) {
			console.error('❌ Failed to stop iframe picking mode:', e);
			logError('Failed to stop iframe picking mode: ' + e);
		}
	}, [logWarn, logInfo, logError]);

	// Get the selected element from iframe picking mode
	const getPickedElementFromIframe = useCallback(async (): Promise<string | null> => {
		console.log('🔍 Getting picked element from iframe...');
		const webview = (window as any).getWebview ? (window as any).getWebview() : null;
		if (!webview) {
			console.warn('❌ No webview found for getting picked element');
			logWarn('No webview found for getting picked element');
			return null;
		}
		
		try {
			const script = `(() => {
				try {
					console.log('🎯 Checking for picked element in iframe...');
					
					// Simple selector generation
					const toSelector = (el) => {
						if (!el) return '';
						console.log('🏗️ Building selector for element:', el.tagName, el.id, el.className);
						
						if (el.id) {
							const sel = '#' + el.id;
							console.log('✅ Using ID selector:', sel);
							return sel;
						}
						if (el.className && typeof el.className === 'string') {
							const classes = el.className.trim().split(/\\s+/).filter(c => c && /^[a-zA-Z]/.test(c));
							if (classes.length) {
								const sel = '.' + classes[0];
								console.log('✅ Using class selector:', sel);
								return sel;
							}
						}
						const tag = el.tagName.toLowerCase();
						const parent = el.parentElement;
						if (parent) {
							const siblings = Array.from(parent.children).filter(s => s.tagName === el.tagName);
							if (siblings.length > 1) {
								const index = siblings.indexOf(el);
								const sel = tag + ':nth-of-type(' + (index + 1) + ')';
								console.log('✅ Using nth-of-type selector:', sel);
								return sel;
							}
						}
						console.log('✅ Using simple tag selector:', tag);
						return tag;
					};
					
					// Check if we have a global state from picking
					if (window.__PICKING_STATE__ && window.__PICKING_STATE__.lastEl) {
						console.log('✅ Found picked element in state:', window.__PICKING_STATE__.lastEl);
						const el = window.__PICKING_STATE__.lastEl;
						const selector = toSelector(el);
						console.log('🎯 Generated selector:', selector);
						return selector;
					}
					
					// Fallback: check if there's already a picked selector
					const existing = window.__PICK_SEL__ || (window.top && window.top.__PICK_SEL__);
					if (existing) {
						console.log('✅ Found existing selector:', existing);
						return existing;
					}
					
					console.log('❌ No picked element found');
					return null;
				} catch(e) { 
					console.error('❌ Error getting picked element:', e);
					return null; 
				}
			})();`;
			
			const selector = await webview.executeJavaScript(script, true);
			console.log('📥 Picked element result:', selector);
			return typeof selector === 'string' && selector.length > 0 ? selector : null;
		} catch (e) {
			console.error('❌ Failed to get picked element from iframe:', e);
			logError('Failed to get picked element from iframe: ' + e);
			return null;
		}
	}, [logWarn, logError]);

	// Get diagnostic information when picking fails
	const getDiagnosticInfo = useCallback(async () => {
		try {
			const webview = (window as any).getWebview ? (window as any).getWebview() : null;
			if(!webview) {
				return { hasWebview: false };
			}

			const diag = await webview.executeJavaScript(`(() => {
				const s = window.__PICKING_STATE__ || null;
				return s ? ({ hasState:true, hasEl:!!s.lastEl, hoverCount:s.hoverCount, lastSelector:s.lastSelector, locked:s.locked }) : ({ hasState:false });
			})()` , true);
			
			return { hasWebview: true, ...diag };
		} catch(e) { 
			return { hasWebview: true, error: String(e) };
		}
	}, []);

	return {
		activePicking,
		setActivePicking,
		startIframePickingMode,
		stopIframePickingMode,
		getPickedElementFromIframe,
		getDiagnosticInfo,
	};
};