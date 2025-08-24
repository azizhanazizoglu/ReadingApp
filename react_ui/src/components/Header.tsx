import React, { RefObject } from "react";
import { AllianzLogo } from "@/components/AllianzLogo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Button } from "@/components/ui/button";
import { ArrowRight, Zap, UploadCloud } from "lucide-react";
import { SearchBar } from "@/components/SearchBar";

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
}) => (
  <header
    className="w-full flex items-center justify-between px-10 py-4 bg-white/80 dark:bg-[#223A5E]/90 shadow-md rounded-b-3xl transition-colors border-b border-[#e6f0fa] dark:border-[#335C81]"
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
    <div className="flex items-center gap-2 flex-1 justify-center">
      <SearchBar
        address={address}
        setAddress={setAddress}
        onGo={handleGo}
        loading={loading}
        fontStack={fontStack}
        darkMode={darkMode}
        searchFocused={false}
        setSearchFocused={() => {}}
      />
      <Button
        className="px-3 py-1 rounded-full bg-[#0057A0] hover:bg-[#003366] active:scale-95 text-white shadow transition-all flex items-center justify-center"
        style={{
          fontFamily: fontStack,
          minWidth: 40,
          minHeight: 40,
          boxShadow: "0 2px 12px 0 rgba(0,87,160,0.10)",
        }}
        onClick={handleGo}
        disabled={loading || !address.trim()}
        tabIndex={0}
        aria-label="Git"
      >
        <ArrowRight size={22} strokeWidth={2.2} className="transition-transform duration-150 group-active:scale-90" />
      </Button>
      <Button
        className="px-3 py-1 rounded-full bg-[#E6F0FA] hover:bg-[#B3C7E6] active:scale-95 text-[#0057A0] dark:bg-[#335C81] dark:hover:bg-[#223A5E] dark:text-[#E6F0FA] shadow transition-all flex items-center justify-center"
        style={{
          fontFamily: fontStack,
          minWidth: 40,
          minHeight: 40,
          boxShadow: "0 2px 12px 0 rgba(0,87,160,0.10)",
        }}
        onClick={handleAutomation}
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
        onClick={handleUploadClick}
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
    <div className="flex items-center min-w-[48px] justify-end">
      <ThemeToggle />
    </div>
  </header>
);
