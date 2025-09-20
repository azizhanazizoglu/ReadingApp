import React, { RefObject } from "react";
import { AllianzLogo } from "@/components/AllianzLogo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Button } from "@/components/ui/button";
import { ArrowRight, Zap, UploadCloud, Home, Code2, ChevronLeft, ChevronRight, RefreshCcw } from "lucide-react";
import { SearchBar } from "@/components/SearchBar";
import { DevModeToggle } from "@/components/DevModeToggle";
import { getDomAndUrlFromWebview, getWebview } from "@/services/webviewDom";
import { runActions } from "@/services/ts3ActionRunner";
import { runTs3 } from "@/services/ts3Service";
import { BACKEND_URL } from "@/config";
import { runFindHomePageSF } from "@/stateflows/findHomePageSF";
import { runGoUserTaskPageSF } from "@/stateflows/goUserTaskPageSF";
import { runFillFormsUserTaskPageSF } from "@/stateflows/fillFormsUserTaskPageSF";
import { runFillFormsUserTaskPageSF as runFillFormsUserTaskPageStaticSF } from "@/stateflows/fillFormsUserTaskPageStaticSF";
import { runMasterUserTaskPageSF } from "@/stateflows/masterUserTaskPageSF";
import { runCalibStart, saveCalibDraft, finalizeCalib } from "@/stateflows/calibFillUserTaskPageStaticSF";
import { CalibrationPanel } from "@/components/CalibrationPanel";

