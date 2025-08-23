import React from "react";

interface BrowserViewProps {
  iframeUrl: string;
  loading: boolean;
  uploading: boolean;
  darkMode: boolean;
  fontStack: string;
  handleIframeLoad: () => void;
  result: string | null;
}

export const BrowserView: React.FC<BrowserViewProps & { style?: React.CSSProperties }> = ({
  iframeUrl,
  loading,
  uploading,
  darkMode,
  fontStack,
  handleIframeLoad,
  result,
  style = {},
}) => (
  <div
    className="flex-grow w-full rounded-3xl shadow-2xl border border-[#B3C7E6] dark:border-[#335C81] flex items-center justify-center transition-colors overflow-hidden"
    style={{
      minHeight: 520,
      maxHeight: 1100,
      height: 'calc(70vh + 80px)',
      marginBottom: 8,
      marginTop: 24,
      position: "relative",
      background: darkMode ? undefined : "rgba(238,245,255,0.97)",
      ...style,
    }}
  >
    {iframeUrl ? (
      <iframe
        src={iframeUrl}
        title="Webpage"
        className="w-full h-full min-h-[540px] rounded-3xl border-none"
        style={{ background: "white" }}
        onLoad={handleIframeLoad}
      />
    ) : (
      <span className="text-[#7B8FA1] dark:text-[#B3C7E6] text-xl select-none">
        [ Web sitesi burada görünecek ]
      </span>
    )}
    {(loading || uploading) && (
      <div className="absolute inset-0 flex items-center justify-center bg-white/70 dark:bg-[#223A5E]/80 z-10 rounded-3xl">
        <span className="text-[#0057A0] dark:text-[#E6F0FA] text-lg font-semibold animate-pulse">
          {loading ? "Yükleniyor..." : "Yükleniyor..."}
        </span>
      </div>
    )}
    {result && (
      <div className="w-full max-w-6xl mb-4 p-4 rounded-xl bg-white/80 dark:bg-[#335C81]/80 shadow text-[#003366] dark:text-[#E6F0FA] text-center text-base break-words">
        {result}
      </div>
    )}
  </div>
);
