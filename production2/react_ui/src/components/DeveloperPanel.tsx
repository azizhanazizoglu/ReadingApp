import React from "react";
import { Button } from "@/components/ui/button";
import { Monitor, Home, Zap, Code2 } from "lucide-react";

interface DeveloperPanelProps {
  onHome: () => void;
  onTestSt1: () => void;
  onTestSt2: () => void;
  darkMode: boolean;
}

export const DeveloperPanel: React.FC<DeveloperPanelProps> = ({
  onHome,
  onTestSt1,
  onTestSt2,
  darkMode,
}) => {
  return (
    <div
      className="flex flex-row gap-4 items-center justify-center p-4 rounded-2xl shadow-lg border border-[#B3C7E6] dark:border-[#335C81] bg-white/90 dark:bg-[#223A5E]/90 mt-6 mb-2"
      style={{ minWidth: 420 }}
    >
      <Button
        className="flex items-center gap-2 px-4 py-2 rounded-full bg-[#0057A0] hover:bg-[#003366] text-white font-semibold shadow"
        onClick={onHome}
        aria-label="Ana Sayfa"
      >
        <Home size={20} /> Ana Sayfa
      </Button>
      <Button
        className="flex items-center gap-2 px-4 py-2 rounded-full bg-[#FFD580] hover:bg-[#FFB300] text-[#665C3A] font-semibold shadow"
        onClick={onTestSt1}
        aria-label="Test State 1"
      >
        <Zap size={20} /> TestSt1
      </Button>
      <Button
        className="flex items-center gap-2 px-4 py-2 rounded-full bg-[#B3C7E6] hover:bg-[#0057A0] text-[#003366] dark:bg-[#335C81] dark:hover:bg-[#223A5E] dark:text-[#E6F0FA] font-semibold shadow"
        onClick={onTestSt2}
        aria-label="Test State 2"
      >
        <Code2 size={20} /> TestSt2
      </Button>
      <span className="ml-4 flex items-center gap-2 text-xs font-mono text-[#7B8FA1] dark:text-[#B3C7E6]">
        <Monitor size={16} /> Developer Modu
      </span>
    </div>
  );
};
