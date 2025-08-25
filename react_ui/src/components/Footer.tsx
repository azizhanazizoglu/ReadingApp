import React from "react";

interface FooterProps {
  fontStack: string;
  status: string;
  darkMode: boolean;
}

export const Footer: React.FC<FooterProps> = ({ fontStack, status, darkMode }) => {
  React.useEffect(() => {
    if (typeof window !== 'undefined') {
      if (!window.__DEV_LOGS) window.__DEV_LOGS = [];
      window.__DEV_LOGS.push({
        time: new Date().toISOString(),
        component: 'Footer',
        state: 'render',
        code: 'FT-1001',
        message: 'Footer render edildi.'
      });
    }
  }, []);
  return (
    <footer
  className="w-full px-8 py-4 bg-white/95 dark:bg-[#223A5E]/95 rounded-t-2xl shadow-sm flex items-center justify-between transition-colors border-t-2 border-[#0057A0] dark:border-[#335C81]"
      style={{
        fontFamily: fontStack,
        maxWidth: 1400,
        margin: "0 auto",
    minHeight: 60,
    height: 60,
        flexShrink: 0,
      }}
    >
  <span className="text-xl font-semibold tracking-tight text-[#003366] dark:text-[#E6F0FA] select-none">
      Zirve Sigorta
    </span>
  <span className="text-[#7B8FA1] dark:text-[#E6F0FA] text-base max-w-[55%] truncate" title={status}>{status}</span>
  <span className="text-[#0057A0] dark:text-[#B3C7E6] text-base font-medium select-none">
      Acil Destek: <a href="mailto:azizhanazizoglu@gmail.com" className="underline hover:text-[#003366] dark:hover:text-white">azizhanazizoglu@gmail.com</a>
    </span>
  </footer>
    );
  };
