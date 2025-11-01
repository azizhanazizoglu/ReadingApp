 
import React, { RefObject } from "react";
import { AllianzLogo } from "@/components/AllianzLogo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Button } from "@/components/ui/button";
import { ArrowRight, Zap, UploadCloud, Home, ChevronLeft, ChevronRight, RefreshCcw, Crosshair } from "lucide-react";
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
}) => {
  // Dev log helper
  const devLog = (code: string, message: string) => {
    if (typeof window !== 'undefined') {
      if (!(window as any).__DEV_LOGS) (window as any).__DEV_LOGS = [];
      (window as any).__DEV_LOGS.push({
        time: new Date().toISOString(), component: 'Header', state: 'event', code, message
      });
    }
  };

  // Wrapper helpers
  const onGo = () => { devLog('HD-GO', 'Go clicked'); handleGo(); };
  const onAutomation = () => { devLog('HD-AUTO', 'Automation clicked'); handleAutomation(); };
  const onUpload = () => { devLog('HD-UPLOAD', 'Upload clicked'); handleUploadClick(); };

  // Nav state
  const [canBack, setCanBack] = React.useState(false);
  const [canForward, setCanForward] = React.useState(false);
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
  const onBack = () => { try { const el: any = document.getElementById('app-webview'); if (el?.canGoBack?.()) el.goBack(); } catch {} };
  const onForward = () => { try { const el: any = document.getElementById('app-webview'); if (el?.canGoForward?.()) el.goForward(); } catch {} };
  const onRefresh = () => { try { const el: any = document.getElementById('app-webview'); if (el?.reload) { if (el.reloadIgnoringCache) el.reloadIgnoringCache(); else el.reload(); } } catch {} };

  // TsX dev inputs
  const [tsxCmd, setTsxCmd] = React.useState<string>('Yeni Trafik');
  const [forceLLM, setForceLLM] = React.useState<boolean>(false);
  const [fullAutoRunning, setFullAutoRunning] = React.useState<boolean>(false);

  // Calibration state
  const [calibOpen, setCalibOpen] = React.useState(false);
  const [calibHost, setCalibHost] = React.useState<string>('');
  const [calibTask, setCalibTask] = React.useState<string>('Yeni Trafik');
  const [calibRuhsat, setCalibRuhsat] = React.useState<Record<string, string>>({});
  const [calibCandidates, setCalibCandidates] = React.useState<any[]>([]);
  const [calibLoadedOnce, setCalibLoadedOnce] = React.useState(false);

  // Wait for webview stop
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

  // TsX loop
  const runTsxLoop = async () => {
    devLog('HD-TSX-START', 'TsX loop start');
    const MAX_STEPS = 6;
    let lastExecuted: string | undefined = undefined;
    for (let step = 1; step <= MAX_STEPS; step++) {
      try {
        const { html, url } = await getDomAndUrlFromWebview((c, m) => devLog(c, `[step ${step}] ${m}`));
        if (!html) { devLog('HD-TSX-NOHTML', `[step ${step}] no html`); break; }
        devLog('HD-TSX-REQUEST', `[step ${step}] sending ${html.length} chars`);
        const r = await fetch(`${BACKEND_URL}/api/tsx/dev-run`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_command: tsxCmd || 'Yeni Trafik', html, force_llm: !!forceLLM, executed_action: lastExecuted, current_url: url, hard_reset: step === 1 })
        });
        if (!r.ok) { devLog('HD-TSX-ERR', `[step ${step}] HTTP ${r.status}`); break; }
        const j = await r.json();
        devLog('HD-TSX-OK', `[step ${step}] state=${j?.state}`);
        if (j?.state === 'nav_failed') { devLog('HD-TSX-END', `[step ${step}] nav_failed`); break; }
        const details = j?.details || {};
        const phase = details?.phase; const mappingReady = !!details?.mapping_ready;
        if (phase === 'filling' || mappingReady) {
          try {
            try { await fetch(`${BACKEND_URL}/api/mapping/dump`, { method: 'POST' }); } catch {}
            await runTs3(BACKEND_URL, (c, m) => devLog(c, `[TS3] ${m}`), { useBackendScript: true, highlight: true, simulateTyping: true, stepDelayMs: 0 });
            await waitForWebviewStop(8000);
          } catch (e: any) {
            devLog('HD-TS3-ERR', `[step ${step}] ${String(e?.message || e)}`);
            devLog('HD-TSX-END', `[step ${step}] final not reached`);
            break;
          }
          devLog('HD-TSX-END', `[step ${step}] completed to final`);
          break;
        }
        const actions: string[] = (j?.details && Array.isArray(j.details.actions)) ? j.details.actions : [];
        if (actions.length > 0) {
          const first = [actions[0]];
          try { const res = await runActions(first, true, (c, m) => devLog(c, `[step ${step}] ${m}`)); devLog('HD-TSX-ACT', `[step ${step}] executed 1 action ${JSON.stringify(res)}`); lastExecuted = first[0]; }
          catch (e: any) { devLog('HD-TSX-ACT-ERR', `[step ${step}] ${String(e?.message || e)}`); lastExecuted = first[0]; }
          await waitForWebviewStop(8000);
          continue;
        }
        devLog('HD-TSX-END', `[step ${step}] no actions`);
        break;
      } catch (e: any) { devLog('HD-TSX-FAIL', `[step ${step}] ${String(e?.message || e)}`); break; }
    }
  };

  // Calibration start
  const onCalibClick = async () => {
    try {
      devLog('HD-CALIB-CLICK', 'Calibration start');
      const res = await runCalibStart('Yeni Trafik', (m) => devLog('HD-CALIB', m));
      if (!res?.ok) { devLog('HD-CALIB-ERR', res?.error || 'start_failed'); return; }
      try { (window as any).__CALIB_EXISTING__ = res?.existing || null; } catch {}
      setCalibHost(res.host || 'unknown');
      setCalibTask(res.task || 'Yeni Trafik');
      setCalibCandidates(res.candidates_preview || []);
      setCalibRuhsat((res.ruhsat as any) || {});
      setCalibOpen(true);
      setCalibLoadedOnce(true);
      devLog('HD-CALIB-OK', `Session ready host=${res.host}`);
    } catch (e: any) { devLog('HD-CALIB-ERR', String(e?.message || e)); }
  };

  // Full automation: Find Home -> Go to Task -> Auto (Master)
  const runFullAutomation = async () => {
    if (fullAutoRunning) return;
    setFullAutoRunning(true);
    devLog('HD-AUTO-FULL', 'Full automation start');
    try {
      // 1) Find Home (F1)
      try {
        const result = await runFindHomePageSF({ waitAfterClickMs: 800, name: 'F1', log: (m) => devLog('HD-F1-LOG', m) });
        if (result.changed) devLog('HD-F1-DONE', `changed via selector=${result.selector} index=${result.index}`);
        else devLog('HD-F1-NOCHANGE', result.reason || 'no-change');
      } catch (e: any) {
        devLog('HD-F1-ERR', String(e?.message || e));
      }
      await waitForWebviewStop(8000);

      // 2) Go to Task (F2)
      try {
        const label = (tsxCmd || '').trim() || 'Yeni Trafik';
        devLog('HD-F2', `Full-auto F2 label='${label}'`);
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
          forceLLM: false,
          maxLoops: Number(sfCfg?.maxLoops ?? 6),
          maxStaticTries: Number(sfCfg?.maxStaticTries ?? 8),
          maxLLMTries: Number(sfCfg?.maxLLMTries ?? 3),
        });
        if (res.changed) devLog('HD-F2-DONE', `changed finalSelector=${res.finalSelector || ''}`);
        else devLog('HD-F2-NOCHANGE', `no change; sideMenuOpened=${res.sideMenuOpened} tried=${res.triedSelectors.length}`);
        if (typeof window !== 'undefined') { const existing = document.getElementById('f2-tried-selectors-panel'); if (existing && existing.parentElement) existing.parentElement.removeChild(existing); }
      } catch (e: any) {
        devLog('HD-F2-ERR', String(e?.message || e));
      }
      await waitForWebviewStop(8000);

      // 3) Auto/Master (F3 pipeline)
      try {
        const res = await runMasterUserTaskPageSF(undefined, { log: (m) => devLog('HD-MASTER-LOG', m) });
        devLog('HD-MASTER-DONE', `ok=${res.ok} method=${(res as any).method || 'unknown'} stoppedAt=${(res as any).stoppedAt || null}`);
      } catch (e: any) {
        devLog('HD-MASTER-ERR', String(e?.message || e));
      }

      devLog('HD-AUTO-FULL-END', 'Full automation completed');
    } finally {
      setFullAutoRunning(false);
    }
  };

  return (
    <div style={{ display:'flex', flexDirection:'column', height:'100vh', width:'100%' }}>
      <header
        className={"w-full px-10 py-4 bg-white/80 dark:bg-[#223A5E]/90 shadow-md rounded-b-3xl transition-colors border-b border-[#e6f0fa] dark:border-[#335C81]"}
        style={{ fontFamily: fontStack, height: 'auto', minHeight: 80, maxWidth: 1400, margin: '0 auto' }}
      >
        <div className="w-full flex items-center justify-between">
          {/* Logo & App Name */}
          <div className="flex items-center gap-3 min-w-[220px]">
            <AllianzLogo className="h-9 w-9" darkMode={darkMode} />
            <span className="text-xl font-semibold tracking-tight text-[#003366] dark:text-[#E6F0FA] select-none">{appName}</span>
          </div>
          {/* Search Bar + Nav/Actions */}
          <div className="flex items-center gap-3 flex-1 justify-center">
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
            {/* Back/Forward/Refresh */}
            <Button className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] dark:bg-[#335C81] dark:hover:bg-[#223A5E] dark:text-[#E6F0FA] shadow" style={{ fontFamily: fontStack, minWidth: 40, minHeight: 40 }} onClick={onBack} disabled={!canBack} aria-label="Geri" title="Geri">
              <ChevronLeft size={20} />
            </Button>
            <Button className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] dark:bg-[#335C81] dark:hover:bg-[#223A5E] dark:text-[#E6F0FA] shadow" style={{ fontFamily: fontStack, minWidth: 40, minHeight: 40 }} onClick={onForward} disabled={!canForward} aria-label="İleri" title="İleri">
              <ChevronRight size={20} />
            </Button>
            <Button className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] dark:bg-[#335C81] dark:hover:bg-[#223A5E] dark:text-[#E6F0FA] shadow" style={{ fontFamily: fontStack, minWidth: 40, minHeight: 40 }} onClick={onRefresh} aria-label="Yenile" title="Yenile">
              <RefreshCcw size={18} />
            </Button>
            <Button className="px-3 py-1 rounded-full bg-[#0057A0] hover:bg-[#003366] active:scale-95 text-white shadow transition-all flex items-center justify-center" style={{ fontFamily: fontStack, minWidth: 40, minHeight: 40, boxShadow: '0 2px 12px 0 rgba(0,87,160,0.10)' }} onClick={onGo} disabled={loading || !address.trim()} tabIndex={0} aria-label="Git">
          <ArrowRight size={20} strokeWidth={2.1} className="transition-transform duration-150 group-active:scale-90" />
            </Button>
            <Button className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] dark:bg-[#335C81] dark:hover:bg-[#223A5E] dark:text-[#E6F0FA] shadow transition-all flex items-center justify-center" style={{ fontFamily: fontStack, minWidth: 40, minHeight: 40, boxShadow: '0 2px 12px 0 rgba(0,87,160,0.10)' }} onClick={runFullAutomation} disabled={fullAutoRunning || !iframeUrl} tabIndex={0} aria-label="Tam Otomasyon Başlat" title="Find Home → Go to Task → Auto">
              <Zap size={22} strokeWidth={2.2} className={fullAutoRunning ? 'animate-pulse' : ''} />
            </Button>
            <Button className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] dark:bg-[#335C81] dark:hover:bg-[#223A5E] dark:text-[#E6F0FA] shadow transition-all flex items-center justify-center" style={{ fontFamily: fontStack, minWidth: 40, minHeight: 40, boxShadow: '0 2px 12px 0 rgba(0,87,160,0.10)' }} onClick={onUpload} disabled={uploading} tabIndex={0} aria-label="JPG Yükle">
              <UploadCloud size={22} strokeWidth={2.2} className={uploading ? 'animate-pulse' : ''} />
              <input ref={fileInputRef} type="file" accept="image/jpeg" className="hidden" onChange={handleFileChange} disabled={uploading} />
            </Button>

            {/* Calibrate (always visible) — icon-only, matches top-row style */}
            <Button
              className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] dark:bg-[#335C81] dark:hover:bg-[#223A5E] dark:text-[#E6F0FA] shadow transition-all flex items-center justify-center"
              style={{ fontFamily: fontStack, minWidth: 40, minHeight: 40, boxShadow: '0 2px 12px 0 rgba(0,87,160,0.10)' }}
              onClick={onCalibClick}
              aria-label="Calibrate"
              title="Calibrate"
            >
              <Crosshair size={20} strokeWidth={2.1} />
            </Button>

            {/* User Task input kept always visible in top header */}
            <input
              value={tsxCmd}
              onChange={(e) => setTsxCmd(e.target.value)}
              placeholder="Komut: Yeni Trafik"
              className="px-2 py-1 text-sm rounded-md border border-[#B3C7E6] focus:outline-none focus:ring-2 focus:ring-[#0057A0] bg-white text-[#003366]"
              style={{ minWidth: 160, height: 34 }}
              aria-label="TsX Komutu"
              title="User Task"
            />
          </div>
          {/* Theme Toggle */}
          <div className="flex items-center min-w-[48px] justify-end gap-2 pl-3">
            <DevModeToggle onClick={() => onToggleDeveloperMode && onToggleDeveloperMode()} active={developerMode} />
            <ThemeToggle />
          </div>
        </div>

        {/* Action Bar (wraps to new lines on small widths) - visible only in Debug */}
        {developerMode && (
        <div className="w-full mt-3 flex flex-wrap items-center gap-2">

          {/* Calibrate moved to top header */}

          {/* 2) Auto (dev) */}
            <Button className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] shadow" style={{ fontFamily: fontStack, minWidth: 72, minHeight: 40, fontWeight: 700 }} onClick={async () => {
              try { const res = await runMasterUserTaskPageSF(undefined, { log: (m) => devLog('HD-MASTER-LOG', m) }); devLog('HD-MASTER-DONE', `ok=${res.ok} method=${(res as any).method || 'unknown'} stoppedAt=${(res as any).stoppedAt || null}`); } catch (e: any) { devLog('HD-MASTER-ERR', String(e?.message || e)); }
            }} aria-label="Auto (Static → LLM)">Auto</Button>

          {/* 3) Find Home (dev) */}
            <Button className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] shadow" style={{ fontFamily: fontStack, minWidth: 52, minHeight: 40, fontWeight: 700 }} onClick={async () => {
              try { const result = await runFindHomePageSF({ waitAfterClickMs: 800, name: 'F1', log: (m) => devLog('HD-F1-LOG', m) }); if (result.changed) devLog('HD-F1-DONE', `changed via selector=${result.selector} index=${result.index}`); else devLog('HD-F1-NOCHANGE', result.reason || 'no-change'); } catch (e: any) { devLog('HD-F1-ERR', String(e?.message || e)); }
            }} aria-label="Find Home">Find Home</Button>

          {/* 4) Go to Task (dev) */}
            <Button className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] shadow" style={{ fontFamily: fontStack, minWidth: 52, minHeight: 40, fontWeight: 700 }} onClick={async () => {
              try {
                const label = (tsxCmd || '').trim() || 'Yeni Trafik';
                devLog('HD-F2', `F2 clicked goUserTaskPageSF label='${label}'`);
                let sfCfg: any = (window as any).__CFG_GOUTASK_SF;
                if (!sfCfg) {
                  try { const r = await fetch(`${BACKEND_URL}/api/config`); const j = await r.json(); sfCfg = (j?.goUserTaskPage?.stateflow) || {}; (window as any).__CFG_GOUTASK_SF = sfCfg; devLog('HD-F2-CFG', `loaded SF config ${JSON.stringify(sfCfg)}`); } catch {}
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
                if (res.changed) devLog('HD-F2-DONE', `changed finalSelector=${res.finalSelector || ''}`); else devLog('HD-F2-NOCHANGE', `no change; sideMenuOpened=${res.sideMenuOpened} tried=${res.triedSelectors.length}`);
                if (typeof window !== 'undefined') { const existing = document.getElementById('f2-tried-selectors-panel'); if (existing && existing.parentElement) existing.parentElement.removeChild(existing); }
              } catch (e: any) { devLog('HD-F2-ERR', String(e?.message || e)); }
            }} aria-label="Go to Task">Go to Task</Button>

          {/* 5) Fill (Static) (dev) */}
            <Button className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] shadow" style={{ fontFamily: fontStack, minWidth: 52, minHeight: 40, fontWeight: 700 }} onClick={async () => {
              try { const result = await runFillFormsUserTaskPageStaticSF({ log: (m) => devLog('HD-TSX-SF', `Static SF: ${m}`) }); if (result?.ok) devLog('HD-TSX-SUCCESS', `Static fill ok step=${result.step || 'unknown'}`); else devLog('HD-TSX-ERROR', `Static fill failed step=${result?.step || 'unknown'} error=${result?.error || 'unknown'}`); } catch (e: any) { devLog('HD-TSX-CLICK-ERR', `Static error: ${String(e?.message || e)}`); }
            }} aria-label="Fill (Static)">Fill (Static)</Button>

          {/* 6) Fill (LLM) (dev) */}
            <Button className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] shadow" style={{ fontFamily: fontStack, minWidth: 52, minHeight: 40, fontWeight: 700 }} onClick={async () => {
              try { const result = await runFillFormsUserTaskPageSF({ log: (m) => devLog('HD-F3-LLM-SF', `LLM SF: ${m}`) }); if (result?.ok) devLog('HD-F3-LLM-RESULT', `LLM stateflow ok step=${result.step || 'unknown'}`); else devLog('HD-F3-LLM-ERROR', `LLM stateflow failed step=${result?.step || 'unknown'} error=${result?.error || 'unknown'}`); } catch (e: any) { devLog('HD-F3-ERR', `F3: ${String(e?.message || e)}`); }
            }} aria-label="Fill (LLM)">Fill (LLM)</Button>

          {/* Quick Home (dev utility) */}
          <Button className="ml-auto px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] dark:bg-[#335C81] dark:hover:bg-[#223A5E] dark:text-[#E6F0FA] shadow" style={{ fontFamily: fontStack, minWidth: 40, minHeight: 40 }} onClick={() => setAddress('https://preview--screen-to-data.lovable.app/traffic-insurance')} aria-label="Ana Sayfa (Dev)" title="Quick open Traffic Insurance page">
            <Home size={20} />
          </Button>
  </div>
  )}
      </header>

      {/* Content Area & Calibration Panel */}
      <div style={{ position:'relative', width:'100%', flex:1 as any, minHeight:0, overflow:'hidden' }}>
        {/* Resizable container: width shrinks smoothly when panel opens */}
        <div style={{ position:'absolute', top:0, left:0, bottom:0, right:0 }}>
          <div id="calibration-iframe-host" style={{ position:'absolute', top:0, left:0, bottom:0, width: `calc(100% - ${calibOpen? 640: 0}px)`, transition:'width 320ms cubic-bezier(0.4,0,0.2,1)', willChange:'width', overflow:'hidden' }} />
        </div>
        {/* Sliding panel anchored to right */}
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
                try { const r = await saveCalibDraft(calibHost, calibTask, draft); devLog('HD-CALIB-SAVE', `saved ${r?.path || ''}`); } catch (e: any) { devLog('HD-CALIB-SAVE-ERR', String(e?.message || e)); }
              }}
              onTestPlan={async () => {
                try { const rr = await fetch(`${BACKEND_URL}/api/calib`, { method: 'POST', headers: { 'Content-Type':'application/json' }, body: JSON.stringify({ op: 'testFillPlan', mapping: { host: calibHost, task: calibTask } }) }); const jj = await rr.json(); devLog('HD-CALIB-TEST', `ok=${jj?.ok} count=${jj?.plan?.count}`); } catch (e: any) { devLog('HD-CALIB-TEST-ERR', String(e?.message || e)); }
              }}
              onFinalize={async () => {
                try { devLog('HD-CALIB-FINALIZE', `finalize host=${calibHost} task=${calibTask}`); const res = await finalizeCalib(calibHost, calibTask); devLog('HD-CALIB-FINALIZE-OK', `merged=${res?.merged ?? false}`); } catch (e: any) { devLog('HD-CALIB-FINALIZE-ERR', String(e?.message || e)); }
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
