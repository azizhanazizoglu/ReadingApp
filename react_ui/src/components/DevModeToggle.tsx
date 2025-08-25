import * as React from "react";
import { Button } from "@/components/ui/button";
import { Bot } from "lucide-react";

export function DevModeToggle({ onClick, active }: { onClick: () => void; active: boolean }) {
  return (
    <Button
      aria-label="Developer Modu"
      onClick={onClick}
      className={`px-3 py-1 rounded-full shadow transition-all flex items-center justify-center ${
        active
          ? 'bg-[#0057A0] hover:bg-[#003366] text-white'
          : 'bg-[#E6F0FA] hover:bg-[#B3C7E6] text-[#0057A0] dark:bg-[#335C81] dark:hover:bg-[#223A5E] dark:text-[#E6F0FA]'
      }`}
      style={{ minWidth: 40, minHeight: 40 }}
    >
      <Bot className="h-5 w-5" />
    </Button>
  );
}
