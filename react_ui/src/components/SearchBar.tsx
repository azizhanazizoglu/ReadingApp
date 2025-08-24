import React from "react";

interface SearchBarProps {
  address: string;
  setAddress: (val: string) => void;
  onGo: () => void;
  loading: boolean;
  fontStack: string;
  darkMode: boolean;
  searchFocused: boolean;
  setSearchFocused: (val: boolean) => void;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  address,
  setAddress,
  onGo,
  loading,
  fontStack,
  darkMode,
  searchFocused,
  setSearchFocused,
}) => {
  React.useEffect(() => {
    if (typeof window !== 'undefined') {
      if (!window.__DEV_LOGS) window.__DEV_LOGS = [];
      window.__DEV_LOGS.push({
        time: new Date().toISOString(),
        component: 'SearchBar',
        state: 'render',
        code: 'SB-1001',
        message: 'SearchBar render edildi.'
      });
    }
  }, []);
  const handleEnter = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      if (typeof window !== 'undefined') {
        if (!window.__DEV_LOGS) window.__DEV_LOGS = [];
        window.__DEV_LOGS.push({
          time: new Date().toISOString(),
          component: 'SearchBar',
          state: 'event',
          code: 'SB-1002',
          message: 'Enter ile arama yapıldı.'
        });
      }
      onGo();
    }
  };
  return (
    <div className="relative flex items-center w-full max-w-2xl mx-auto">
      <input
        type="text"
        value={address}
        onChange={(e) => setAddress(e.target.value)}
        onFocus={() => setSearchFocused(true)}
        onBlur={() => setSearchFocused(false)}
        className={`pr-4 py-3 w-full rounded-full bg-[#f5faff] dark:bg-[#223A5E] text-base shadow focus:ring-2 focus:ring-[#0057A0] dark:focus:ring-[#E6F0FA] focus:outline-none transition-all border border-[#B3C7E6] dark:border-[#335C81] text-[#003366] dark:text-[#E6F0FA] font-normal ${address ? 'pl-12 text-left' : 'pl-0 text-center'} animate-search-move`}
        style={{ fontFamily: fontStack, minWidth: 320, maxWidth: '100%', fontWeight: 400, letterSpacing: 0.01, transition: 'padding 0.3s, text-align 0.3s' }}
        onKeyDown={handleEnter}
        autoFocus
        disabled={loading}
      />
    <span
      className={`absolute top-1/2 transform -translate-y-1/2 text-[#003366] dark:text-[#B3C7E6] pointer-events-none transition-all duration-300 ${address ? 'left-4' : 'left-1/2 -translate-x-1/2'} animate-search-icon`}
      style={{ fontWeight: 700, transition: 'left 0.3s, transform 0.3s' }}
    >
  {/* Daha kaliteli, küçük ve kalın bir büyüteç ikonu */}
      <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
        <circle cx="11" cy="11" r="7" />
        <line x1="18" y1="18" x2="15.2" y2="15.2" />
      </svg>
    </span>
    <style>{`
      .animate-search-move {
        transition: padding 0.3s, text-align 0.3s;
      }
      .animate-search-icon {
        transition: left 0.3s, transform 0.3s;
      }
    `}</style>
    </div>
  );
}