interface HeaderProps {
  appName: string;
  darkMode: boolean;
  fontStack: string;
  address: string;
  setAddress: (val: string) => void;
  handleGo: () => void;
  loading: boolean;
  automation: boolean;
  handleAutomation: () => void;
  iframeUrl: string;
  uploading: boolean;
  handleUploadClick: () => void;
  fileInputRef: RefObject<HTMLInputElement>;
  handleFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  developerMode?: boolean;
  onToggleDeveloperMode?: () => void;
  onDevHome?: () => void;
  onDevTestSt1?: () => void;
  onDevTestSt2?: () => void;
  onDevTestSt3?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  appName,
  darkMode,
  fontStack,
  address,
  setAddress,
  handleGo,
  loading,
  automation,
  handleAutomation,
  iframeUrl,
  uploading,
  handleUploadClick,
  fileInputRef,
  handleFileChange,
  developerMode = false,
  onToggleDeveloperMode,
  onDevHome,
  onDevTestSt1,
  onDevTestSt2,
  onDevTestSt3,
}) => {
  // Developer log helper
  const devLog = (code: string, message: string) => {
    if (typeof window !== 'undefined') {
      if (!window.__DEV_LOGS) window.__DEV_LOGS = [];
      window.__DEV_LOGS.push({
        time: new Date().toISOString(),
        component: 'Header',
        state: 'event',
        code,
        message
      });
    }
  };
  // Wrapper fonksiyonlar
  const onGo = () => { devLog('HD-1001', 'Go butonuna tıklandı'); handleGo(); };
  const onAutomation = () => { devLog('HD-1002', 'Otomasyon başlat butonuna tıklandı'); handleAutomation(); };
  const onUpload = () => { devLog('HD-1003', 'Upload butonuna tıklandı'); handleUploadClick(); };
  // Back/Forward state
  const [canBack, setCanBack] = React.useState(false);
  const [canForward, setCanForward] = React.useState(false);
  // TsX command (developer input)
  const [tsxCmd, setTsxCmd] = React.useState<string>("Yeni Trafik");
  const [forceLLM, setForceLLM] = React.useState<boolean>(false);
  // Poll canGoBack/canGoForward on url change
  React.useEffect(() => {
    const el: any = document.getElementById('app-webview');
    if (!el) return;
    const update = () => {
      try {
        setCanBack(!!el.canGoBack && el.canGoBack());
        setCanForward(!!el.canGoForward && el.canGoForward());
      } catch {}
    };
    update();
    const t = setInterval(update, 500);
    return () => clearInterval(t);
  }, [iframeUrl]);
  const onBack = () => {
    try {
      const el: any = document.getElementById('app-webview');
      if (el && el.canGoBack && el.canGoBack()) {
        devLog('HD-NAV-BACK', 'Geri butonuna tıklandı');
        el.goBack();
      }
    } catch {}
  };
  const onForward = () => {
    try {
      const el: any = document.getElementById('app-webview');
      if (el && el.canGoForward && el.canGoForward()) {
        devLog('HD-NAV-FWD', 'İleri butonuna tıklandı');
        el.goForward();
      }
    } catch {}
  };
  const onRefresh = () => {
    try {
      const el: any = document.getElementById('app-webview');
      if (el && el.reload) {
        devLog('HD-NAV-REFRESH', 'Yenile butonuna tıklandı');
        // Tercihen cache'i atlayarak yenile
        if (el.reloadIgnoringCache) el.reloadIgnoringCache(); else el.reload();
      }
    } catch {}
  };
  // Calibration panel state
  const [calibOpen, setCalibOpen] = React.useState(false);
  const [calibHost, setCalibHost] = React.useState<string>("");
  const [calibTask, setCalibTask] = React.useState<string>("Yeni Trafik");
  const [calibCandidates, setCalibCandidates] = React.useState<any[]>([]);
  const [calibRuhsat, setCalibRuhsat] = React.useState<Record<string, string>>({});

  const [calibLoadedOnce, setCalibLoadedOnce] = React.useState(false);
  const onCalibClick = async () => {
    // Toggle close if already open (no fresh backend call)
    if (calibOpen) {
      setCalibOpen(false);
      devLog('HD-CALIB-TOGGLE', 'Panel closed');
      return;
    }
    // If we have already loaded once, just reopen and (optionally) refresh latest draft without re-extracting image/LLM every time
    if (calibLoadedOnce) {
      setCalibOpen(true);
      devLog('HD-CALIB-REOPEN', 'Panel reopened (cached data)');
      // Soft refresh existing draft & ruhsat in background
      try {
        const hostVal = calibHost || 'unknown';
        if (hostVal !== 'unknown') {
          const r = await fetch(`${BACKEND_URL}/api/calib`, { method: 'POST', headers:{ 'Content-Type':'application/json' }, body: JSON.stringify({ op:'load', mapping:{ host: hostVal, task: calibTask || 'Yeni Trafik' } }) });
          const j = await r.json();
          if (j?.ok && j?.data) {
            try { (window as any).__CALIB_EXISTING__ = j.data; } catch {}
            devLog('HD-CALIB-RELOAD', 'Draft reloaded on reopen');
          }
        }
      } catch {}
      return;
    }
    try {
      devLog('HD-CALIB-CLICK', 'Calibration button clicked (initial load)');
      devLog('HD-CALIB', 'Starting session: DOM capture + OCR/LLM extraction');
      const res = await runCalibStart('Yeni Trafik', (m)=>devLog('HD-CALIB', m));
      devLog('HD-CALIB', `StartSession returned ok=${res?.ok} host=${res?.host||''} inputs_found=${res?.inputs_found ?? 'n/a'} ruhsat_keys=${Object.keys(res?.ruhsat||{}).length}`);
      if (!res?.ok) { devLog('HD-CALIB-ERR', res?.error || 'start_failed'); return; }
      try { (window as any).__CALIB_EXISTING__ = res?.existing || null; } catch {}
      setCalibHost(res.host || 'unknown');
      setCalibTask(res.task || 'Yeni Trafik');
      setCalibCandidates(res.candidates_preview || []);
      setCalibRuhsat((res.ruhsat as any) || {});
      setCalibOpen(true);
      setCalibLoadedOnce(true);
      devLog('HD-CALIB-OK', `Session ready host=${res.host}`);
    } catch (e: any) {
      devLog('HD-CALIB-ERR', String(e?.message || e));
    }
  };
  // Wait for one did-stop-loading from webview (with timeout)
  const waitForWebviewStop = (timeoutMs = 7000) => new Promise<void>((resolve) => {
    try {
      const el: any = getWebview();
      if (!el || !el.addEventListener) { setTimeout(() => resolve(), 400); return; }
      let done = false;
      const onStop = () => { if (done) return; done = true; try { el.removeEventListener('did-stop-loading', onStop); } catch {} resolve(); };
      try { el.addEventListener('did-stop-loading', onStop); } catch { setTimeout(() => resolve(), 400); return; }
      setTimeout(() => { if (done) return; done = true; try { el.removeEventListener('did-stop-loading', onStop); } catch {} resolve(); }, timeoutMs);
    } catch { setTimeout(() => resolve(), 400); }
  });

  // Run TsX loop: capture → backend → maybe click 1 action → wait → repeat (max few steps)
  const runTsxLoop = async () => {
    devLog('HD-TSX-START', 'TsX button clicked - starting loop');
    const MAX_STEPS = 6;
    let lastExecuted: string | undefined = undefined;
    for (let step = 1; step <= MAX_STEPS; step++) {
      try {
        devLog('HD-TSX-STEP', `[step ${step}] Getting HTML from webview`);
        const { html, url } = await getDomAndUrlFromWebview((c, m) => devLog(c, `[step ${step}] ${m}`));
        if (!html) { 
          devLog('HD-TSX-NOHTML', `[step ${step}] Webview HTML alınamadı`); 
          break; 
        }
        devLog('HD-TSX-REQUEST', `[step ${step}] Sending request to backend: ${html.length} chars, URL: ${url}`);
        const r = await fetch(`${BACKEND_URL}/api/tsx/dev-run`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_command: tsxCmd || 'Yeni Trafik', html, force_llm: !!forceLLM, executed_action: lastExecuted, current_url: url, hard_reset: step === 1 })
        });
        devLog('HD-TSX-RESPONSE', `[step ${step}] Backend response: ${r.status} ${r.statusText}`);
        if (!r.ok) { 
          devLog('HD-TSX-ERR', `[step ${step}] HTTP ${r.status}`); 
          break; 
        }
        const j = await r.json();
        devLog('HD-TSX-OK', `[step ${step}] state=${j?.state} details=${JSON.stringify(j?.details||{})}`);
        if (j?.state === 'nav_failed') {
          devLog('HD-TSX-END', `[step ${step}] nav_failed reason=${j?.details?.reason||''} tries=${j?.details?.tries??''}`);
          break;
        }
        // If we've reached filling phase or mapping is ready, trigger TS3 fill now and stop the loop
        const details = j?.details || {};
        const phase = details?.phase;
        const mappingReady = !!details?.mapping_ready;
        if (phase === 'filling' || mappingReady) {
          try {
            // Dump mapping JSON to backend logs for diagnostics
            try {
              await fetch(`${BACKEND_URL}/api/mapping/dump`, { method: 'POST' });
            } catch {}
            await runTs3(BACKEND_URL, (c, m) => devLog(c, `[TS3] ${m}`), { useBackendScript: true, highlight: true, simulateTyping: true, stepDelayMs: 0 });
            // Wait one load-stop and poll backend to detect final PDF state
            await waitForWebviewStop(8000);
            let prevHtml: string | undefined;
            let finalOk = false;
            for (let i = 0; i < 5; i++) {
              const { html: curHtml, url: curUrl } = await getDomAndUrlFromWebview((c, m) => devLog(c, `[TS3-POLL ${i+1}/5] ${m}`));
              if (!curHtml) break;
              try {
                const rr = await fetch(`${BACKEND_URL}/api/tsx/dev-run`, {
                  method: 'POST', headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ user_command: tsxCmd || 'Yeni Trafik', html: curHtml, prev_html: prevHtml, current_url: curUrl })
                });
                const jj = await rr.json();
                devLog('HD-TS3-POLL', `[${i+1}/5] state=${jj?.state} details=${JSON.stringify(jj?.details||{})}`);
                const d = jj?.details || {};
                if (jj?.state === 'final' || d?.phase === 'final' || d?.is_final === true) { finalOk = true; break; }
              } catch {}
              prevHtml = curHtml;
              await waitForWebviewStop(1500);
            }
            if (!finalOk) {
              throw new Error('Form doldurma tamamlanamadı veya PDF üretilmedi.');
            }
          } catch (e: any) {
            devLog('HD-TS3-ERR', `[step ${step}] ${String(e?.message || e)}`);
            // Mark TsX as failed since we couldn’t complete to PDF
            devLog('HD-TSX-END', `[step ${step}] ERROR: form doldurulamadı veya final PDF bulunamadı`);
            break;
          }
          devLog('HD-TSX-END', `[step ${step}] final PDF bulundu, süreç tamam`);
          break;
        }
        const actions: string[] = (j?.details && Array.isArray(j.details.actions)) ? j.details.actions : [];
        if (actions.length > 0) {
          // Execute only the first candidate, then wait for navigation and loop
          const first = [actions[0]];
          try {
            const res = await runActions(first, true, (c, m) => devLog(c, `[step ${step}] ${m}`));
            devLog('HD-TSX-ACT', `[step ${step}] Executed 1 action: ${JSON.stringify(res)}`);
            lastExecuted = first[0];
          } catch (e: any) {
            devLog('HD-TSX-ACT-ERR', `[step ${step}] ${String(e?.message || e)}`);
            lastExecuted = first[0];
          }
          await waitForWebviewStop(8000);
          // Continue loop to recapture and re-run
          continue;
        }
        // No actions returned → assume we're at home or static success; end
        devLog('HD-TSX-END', `[step ${step}] completed without actions`);
        break;
      } catch (e: any) {
        devLog('HD-TSX-FAIL', `[step ${step}] ${String(e?.message || e)}`);
        break;
      }
    }
  };
  return (
  <>
  <header
    className={"w-full flex items-center justify-between px-10 py-4 bg-white/80 dark:bg-[#223A5E]/90 shadow-md rounded-b-3xl transition-colors border-b border-[#e6f0fa] dark:border-[#335C81]"}
    style={{
      fontFamily: fontStack,
      height: 80,
      maxWidth: 1400,
      margin: "0 auto",
    }}
  >
    {/* Logo & App Name */}
    <div className="flex items-center gap-3 min-w-[220px]">
      <AllianzLogo className="h-9 w-9" darkMode={darkMode} />
      <span className="text-xl font-semibold tracking-tight text-[#003366] dark:text-[#E6F0FA] select-none">
        {appName}
      </span>
    </div>
    {/* Search Bar + Buttons */}
  <div className="flex items-center gap-3 flex-1 justify-center">
      {/* Developer butonları - search bar solunda */}
    <div className="flex items-center gap-2 mr-3 pr-0">
          {/* TsX Command input (Dev) */}
          <input
            value={tsxCmd}
            onChange={(e) => setTsxCmd(e.target.value)}
            placeholder="Komut: Yeni Trafik"
            className="px-2 py-1 text-sm rounded-md border border-[#B3C7E6] focus:outline-none focus:ring-2 focus:ring-[#0057A0] bg-white text-[#003366]"
            style={{ minWidth: 140, height: 32 }}
            aria-label="TsX Komutu"
          />
          <label className="flex items-center gap-2 text-xs text-[#003366]">
            <input type="checkbox" checked={forceLLM} onChange={(e)=>setForceLLM(e.target.checked)} />
            LLM
          </label>
          <Button
            className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] dark:bg-[#335C81] dark:hover:bg-[#223A5E] dark:text-[#E6F0FA] shadow"
            style={{ fontFamily: fontStack, minWidth: 40, minHeight: 40 }}
            onClick={() => {
              // Ana sayfa: search bar'a adres yaz
              setAddress("https://preview--screen-to-data.lovable.app/traffic-insurance");
            }}
            aria-label="Ana Sayfa (Dev)"
          >
            <Home size={20} />
          </Button>
          {developerMode && (
          <Button
            className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] shadow"
            style={{ fontFamily: fontStack, minWidth: 52, minHeight: 40, fontWeight: 700 }}
            onClick={async () => {
              try {
                devLog('HD-TSX-CLICK', 'TsX button clicked - starting static stateflow');
                const result = await runFillFormsUserTaskPageStaticSF({
                  log: (m) => devLog('HD-TSX-SF', `Static SF: ${m}`)
                });
                
                if (result?.ok) {
                  devLog('HD-TSX-SUCCESS', `TsX static stateflow completed - step: ${result.step || 'unknown'}`);
                } else {
                  devLog('HD-TSX-ERROR', `TsX static stateflow failed - step: ${result?.step || 'unknown'}, error: ${result?.error || 'unknown'}`);
                }
              } catch (e: any) {
                devLog('HD-TSX-CLICK-ERR', `TsX button error: ${String(e?.message || e)}`);
              }
            }}
            aria-label="TsX Dev Run"
          >
            TsX
          </Button>
          )}
          <Button
            className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] shadow"
            style={{ fontFamily: fontStack, minWidth: 40, minHeight: 40, fontWeight: 700 }}
            onClick={onCalibClick}
            aria-label="Calibration"
            title="Calibration"
          >
            C
          </Button>
          {developerMode && (
          <Button
            className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] shadow"
            style={{ fontFamily: fontStack, minWidth: 52, minHeight: 40, fontWeight: 700 }}
            onClick={async () => {
              try {
                devLog('HD-F1', 'F1 clicked');
                const result = await runFindHomePageSF({
                  waitAfterClickMs: 800,
                  name: 'F1',
                  log: (m) => devLog('HD-F1-LOG', m),
                });
                if (result.changed) {
                  devLog('HD-F1-DONE', `changed via selector=${result.selector} index=${result.index}`);
                } else {
                  devLog('HD-F1-NOCHANGE', result.reason || 'no-change');
                }
              } catch (e: any) {
                devLog('HD-F1-ERR', String(e?.message || e));
              }
            }}
            aria-label="F1"
          >
            F1
          </Button>
          )}
          {developerMode && (
          <Button
            className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] shadow"
            style={{ fontFamily: fontStack, minWidth: 72, minHeight: 40, fontWeight: 700 }}
            onClick={async () => {
              try {
                devLog('HD-MASTER', 'Master SF clicked - StaticLLMFallback');
                const res = await runMasterUserTaskPageSF(undefined, { log: (m) => devLog('HD-MASTER-LOG', m) });
                devLog('HD-MASTER-DONE', `ok=${res.ok} method=${(res as any).method || 'unknown'} stoppedAt=${(res as any).stoppedAt || null}`);
              } catch (e: any) {
                devLog('HD-MASTER-ERR', String(e?.message || e));
              }
            }}
            aria-label="Master"
          >
            Master
          </Button>
          )}
          {developerMode && (
          <Button
            className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] shadow"
            style={{ fontFamily: fontStack, minWidth: 52, minHeight: 40, fontWeight: 700 }}
            onClick={async () => {
              try {
                const label = (tsxCmd || '').trim() || 'Yeni Trafik';
                devLog('HD-F2', `F2 clicked goUserTaskPageSF label='${label}'`);
                // Pull stateflow defaults from backend config on first use
                let sfCfg: any = (window as any).__CFG_GOUTASK_SF;
                if (!sfCfg) {
                  try {
                    const r = await fetch(`${BACKEND_URL}/api/config`);
                    const j = await r.json();
                    sfCfg = (j?.goUserTaskPage?.stateflow) || {};
                    (window as any).__CFG_GOUTASK_SF = sfCfg;
                    devLog('HD-F2-CFG', `loaded SF config ${JSON.stringify(sfCfg)}`);
                  } catch {}
                }
                const res = await runGoUserTaskPageSF(label, {
                  waitAfterClickMs: Number(sfCfg?.waitAfterClickMs ?? 800),
                  log: (m) => devLog('HD-F2-LOG', m),
                  useBackend: true,
                  fuzzy: true,
                  forceLLM: forceLLM,
                  maxLoops: Number(sfCfg?.maxLoops ?? 6),
                  maxStaticTries: Number(sfCfg?.maxStaticTries ?? 8),
                  maxLLMTries: Number(sfCfg?.maxLLMTries ?? 3),
                });
                if (res.changed) {
                  devLog('HD-F2-DONE', `changed finalSelector=${res.finalSelector || ''}`);
                } else {
                  devLog('HD-F2-NOCHANGE', `no change; sideMenuOpened=${res.sideMenuOpened} tried=${res.triedSelectors.length}`);
                }
                // Remove any previously injected F2 tried-selectors panel (no longer desired in UI)
                if (typeof window !== 'undefined') {
                  const existing = document.getElementById('f2-tried-selectors-panel');
                  if (existing && existing.parentElement) existing.parentElement.removeChild(existing);
                }
              } catch (e: any) {
                devLog('HD-F2-ERR', String(e?.message || e));
              }
            }}
            aria-label="F2"
          >
            F2
          </Button>
          )}
          {developerMode && (
          <Button
            className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] shadow"
            style={{ fontFamily: fontStack, minWidth: 52, minHeight: 40, fontWeight: 700 }}
            onClick={async () => {
              try {
                devLog('HD-F3', 'F3 clicked - Pure LLM form filling');
                
                // Call pure LLM stateflow directly (with PDF capture we added)
                const result = await runFillFormsUserTaskPageSF({
                  log: (m) => devLog('HD-F3-LLM-SF', `LLM SF: ${m}`)
                });
                
                if (result?.ok) {
                  devLog('HD-F3-LLM-RESULT', `F3: LLM stateflow completed successfully - step: ${result.step || 'unknown'}`);
                } else {
                  devLog('HD-F3-LLM-ERROR', `F3: LLM stateflow failed - step: ${result?.step || 'unknown'}, error: ${result?.error || 'unknown'}`);
                }
              } catch (e: any) {
                devLog('HD-F3-ERR', `F3: ${String(e?.message || e)}`);
              }
            }}
            aria-label="F3"
          >
            F3
          </Button>
          )}
        </div>
      <SearchBar
        address={address}
        setAddress={setAddress}
        onGo={onGo}
        loading={loading}
        fontStack={fontStack}
        darkMode={darkMode}
        searchFocused={false}
        setSearchFocused={() => {}}
        compact={developerMode}
      />
      {/* Back/Forward/Refresh buttons to the right of SearchBar, left of Go */}
      <Button
        className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] dark:bg-[#335C81] dark:hover:bg-[#223A5E] dark:text-[#E6F0FA] shadow"
        style={{ fontFamily: fontStack, minWidth: 40, minHeight: 40 }}
        onClick={onBack}
        disabled={!canBack}
        aria-label="Geri"
        title="Geri"
      >
        <ChevronLeft size={20} />
      </Button>
      <Button
        className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] dark:bg-[#335C81] dark:hover:bg-[#223A5E] dark:text-[#E6F0FA] shadow"
        style={{ fontFamily: fontStack, minWidth: 40, minHeight: 40 }}
        onClick={onForward}
        disabled={!canForward}
        aria-label="İleri"
        title="İleri"
      >
        <ChevronRight size={20} />
      </Button>
      <Button
        className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] dark:bg-[#335C81] dark:hover:bg-[#223A5E] dark:text-[#E6F0FA] shadow"
        style={{ fontFamily: fontStack, minWidth: 40, minHeight: 40 }}
        onClick={onRefresh}
        aria-label="Yenile"
        title="Yenile"
      >
        <RefreshCcw size={18} />
      </Button>
      <Button
        className="px-3 py-1 rounded-full bg-[#0057A0] hover:bg-[#003366] active:scale-95 text-white shadow transition-all flex items-center justify-center"
        style={{
          fontFamily: fontStack,
          minWidth: 40,
          minHeight: 40,
          boxShadow: "0 2px 12px 0 rgba(0,87,160,0.10)",
        }}
        onClick={onGo}
        disabled={loading || !address.trim()}
        tabIndex={0}
        aria-label="Git"
      >
        <ArrowRight size={22} strokeWidth={2.2} className="transition-transform duration-150 group-active:scale-90" />
      </Button>
      {/** vertical divider removed for cleaner look **/}
      <Button
        className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] dark:bg-[#335C81] dark:hover:bg-[#223A5E] dark:text-[#E6F0FA] shadow transition-all flex items-center justify-center"
        style={{
          fontFamily: fontStack,
          minWidth: 40,
          minHeight: 40,
          boxShadow: "0 2px 12px 0 rgba(0,87,160,0.10)",
        }}
        onClick={onAutomation}
        disabled={automation || !iframeUrl}
        tabIndex={0}
        aria-label="Otomasyonu Başlat"
      >
        <Zap size={22} strokeWidth={2.2} className={automation ? "animate-pulse" : ""} />
      </Button>
      <Button
        className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] dark:bg-[#335C81] dark:hover:bg-[#223A5E] dark:text-[#E6F0FA] shadow transition-all flex items-center justify-center"
        style={{
          fontFamily: fontStack,
          minWidth: 40,
          minHeight: 40,
          boxShadow: "0 2px 12px 0 rgba(0,87,160,0.10)",
        }}
        onClick={onUpload}
        disabled={uploading}
        tabIndex={0}
        aria-label="JPG Yükle"
      >
        <UploadCloud size={22} strokeWidth={2.2} className={uploading ? "animate-pulse" : ""} />
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg"
          className="hidden"
          onChange={handleFileChange}
          disabled={uploading}
        />
      </Button>
    </div>
    {/* Theme Toggle */}
  <div className="flex items-center min-w-[48px] justify-end gap-2 pl-3">
      <DevModeToggle onClick={() => onToggleDeveloperMode && onToggleDeveloperMode()} active={developerMode} />
      <ThemeToggle />
    </div>
  </header>
  { /* Sliding layout v2: iframe stays in normal flow; we wrap it so transform doesn't detach baseline; panel overlays on right. */ }
  <div style={{ position:'relative', width:'100%', height:'calc(100vh - 64px)', overflow:'hidden' }}>
    {/* Resizable container: width shrinks smoothly when panel opens */}
    <div style={{ position:'absolute', top:0, left:0, bottom:0, right:0 }}>
      <div
        id="calibration-iframe-host"
        style={{
          position:'absolute',
          top:0,
          left:0,
          bottom:0,
          width: `calc(100% - ${calibOpen? 640: 0}px)`,
          transition:'width 320ms cubic-bezier(0.4,0,0.2,1)',
          willChange:'width',
          overflow:'hidden'
        }}
      />
    </div>
    {/* Sliding panel anchored to right; no translate of iframe so left edge always visible */}
    <div style={{ position:'absolute', top:0, right:0, width:640, height:'100%', pointerEvents: calibOpen? 'auto':'none' }}>
      <div style={{ width:640, height:'100%', borderLeft: darkMode? '1px solid #1e293b':'1px solid #cbd5e1', background: darkMode? 'rgba(17,24,39,0.92)':'#ffffff', boxShadow:'-4px 0 24px -4px rgba(0,0,0,0.08)', transform:`translateX(${calibOpen? 0: 640}px)`, transition:'transform 320ms cubic-bezier(0.4,0,0.2,1)', display:'flex', flexDirection:'column' }}>
        <CalibrationPanel
          host={calibHost}
          task={calibTask}
          ruhsat={calibRuhsat}
          candidates={calibCandidates}
          darkMode={darkMode}
          existingDraft={(window as any).__CALIB_EXISTING__}
          docked
          onClose={() => setCalibOpen(o=>!o)}
          onSaveDraft={async (draft) => {
            try {
              const r = await saveCalibDraft(calibHost, calibTask, draft);
              devLog('HD-CALIB-SAVE', `saved ${r?.path || ''}`);
            } catch (e: any) {
              devLog('HD-CALIB-SAVE-ERR', String(e?.message || e));
            }
          }}
          onTestPlan={async () => {
            try {
              const rr = await fetch(`${BACKEND_URL}/api/calib`, { method: 'POST', headers: { 'Content-Type':'application/json' }, body: JSON.stringify({ op: 'testFillPlan', mapping: { host: calibHost, task: calibTask } }) });
              const jj = await rr.json();
              devLog('HD-CALIB-TEST', `ok=${jj?.ok} count=${jj?.plan?.count}`);
            } catch (e: any) {
              devLog('HD-CALIB-TEST-ERR', String(e?.message || e));
            }
          }}
          onFinalize={async () => {
            try {
              devLog('HD-CALIB-FINALIZE', `finalize host=${calibHost} task=${calibTask}`);
              const res = await finalizeCalib(calibHost, calibTask);
              devLog('HD-CALIB-FINALIZE-OK', `merged=${res?.merged ?? false}`);
            } catch (e: any) {
              devLog('HD-CALIB-FINALIZE-ERR', String(e?.message || e));
            }
          }}
        />
      </div>
    </div>
  </div>
  </>
  );
}
