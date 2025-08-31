import React, { RefObject } from "react";
import { AllianzLogo } from "@/components/AllianzLogo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Button } from "@/components/ui/button";
import { ArrowRight, Zap, UploadCloud, Home, Code2, ChevronLeft, ChevronRight, RefreshCcw } from "lucide-react";
import { SearchBar } from "@/components/SearchBar";
import { DevModeToggle } from "@/components/DevModeToggle";
import { getDomAndUrlFromWebview } from "@/services/webviewDom";
import { runActions } from "@/services/ts3ActionRunner";

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
  return (
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
    {developerMode && (
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
          <Button
            className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] shadow"
            style={{ fontFamily: fontStack, minWidth: 52, minHeight: 40, fontWeight: 700 }}
            onClick={async () => {
              // TsX Dev: capture HTML and call backend orchestrator step
              try {
                const { html } = await getDomAndUrlFromWebview((c, m) => devLog(c, m));
                if (!html) { devLog('HD-TSX-NOHTML', 'Webview HTML alınamadı'); return; }
                const r = await fetch('http://localhost:5001/api/tsx/dev-run', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ user_command: tsxCmd || 'Yeni Trafik', html, force_llm: !!forceLLM })
                });
                if (!r.ok) { devLog('HD-TSX-ERR', `HTTP ${r.status}`); return; }
                const j = await r.json();
                devLog('HD-TSX-OK', `state=${j?.state} details=${JSON.stringify(j?.details||{})}`);
                // If backend suggests actions for navigation (e.g., click#Ana Sayfa), execute them now
                const actions: string[] = (j?.details && Array.isArray(j.details.actions)) ? j.details.actions : [];
                if (actions.length > 0) {
                  try {
                    const res = await runActions(actions, true, (c, m) => devLog(c, m));
                    devLog('HD-TSX-ACT', `Executed ${actions.length} action(s): ${JSON.stringify(res)}`);
                  } catch (e: any) {
                    devLog('HD-TSX-ACT-ERR', String(e?.message || e));
                  }
                }
              } catch (e: any) {
                devLog('HD-TSX-FAIL', String(e?.message || e));
              }
            }}
            aria-label="TsX Dev Run"
          >
            TsX
          </Button>
          <Button
            className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] shadow"
            style={{ fontFamily: fontStack, minWidth: 52, minHeight: 40, fontWeight: 700 }}
            onClick={async () => {
              if (onDevTestSt1) onDevTestSt1();
              try {
                const r = await fetch('http://localhost:5001/api/start-automation', { method: 'POST' });
                if (!r.ok) throw new Error('Start automation failed');
              } catch {}
            }}
            aria-label="Test State 1"
          >
            Ts1
          </Button>
          <Button
            className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] shadow"
            style={{ fontFamily: fontStack, minWidth: 52, minHeight: 40, fontWeight: 700 }}
            onClick={() => { if (onDevTestSt2) onDevTestSt2(); }}
            aria-label="Test State 2"
          >
            Ts2
          </Button>
          <Button
            className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] shadow"
            style={{ fontFamily: fontStack, minWidth: 52, minHeight: 40, fontWeight: 700 }}
            onClick={() => { if (onDevTestSt3) onDevTestSt3(); }}
            aria-label="Test State 3"
          >
            Ts3
          </Button>
        </div>
      )}
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
  );
}
