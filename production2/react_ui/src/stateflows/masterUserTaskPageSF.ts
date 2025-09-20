import { runFillFormsUserTaskPageSF } from "./fillFormsUserTaskPageSF"; // F3 LLM
import { getDomAndUrlFromWebview } from "../services/webviewDom";
import { runTs3 } from "../services/ts3Service";
import { BACKEND_URL } from "../config";

export type SFResult = {
  ok: boolean;
  changed?: boolean;
  reason?: string;
  data?: any;
  step?: string;
  method?: string; // "static" | "llm_fallback"
  finalSelector?: string;
  error?: string;
};

export type SFRunner = (opts?: { log?: (msg: string) => void }) => Promise<SFResult>;

export type MasterStep = {
  name: string;
  run: SFRunner;
  stopOnChanged?: boolean; // default true
};

// StaticLLMFallback: TsX static first → F3 LLM fallback if fails
async function runStaticLLMFallback(opts?: { 
  log?: (msg: string) => void; 
  maxTsxSteps?: number; 
  tsxCmd?: string;
  initialUrl?: string; // URL to reset to for LLM fallback
}): Promise<SFResult> {
  const log = opts?.log || (() => {});
  const maxTsxSteps = opts?.maxTsxSteps || 8;
  const tsxCmd = opts?.tsxCmd || 'Yeni Trafik';
  const initialUrl = opts?.initialUrl;

  log(`StaticLLMFallback: Starting TsX static → F3 LLM fallback for '${tsxCmd}'`);
  if (initialUrl) {
    log(`StaticLLMFallback: Initial URL for fallback reset: ${initialUrl}`);
  }

  // Phase 1: TsX Static First
  log(`StaticLLMFallback: Phase 1 - TsX static (max ${maxTsxSteps} steps)`);
  
  try {
    let lastExecuted: string | undefined;
    let prevHtml: string | undefined;
    let finalOk = false;

    for (let step = 1; step <= maxTsxSteps; step++) {
      const { html, url } = await getDomAndUrlFromWebview((c, m) => log(`[TsX-${step}] ${c}: ${m}`));
      if (!html) {
        log(`StaticLLMFallback: TsX step ${step} - No HTML, breaking`);
        break;
      }

      try {
        const r = await fetch(`${BACKEND_URL}/api/tsx/dev-run`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            user_command: tsxCmd, 
            html, 
            force_llm: false, // Static first
            executed_action: lastExecuted, 
            current_url: url, 
            hard_reset: step === 1,
            prev_html: prevHtml
          })
        });

        if (!r.ok) {
          log(`StaticLLMFallback: TsX step ${step} - HTTP ${r.status}, falling back to F3 LLM`);
          break;
        }

        const j = await r.json();
        log(`StaticLLMFallback: TsX step ${step} - state=${j?.state} phase=${j?.details?.phase || 'unknown'}`);

        const details = j?.details || {};
        const phase = details?.phase;
        const mappingReady = !!details?.mapping_ready;

        // Navigation failed - fall back to F3 LLM
        if (j?.state === 'nav_failed') {
          log(`StaticLLMFallback: TsX navigation failed after ${step} steps - falling back to F3 LLM`);
          break;
        }

        // Ready for form filling via TS3
        if (phase === 'filling' || mappingReady) {
          log(`StaticLLMFallback: TsX reached filling phase, executing TS3`);
          
          try {
            // Dump mapping for diagnostics
            await fetch(`${BACKEND_URL}/api/mapping/dump`, { method: 'POST' });
            
            // Execute TS3 form filling
            await runTs3(BACKEND_URL, (c, m) => log(`[TS3] ${c}: ${m}`), { 
              useBackendScript: true, 
              highlight: true, 
              simulateTyping: true, 
              stepDelayMs: 0 
            });

            // Wait and poll for final completion
            await new Promise(resolve => setTimeout(resolve, 8000));
            
            for (let i = 0; i < 5; i++) {
              const { html: curHtml, url: curUrl } = await getDomAndUrlFromWebview((c, m) => log(`[Final-Poll ${i+1}/5] ${c}: ${m}`));
              if (!curHtml) break;

              try {
                const pollResult = await fetch(`${BACKEND_URL}/api/tsx/dev-run`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ user_command: tsxCmd, html: curHtml, prev_html: prevHtml, current_url: curUrl })
                });
                
                const pollData = await pollResult.json();
                const pollDetails = pollData?.details || {};
                
                if (pollData?.state === 'final' || pollDetails?.phase === 'final' || pollDetails?.is_final === true) {
                  finalOk = true;
                  log(`StaticLLMFallback: TsX + TS3 completed successfully at poll ${i+1}`);
                  break;
                }
              } catch (e) {
                log(`StaticLLMFallback: Poll ${i+1} error: ${e}`);
              }
              
              prevHtml = curHtml;
              await new Promise(resolve => setTimeout(resolve, 1500));
            }

            if (finalOk) {
              return { 
                ok: true, 
                changed: true, 
                method: "static", 
                step: "completed", 
                reason: "TsX static navigation + TS3 fill successful" 
              };
            } else {
              log(`StaticLLMFallback: TsX filled forms but final state unclear, falling back to F3 LLM`);
              break;
            }

          } catch (fillError) {
            log(`StaticLLMFallback: TS3 fill error: ${fillError}, falling back to F3 LLM`);
            break;
          }
        }

        // Final state reached directly
        if (j?.state === 'final' || phase === 'final') {
          log(`StaticLLMFallback: TsX reached final state directly`);
          return { 
            ok: true, 
            changed: true, 
            method: "static", 
            step: "final", 
            reason: "TsX completed to final state" 
          };
        }

        // Continue TsX loop
        lastExecuted = details?.executed_action;
        prevHtml = html;
        await new Promise(resolve => setTimeout(resolve, 600));

      } catch (stepError) {
        log(`StaticLLMFallback: TsX step ${step} error: ${stepError}`);
        break;
      }
    }

    log(`StaticLLMFallback: TsX phase completed after ${maxTsxSteps} steps, no final success`);

  } catch (tsxError) {
    log(`StaticLLMFallback: TsX phase failed: ${tsxError}`);
  }

  // Phase 2: F3 LLM Fallback
  log(`StaticLLMFallback: Phase 2 - F3 LLM fallback`);
  
  // Reset URL for LLM fallback if available
  if (initialUrl) {
    log(`StaticLLMFallback: Resetting to initial URL for F3 LLM: ${initialUrl}`);
    try {
      const webview = document.getElementById('app-webview') as any;
      if (webview && webview.src) {
        webview.src = initialUrl;
        log(`StaticLLMFallback: URL reset initiated, waiting for load...`);
        await new Promise(resolve => setTimeout(resolve, 3000)); // Wait for page load
        log(`StaticLLMFallback: URL reset completed`);
      }
    } catch (resetError) {
      log(`StaticLLMFallback: URL reset warning: ${resetError}`);
    }
  }
  
  try {
    const f3Result = await runFillFormsUserTaskPageSF({
      log: (m) => log(`[F3-LLM] ${m}`)
    });

    if (f3Result?.ok) {
      log(`StaticLLMFallback: F3 LLM fallback completed successfully`);
      return {
        ok: true,
        changed: true,
        method: "llm_fallback",
        step: f3Result.step || "completed",
        reason: "F3 LLM fallback successful after TsX static failure",
        finalSelector: f3Result.finalSelector
      };
    } else {
      log(`StaticLLMFallback: F3 LLM fallback also failed: ${f3Result?.error || 'unknown'}`);
      return {
        ok: false,
        method: "llm_fallback",
        step: "both_failed",
        error: `Both TsX static and F3 LLM failed. Static: no final state, LLM: ${f3Result?.error || 'unknown'}`,
        reason: "All methods exhausted"
      };
    }

  } catch (f3Error) {
    log(`StaticLLMFallback: F3 LLM fallback error: ${f3Error}`);
    return {
      ok: false,
      method: "llm_fallback", 
      step: "f3_error",
      error: `TsX static incomplete, F3 LLM error: ${f3Error}`,
      reason: "F3 LLM exception"
    };
  }
}

