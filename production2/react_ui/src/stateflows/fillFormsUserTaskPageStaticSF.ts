import { getDomAndUrlFromWebview, checkSelectorHasValue } from "../services/webviewDom";
import { BACKEND_URL } from "../config";
import { runActions } from "../services/ts3ActionRunner";
import { runInPageFill } from "../services/ts3InPageFiller";
import { setupPdfDownloadCapture, waitForPdfDownload, cleanupPdfDownloadCapture } from "../services/pdfDownloadService";

export type F3Options = {
  waitAfterActionMs?: number;
  maxLoops?: number;
  maxLLMTries?: number;
  log?: (m: string) => void;
};

async function postF3Static(op: string, body: any, log?: (m: string)=>void) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/f3-static`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ op, ...(body||{}) }),
    });
    if (!res.ok) return { ok:false, error: `http_${res.status}` };
    const j = await res.json();
    log?.(`F3-Static backend op=${op} keys=${Object.keys(j||{}).join(',')}`);
    return j;
  } catch (e: any) {
    log?.(`F3-Static backend error op=${op} ${String(e?.message||e)}`);
    return { ok:false, error:'fetch_failed' };
  }
}

export async function runFillFormsUserTaskPageSF(opts?: F3Options) {
  const log = opts?.log || (()=>{});
  // Load config from backend to allow dynamic tuning
  let cfg: any = undefined;
  try {
    const res = await fetch(`${BACKEND_URL}/api/config`);
    if (res.ok) cfg = await res.json();
  } catch {}
  const f3cfg = cfg?.goFillForms?.stateflow || {};
  const waitMs = Math.max(0, opts?.waitAfterActionMs ?? (typeof f3cfg.waitAfterActionMs === 'number' ? f3cfg.waitAfterActionMs : 600));
  const maxLoops = Math.max(1, opts?.maxLoops ?? (typeof f3cfg.maxLoops === 'number' ? f3cfg.maxLoops : 10));
  const perFieldAttemptWaits: number[] = Array.isArray(f3cfg.perFieldAttemptWaits) && f3cfg.perFieldAttemptWaits.length
    ? f3cfg.perFieldAttemptWaits.map((n: any) => Math.max(0, Number(n)||0))
    : [250, 400, 600];
  const postFillVerifyDelayMs: number = typeof f3cfg.postFillVerifyDelayMs === 'number' ? f3cfg.postFillVerifyDelayMs : 200;
  const htmlCheckDelayMs: number = typeof f3cfg.htmlCheckDelayMs === 'number' ? f3cfg.htmlCheckDelayMs : 200;
  const commitEnterCfg = (f3cfg.commitEnter !== undefined) ? !!f3cfg.commitEnter : true;
  const clickOutsideCfg = (f3cfg.clickOutside !== undefined) ? !!f3cfg.clickOutside : true;

  // Step 0: get ruhsat json from backend component
  const input = await postF3Static('loadRuhsatFromTmp', {}, log);
  if (!input?.ok) {
    log(`F3-Static loadRuhsatFromTmp failed: ${JSON.stringify(input)}`);
    // Provide user-friendly error messages based on error_code
    const errorCode = input?.error_code || 'unknown';
    let userMessage = input?.error || 'Ruhsat loading failed';
    
    switch (errorCode) {
      case 'no_image_dir':
        userMessage = 'Image directory not found. Please check configuration.';
        break;
      case 'no_images':
        userMessage = 'No ruhsat images found. Please upload a ruhsat image first.';
        break;
      case 'missing_api_key':
        userMessage = 'OpenAI API key missing. Cannot extract ruhsat data from image.';
        break;
      case 'vision_failed':
        userMessage = 'Failed to extract ruhsat data from image. Please try uploading a clearer image.';
        break;
      case 'ingest_failed':
      case 'ingest_exception':
        userMessage = 'Ruhsat data processing failed. Please check the image format or try again.';
        break;
    }
    
    return { ok:false, step:'loadRuhsat', error: input?.error || 'no_input', error_code: errorCode, user_message: userMessage };
  }
  log(`F3-Static loadRuhsatFromTmp meta: ${JSON.stringify(input.meta || {})}`);
  if (input.prep) {
    log(`F3-Static staging prep: ${JSON.stringify(input.prep)}`);
  }
  const ruhsat = input.data;

  // Setup PDF download capture for final page detection
  const pdfTargetDir = 'c:\\Users\\azizh\\Documents\\ReadingApp\\production2\\tmp\\pdf';
  const pdfSetupOk = await setupPdfDownloadCapture({ 
    targetDir: pdfTargetDir, 
    timeout: 10000, 
    log 
  });
  
  if (!pdfSetupOk) {
    log('PDF-CAPTURE: Warning - Failed to setup download handler, will use fallback detection');
  } else {
    log('PDF-CAPTURE: Download handler setup successful');
  }

  // Capture initial DOM + URL so backend can resolve host (for calib.json domain mappings)
  const firstSnap = await getDomAndUrlFromWebview((m)=>log(`[WV] ${m}`));
  let prevHtml = firstSnap.html || '';
  let prevUrl  = firstSnap.url || '';
  if (!prevHtml) return { ok:false, error:'no-initial-html' };
  const domainTask = "Yeni Trafik"; // TODO: make dynamic (user selection / context)
  // Cache last analyze results to avoid re-calling static mapping for same HTML
  let lastAnaHtml: string | undefined;
  let lastAna: any | undefined;

  // Track URLs already processed (filled + action tried). Simpler/more stable than fingerprint for now.
  const processedUrls = new Set<string>();
  let lastUrl = prevUrl;

  for (let i=0; i<maxLoops; i++) {
    log(`SF-F3-Static loop ${i+1}/${maxLoops} url=${prevUrl}`);

  // Analyze (or reuse) to obtain mapping + page fingerprint + actions
    let ana: any;
    if (lastAnaHtml === prevHtml && lastAna) {
      ana = lastAna;
      log(`SF-F3-Static analyze: reused cached static mapping for current HTML`);
    } else {
      ana = await postF3Static('analyzePageStaticFillForms', { html: prevHtml, current_url: prevUrl, task: domainTask }, log);
      lastAnaHtml = prevHtml; lastAna = ana;
    }
    if (!ana?.ok) {
      log(`SF-F3-Static analyze failed: ${JSON.stringify(ana)} - attempting LLM fallback`);
      return { ok:false, step:'analyze', error: ana?.error || 'static-failed', should_fallback: true };
    }

  const pageFp = ana.fingerprint || `${prevUrl}`;
  const alreadyProcessed = processedUrls.has(prevUrl);
  log(`SF-F3-Static page id (url)=${prevUrl} processed=${alreadyProcessed}`);

    // Final page detection (only if analysis says final OR backend op confirms)
  let finalCandidate = !!ana.is_final; // now means pdf_found backend side
    // Defer early return until after we optionally run actions on a final page.
    const fin = await postF3Static('detectFinalPage', { html: prevHtml, current_url: prevUrl, task: domainTask }, log);
  let backendFinalCandidate = !!(fin?.ok && fin.is_final);
  const ctaPresent = !!(fin?.hits?.length || ana?.hits?.length || fin?.cta_present || ana?.cta_present);

  // Track CTA presence & pdf status across loops for fallback
  (window as any).__STATIC_LAST_CTA__ = ctaPresent || (window as any).__STATIC_LAST_CTA__;
  (window as any).__STATIC_LAST_PDF__ = (fin?.pdf_found || ana?.pdf_found) || (window as any).__STATIC_LAST_PDF__;

    if (alreadyProcessed) {
      // Avoid re-filling: just quick final page check then exit loop if still same and maxLoops not exceeded.
      await new Promise(r=>setTimeout(r, Math.min(waitMs, 400)));
    } else {
  const fieldMapping: Record<string,string> = ana.field_mapping || {};
  const hasMapping = fieldMapping && Object.keys(fieldMapping).length > 0;
  if (hasMapping) {
        // Validation & fallback gate
        // Determine critical fields: try calibration-provided (ana.validation?.critical_fields or ana.critical_fields) fallback to default list.
        const critical = Array.isArray(ana?.critical_fields) && ana.critical_fields.length
          ? ana.critical_fields
          : ['plaka_no', 'model_yili', 'sasi_no', 'motor_no'];
        
        const validation = await postF3Static('validateCriticalFields', { 
          field_mapping: fieldMapping, 
          ruhsat_json: ruhsat, 
          task: domainTask, 
          current_url: prevUrl,
          critical_fields_override: critical 
        }, log);
        if (validation?.ok) {
          const fallbackCheck = await postF3Static('checkShouldFallbackToLLM', { validation_result: validation, task: domainTask, current_url: prevUrl }, log);
          if (fallbackCheck?.ok && fallbackCheck.should_fallback) {
            log(`SF-F3-Static fallback triggered: ${fallbackCheck.reason} (threshold=${fallbackCheck.threshold})`);
            return { ok:false, step:'static_insufficient', should_fallback: true, fallback_reason: fallbackCheck.reason };
          }
        }

        const expectedKeys = Object.keys(fieldMapping).filter(k => ruhsat && typeof ruhsat[k] !== 'undefined' && String(ruhsat[k]??'').trim() !== '');
        const dynamicThreshold = Math.min(2, Math.max(1, expectedKeys.length >= 2 ? 2 : 1));
        
        const order = Array.from(new Set([...critical, ...expectedKeys]))
          .filter(k => !!fieldMapping[k] && String(ruhsat[k] ?? '').trim() !== '');
        log(`SF-F3-Static Form1: sequential fill order -> ${order.join(', ')}`);

        const selectorStatus: Record<string, boolean> = {};
        for (const k of order) {
          const sel = fieldMapping[k];
          log(`SF-F3-Static step: fill ${k} -> ${sel}`);
          let okOne = false;
          const attempts = perFieldAttemptWaits.length ? perFieldAttemptWaits : [300,500,700];
          for (let attempt=1; attempt<=attempts.length; attempt++) {
            const waitAfter = attempts[attempt-1];
            await runInPageFill({ [k]: sel }, ruhsat, { highlight:true, simulateTyping:true, stepDelayMs:0, commitEnter:commitEnterCfg, clickOutside:clickOutsideCfg, waitAfterFillMs: waitAfter }, (c,m)=>log(`${c} ${m}`));
            await new Promise(r=>setTimeout(r, Math.max(0, waitAfter - 100)));
            okOne = await checkSelectorHasValue(sel, (c,m)=>log(`${c} ${m}`));
            log(`SF-F3-Static step: verify ${k} attempt ${attempt} -> ${okOne? 'YES':'NO'}`);
            if (okOne) break;
          }
          selectorStatus[k] = !!okOne;
          if (!okOne) log(`SF-F3-Static step: give up ${k} after ${perFieldAttemptWaits.length} attempts`);
        }

        await new Promise(r=>setTimeout(r, htmlCheckDelayMs));
        const curHtmlCheck = (await getDomAndUrlFromWebview((m)=>log(`[WV] ${m}`))).html || prevHtml;
        const filledCheck = await postF3Static('detectFormsFilled', { html: curHtmlCheck, current_url: prevUrl, task: domainTask, min_filled: dynamicThreshold }, log);
        log(`SF-F3-Static Form1: filled-check (html-only) -> ${JSON.stringify(filledCheck)}`);

        const criticalPresent = critical.some(k => !!fieldMapping[k]);
        const criticalOk = critical.filter(k => !!fieldMapping[k]).every(k => !!selectorStatus[k]);
        const committedCount = Object.values(selectorStatus).filter(Boolean).length;
        const committedEnough = committedCount >= dynamicThreshold;

        let attemptedAction = false;
        // Provide richer gating diagnostics
        log(`SF-F3-Static gates: filledCheck.ok=${!!filledCheck?.ok} criticalPresent=${criticalPresent} criticalOk=${criticalOk} committedEnough=${committedEnough} committedCount=${committedCount} dynamicThreshold=${dynamicThreshold}`);

        // Heuristic: if every mapped selector failed to verify (all false) AND we committed zero fields,
        // treat this page as effectively "no-mapping" for action purposes. This covers pages where
        // mapping carried over from a previous page (stale selectors) or fields moved out of the DOM.
        const allSelectorsFailed = Object.keys(selectorStatus).length > 0 && Object.values(selectorStatus).every(v => !v);
        const shouldForceActionsDueToMissingSelectors = allSelectorsFailed && committedCount === 0;
        if (shouldForceActionsDueToMissingSelectors) {
          log('SF-F3-Static notice: all mapped selectors missing/unfilled; will force action attempt.');
        }

        if ((filledCheck?.ok && (!criticalPresent || criticalOk) && committedEnough) || shouldForceActionsDueToMissingSelectors) {
          const acts: string[] = Array.isArray(ana.actions) ? ana.actions : [];
          if (acts.length) {
            // Use action_selectors mapping when available from static analyzer
            const actionSelectors = ana.action_selectors || {};
            const clickActs = acts.map(a => {
              if (a.startsWith('css#')) {
                // Already css# prefixed, preserve as is
                return a;
              } else if (actionSelectors[a]) {
                // Map action label to css selector using backend mapping
                return `css#${actionSelectors[a]}`;
              } else {
                // Fall back to text search
                return `click#${a}`;
              }
            });
            log(`SF-F3-Static actions: attempting ${clickActs.join(',')} (reason=${shouldForceActionsDueToMissingSelectors ? 'force-missing-selectors' : 'gates-passed'})`);
            
            // Log detailed action analysis for debugging
            for (let i = 0; i < acts.length; i++) {
              const orig = acts[i];
              const processed = clickActs[i];
              if (orig.startsWith('css#')) {
                const selector = orig.substring(4);
                log(`SF-F3-Static action ${i+1}: CSS selector (preserved) "${selector}" -> ${processed}`);
              } else if (actionSelectors[orig]) {
                const selector = actionSelectors[orig];
                log(`SF-F3-Static action ${i+1}: CSS selector (mapped) "${selector}" -> ${processed}`);
              } else {
                log(`SF-F3-Static action ${i+1}: Text search (fallback) "${orig}" -> ${processed}`);
              }
            }
            
            await runActions(clickActs, true, (c,m)=>log(`${c} ${m}`));
            attemptedAction = true;
            
            // Only attempt PDF capture on the final page (insurance-quote)
            const isFinalPage = prevUrl?.includes('insurance-quote') || ana?.is_final || backendFinalCandidate;
            if (pdfSetupOk && isFinalPage) {
              const pdfPrimaryWaitMs = 2000; // reduced to 2 seconds for faster processing
              log(`PDF-CAPTURE: Waiting for PDF generation after actions (timeout=${pdfPrimaryWaitMs}ms)...`);
              let pdfResult = await waitForPdfDownload(pdfPrimaryWaitMs, log);
              if (!pdfResult.ok) {
                // Secondary extended wait if CTA present or final candidate heuristics indicate likely PDF
                if (ana?.cta_present || ana?.is_final) {
                  const extendedWaitMs = 1000; // reduced to 1 second for faster processing
                  log(`PDF-CAPTURE: Primary wait failed (${pdfResult.error||'timeout'}); extending wait by ${extendedWaitMs}ms due to CTA/final heuristics`);
                  const second = await waitForPdfDownload(extendedWaitMs, log);
                  // Prefer second result only if it succeeds
                  if (second.ok) pdfResult = second;
                }
              }
              if (pdfResult.ok && pdfResult.path) {
                log(`PDF-CAPTURE: Successfully captured PDF -> ${pdfResult.path}`);
                // Store PDF path globally for backend detection
                (window as any).__STATIC_LAST_PDF_PATH__ = pdfResult.path;
                (window as any).__STATIC_LAST_PDF__ = true;
              } else {
                log(`PDF-CAPTURE: Failed to capture PDF -> ${pdfResult.error || 'timeout'}`);
                // Try alternative PDF detection methods
                log('PDF-CAPTURE: Attempting alternative PDF detection...');
                const altPdfFound = await checkAlternativePdfGeneration(log);
                if (altPdfFound) {
                  log('PDF-CAPTURE: Alternative PDF detection successful');
                  (window as any).__STATIC_LAST_PDF_PATH__ = altPdfFound;
                  (window as any).__STATIC_LAST_PDF__ = true;
                } else {
                  log('PDF-CAPTURE: No alternative PDF detection methods found PDF');
                }
              }
            } else if (pdfSetupOk) {
              log(`PDF-CAPTURE: Skipped - not on final page (${prevUrl})`);
            }
          } else {
            log(`SF-F3-Static no actions for this page`);
          }
        } else {
          log(`SF-F3-Static skip actions: gates not satisfied (htmlOk=${!!filledCheck?.ok}, criticalOk=${criticalOk}, committed=${committedCount}/${dynamicThreshold})`);
        }

        processedUrls.add(prevUrl);
        // After action attempt, poll for navigation up to 5 times
        if (attemptedAction) {
          // Check if PDF was successfully captured during action - if so, this might be final completion
          const pdfCapturedDuringAction = !!(window as any).__STATIC_LAST_PDF__;
          
          const navTimeoutMs = Math.max(waitMs, 1200);
          const pollInterval = 300;
          const polls = Math.ceil(navTimeoutMs / pollInterval);
          let navigated = false;
          for (let p=0; p<polls; p++) {
            await new Promise(r=>setTimeout(r, pollInterval));
            const snap = await getDomAndUrlFromWebview((m)=>log(`[WV] ${m}`));
            if (snap.url && snap.url !== prevUrl) { navigated = true; prevHtml = snap.html || prevHtml; prevUrl = snap.url; log(`SF-F3-Static navigation detected post-action -> ${prevUrl}`); break; }
          }
          
          if (!navigated) {
            // If PDF was captured but no navigation, treat as successful completion instead of error
            if (pdfCapturedDuringAction) {
              const pdfPath = (window as any).__STATIC_LAST_PDF_PATH__;
              log(`SF-F3-Static: No navigation but PDF captured -> treating as successful completion (${pdfPath})`);
              // Cleanup PDF download handlers
              if (pdfSetupOk) {
                await cleanupPdfDownloadCapture(log);
              }
              return { ok:true, final:true, step:'pdf_captured_no_nav', pdf_path: pdfPath, last_url: prevUrl };
            }
            
            log(`SF-F3-Static ERROR: action did not cause navigation (url stayed ${prevUrl})`);
            return { ok:false, step:'action_navigation', error:'no_navigation_after_action', url: prevUrl };
          }
        } else {
          await new Promise(r=>setTimeout(r, waitMs));
        }
      } else {
        // No fields to fill – but we may still have actions (e.g. final activation button)
        const acts: string[] = Array.isArray(ana.actions) ? ana.actions : [];
        if (acts.length && !alreadyProcessed) {
          // Use action_selectors mapping when available from static analyzer (same logic as main branch)
          const actionSelectors = ana.action_selectors || {};
          const clickActs = acts.map(a => {
            if (a.startsWith('css#')) {
              // Already css# prefixed, preserve as is
              return a;
            } else if (actionSelectors[a]) {
              // Map action label to css selector using backend mapping
              return `css#${actionSelectors[a]}`;
            } else {
              // Fall back to text search
              return `click#${a}`;
            }
          });
          
          // Log detailed action analysis for debugging
          for (let i = 0; i < acts.length; i++) {
            const orig = acts[i];
            const processed = clickActs[i];
            if (orig.startsWith('css#')) {
              log(`SF-F3-Static action ${i+1} (no-mapping): CSS selector (preserved) "${orig.substring(4)}" -> ${processed}`);
            } else if (actionSelectors[orig]) {
              const selector = actionSelectors[orig];
              log(`SF-F3-Static action ${i+1} (no-mapping): CSS selector (mapped) "${selector}" -> ${processed}`);
            } else {
              log(`SF-F3-Static action ${i+1} (no-mapping): Text search (fallback) "${orig}" -> ${processed}`);
            }
          }
          
          log(`SF-F3-Static actions(no-mapping): attempting ${clickActs.join(',')}`);
          await runActions(clickActs, true, (c,m)=>log(`${c} ${m}`));
          
          // Only attempt PDF capture on the final page (insurance-quote)  
          const isFinalPage = prevUrl?.includes('insurance-quote') || ana?.is_final || backendFinalCandidate;
          if (pdfSetupOk && isFinalPage) {
            const pdfPrimaryWaitMs = 2000; // reduced to 2 seconds for faster processing
            log(`PDF-CAPTURE: Waiting for PDF generation after no-mapping actions (timeout=${pdfPrimaryWaitMs}ms)...`);
            let pdfResult = await waitForPdfDownload(pdfPrimaryWaitMs, log);
            if (!pdfResult.ok && (ana?.cta_present || ana?.is_final)) {
              const extendedWaitMs = 1000; // reduced to 1 second for faster processing
              log(`PDF-CAPTURE: Primary wait failed (${pdfResult.error||'timeout'}); extending wait by ${extendedWaitMs}ms due to CTA/final heuristics`);
              const second = await waitForPdfDownload(extendedWaitMs, log);
              if (second.ok) pdfResult = second;
            }
            if (pdfResult.ok && pdfResult.path) {
              log(`PDF-CAPTURE: Successfully captured PDF -> ${pdfResult.path}`);
              // Store PDF path globally for backend detection
              (window as any).__STATIC_LAST_PDF_PATH__ = pdfResult.path;
              (window as any).__STATIC_LAST_PDF__ = true;
            } else {
              log(`PDF-CAPTURE: Failed to capture PDF -> ${pdfResult.error || 'timeout'}`);
              // Try alternative PDF detection methods
              log('PDF-CAPTURE: Attempting alternative PDF detection...');
              const altPdfFound = await checkAlternativePdfGeneration(log);
              if (altPdfFound) {
                log('PDF-CAPTURE: Alternative PDF detection successful');
                (window as any).__STATIC_LAST_PDF_PATH__ = altPdfFound;
                (window as any).__STATIC_LAST_PDF__ = true;
              } else {
                log('PDF-CAPTURE: No alternative PDF detection methods found PDF');
              }
            }
          } else if (pdfSetupOk) {
            log(`PDF-CAPTURE: Skipped - not on final page (${prevUrl})`);
          }
          
          processedUrls.add(prevUrl);
          // After action attempt, allow navigation polling like normal branch
          const navTimeoutMs = Math.max(waitMs, 1200);
          const pollInterval = 300;
          const polls = Math.ceil(navTimeoutMs / pollInterval);
          let navigated = false;
          for (let p=0; p<polls; p++) {
            await new Promise(r=>setTimeout(r, pollInterval));
            const snap = await getDomAndUrlFromWebview((m)=>log(`[WV] ${m}`));
            if (snap.url && snap.url !== prevUrl) { navigated = true; prevHtml = snap.html || prevHtml; prevUrl = snap.url; log(`SF-F3-Static navigation detected post-action -> ${prevUrl}`); break; }
          }
          if (!navigated) {
            log(`SF-F3-Static note: action(no-mapping) did not cause navigation (url stayed ${prevUrl})`);
          }
        } else {
          log(`SF-F3-Static no field mapping & no actions; marking processed`);
          processedUrls.add(prevUrl);
          await new Promise(r=>setTimeout(r, waitMs));
        }
      }
    }

    // Snapshot to detect navigation
    const loopSnap = await getDomAndUrlFromWebview((m)=>log(`[WV] ${m}`));
    const newHtml = loopSnap.html || prevHtml;
    const newUrl  = loopSnap.url  || prevUrl;
    const urlChanged = newUrl !== prevUrl;
  if (urlChanged) log(`SF-F3-Static navigation detected loop-scan prev=${prevUrl} new=${newUrl}`);
  prevHtml = newHtml; prevUrl = newUrl;
    lastUrl = prevUrl;
    // If after processing we are still on this URL and it was a final candidate, return final.
    if ((finalCandidate || backendFinalCandidate) && processedUrls.has(prevUrl)) {
      log(`SF-F3-Static detected final page via ${finalCandidate ? 'analysis' : backendFinalCandidate ? 'backend-detect' : 'unknown'} (post-actions)`);
      return { ok:true, final:true, step:'final_page', last_url: prevUrl };
    }
  }

  // Fallback if we saw CTA but never saw pdf evidence
  try {
    const hadCta = !!(window as any).__STATIC_LAST_CTA__;
    const hadPdf = !!(window as any).__STATIC_LAST_PDF__;
    const pdfPath = (window as any).__STATIC_LAST_PDF_PATH__;
    
    if (hadCta && !hadPdf) {
      log(`SF-F3-Static fallback: CTA seen but no PDF generated after ${maxLoops} loops`);
      // Cleanup PDF download handlers
      if (pdfSetupOk) {
        await cleanupPdfDownloadCapture(log);
      }
      return { ok:false, step:'pdf_missing', should_fallback:true, reason:'pdf_not_generated', last_url: lastUrl };
    }
    
    if (hadPdf && pdfPath) {
      log(`SF-F3-Static success: PDF generated and captured -> ${pdfPath}`);
      // Cleanup PDF download handlers
      if (pdfSetupOk) {
        await cleanupPdfDownloadCapture(log);
      }
      return { ok:true, final:true, step:'pdf_captured', pdf_path: pdfPath, last_url: lastUrl };
    }
  } catch {}

  // Cleanup PDF download handlers
  if (pdfSetupOk) {
    await cleanupPdfDownloadCapture(log);
  }

  return { ok:true, step:'completed', last_url: lastUrl };
}

