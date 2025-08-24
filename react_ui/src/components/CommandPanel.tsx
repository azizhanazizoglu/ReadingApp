import React from "react";

interface CommandPanelProps {
  commandLog: { icon: string; message: string; color: string }[];
  fontStack: string;
  darkMode: boolean;
}

export const CommandPanel: React.FC<CommandPanelProps> = ({ commandLog, fontStack, darkMode }) => {
  React.useEffect(() => {
    if (typeof window !== 'undefined') {
      if (!window.__DEV_LOGS) window.__DEV_LOGS = [];
      window.__DEV_LOGS.push({
        time: new Date().toISOString(),
        component: 'CommandPanel',
        state: 'render',
        code: 'CP-1001',
        message: 'CommandPanel render edildi.'
      });
    }
  }, []);
  return (
    <div
      className="w-full max-w-6xl mb-12 px-6 py-3 rounded-xl shadow border border-[#B3C7E6] dark:border-[#335C81] transition-colors flex items-center justify-center"
      style={{
        fontFamily: fontStack,
        minHeight: 48,
        maxHeight: 48,
        background: darkMode ? undefined : "rgba(245,250,255,0.97)",
        color: darkMode ? undefined : "#0057A0",
        boxShadow: darkMode ? undefined : "0 4px 24px 0 rgba(0,87,160,0.08)",
        borderTop: darkMode ? undefined : "2px solid #B3C7E6",
        overflow: 'hidden',
      }}
    >
    {commandLog.length === 0 ? (
      <span className="text-[#7B8FA1] dark:text-[#B3C7E6] text-base font-medium" style={{fontFamily: fontStack}}>
        Komut çıktısı burada görünecek.
      </span>
    ) : (
      <div className="flex items-center gap-3 w-full justify-center animate-fade-in">
        <span style={{ fontSize: 22, animation: commandLog[0].icon === '🟢' ? 'pop 0.5s' : commandLog[0].icon === '🔴' ? 'shake 0.5s' : 'none' }}>{commandLog[0].icon}</span>
        <span
          className="text-base font-semibold truncate"
          style={{
            color: darkMode ? '#B3C7E6' : '#0057A0',
            fontFamily: fontStack,
            letterSpacing: 0.1,
            maxWidth: 420,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {commandLog[0].message}
        </span>
      </div>
    )}
    <style>{`
      @keyframes pop { 0% { transform: scale(1); } 50% { transform: scale(1.25); } 100% { transform: scale(1); } }
      @keyframes shake { 0% { transform: translateX(0); } 20% { transform: translateX(-4px); } 40% { transform: translateX(4px); } 60% { transform: translateX(-2px); } 80% { transform: translateX(2px); } 100% { transform: translateX(0); } }
      .animate-fade-in { animation: fadeIn 0.5s; }
      @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    `}</style>
  </div>
    );
  };