export async function runMasterUserTaskPageSF(steps?: MasterStep[], opts?: { log?: (msg: string) => void }): Promise<SFResult> {
  const log = opts?.log || (() => {});
  
  // Capture initial URL for fallback reset
  const { url: initialUrl } = await getDomAndUrlFromWebview((c, m) => log(`[UrlCapture] ${c}: ${m}`));
  log(`[MasterUserTaskPageSF] Initial URL captured: ${initialUrl}`);

  // Master only does StaticLLMFallback - NO findHomePage or navigation
  log(`[MasterUserTaskPageSF] Starting StaticLLMFallback strategy (TsX → F3 LLM)`);
  
  try {
    const result = await runStaticLLMFallback({ 
      log: (m) => log(`[StaticLLMFallback] ${m}`),
      initialUrl: initialUrl 
    });
    
    log(`[MasterUserTaskPageSF] StaticLLMFallback completed: ok=${result.ok} method=${result.method || 'unknown'}`);
    return result;
    
  } catch (error) {
    log(`[MasterUserTaskPageSF] StaticLLMFallback error: ${error}`);
    return {
      ok: false,
      method: "error",
      error: `StaticLLMFallback failed: ${error}`,
      reason: "Master strategy exception"
    };
  }
}

// Convenience export
export const FeatureSF = {
  staticLLMFallback: (opts?: { 
    log?: (msg: string) => void; 
    maxTsxSteps?: number; 
    tsxCmd?: string; 
    initialUrl?: string; 
  }) => runStaticLLMFallback(opts),
};