/**
 * Alternative PDF detection methods for when direct download fails
 */
async function checkAlternativePdfGeneration(log: (m: string) => void): Promise<string | null> {
  try {
    // Method 1: Check for new tabs/windows with PDF content
    const checkNewTabs = (): Promise<string | null> => {
      return new Promise((resolve) => {
        let foundPdf = false;
        const originalOpen = window.open;
        
        // Override window.open temporarily to catch new tabs
        window.open = function(...args) {
          const result = originalOpen.apply(this, args);
          const url = args[0]?.toString() || '';
          
          if (url.includes('.pdf') || url.includes('pdf') || url.toLowerCase().includes('download')) {
            log(`PDF-CAPTURE: Detected PDF in new tab: ${url}`);
            foundPdf = true;
            resolve(url);
          }
          
          return result;
        };
        
        // Restore after 3 seconds
        setTimeout(() => {
          window.open = originalOpen;
          if (!foundPdf) resolve(null);
        }, 3000);
      });
    };

    // Method 2: Check current page for PDF elements
    const checkCurrentPagePdf = (): string | null => {
      // Check for PDF iframe, embed, or object elements
      const pdfIframes = document.querySelectorAll('iframe[src*="pdf"], iframe[src*=".pdf"]');
      const pdfEmbeds = document.querySelectorAll('embed[src*="pdf"], embed[src*=".pdf"]');
      const pdfObjects = document.querySelectorAll('object[data*="pdf"], object[data*=".pdf"]');
      const pdfLinks = document.querySelectorAll('a[href*="pdf"], a[href*=".pdf"]');
      
      if (pdfIframes.length > 0) {
        const src = (pdfIframes[0] as HTMLIFrameElement).src;
        log(`PDF-CAPTURE: Found PDF iframe: ${src}`);
        return src;
      }
      
      if (pdfEmbeds.length > 0) {
        const src = (pdfEmbeds[0] as HTMLEmbedElement).src;
        log(`PDF-CAPTURE: Found PDF embed: ${src}`);
        return src;
      }
      
      if (pdfObjects.length > 0) {
        const data = (pdfObjects[0] as HTMLObjectElement).data;
        log(`PDF-CAPTURE: Found PDF object: ${data}`);
        return data;
      }
      
      if (pdfLinks.length > 0) {
        const href = (pdfLinks[0] as HTMLAnchorElement).href;
        log(`PDF-CAPTURE: Found PDF link: ${href}`);
        return href;
      }
      
      return null;
    };

    // Method 3: Check for blob URLs (common in modern web apps)
    const checkBlobUrls = (): string | null => {
      // Look for any blob URLs in the page that might be PDFs
      const allLinks = document.querySelectorAll('a[href^="blob:"]');
      const allSources = document.querySelectorAll('[src^="blob:"]');
      
      for (const link of allLinks) {
        const href = (link as HTMLAnchorElement).href;
        if (href.includes('blob:')) {
          log(`PDF-CAPTURE: Found blob URL link: ${href}`);
          return href;
        }
      }
      
      for (const source of allSources) {
        const src = (source as HTMLElement).getAttribute('src') || '';
        if (src.includes('blob:')) {
          log(`PDF-CAPTURE: Found blob URL source: ${src}`);
          return src;
        }
      }
      
      return null;
    };

    // Method 4: Check if URL changed to PDF-related endpoint
    const checkCurrentUrl = (): string | null => {
      const currentUrl = window.location.href;
      if (currentUrl.includes('pdf') || currentUrl.includes('download') || currentUrl.includes('quote')) {
        log(`PDF-CAPTURE: Current URL suggests PDF generation: ${currentUrl}`);
        return currentUrl;
      }
      return null;
    };

    // Try all methods with delays to allow for async PDF generation
    await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second for PDF to generate
    
    const currentPagePdf = checkCurrentPagePdf();
    if (currentPagePdf) return currentPagePdf;
    
    const blobPdf = checkBlobUrls();
    if (blobPdf) return blobPdf;
    
    const urlPdf = checkCurrentUrl();
    if (urlPdf) return urlPdf;
    
    // Check for new tabs
    const newTabPdf = await checkNewTabs();
    if (newTabPdf) return newTabPdf;
    
    log('PDF-CAPTURE: No alternative PDF detection methods found PDF');
    return null;
    
  } catch (error) {
    log(`PDF-CAPTURE: Error in alternative detection: ${error}`);
    return null;
  }
}
