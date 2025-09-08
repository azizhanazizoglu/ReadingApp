import React from "react";
import { handleGoFactory } from "./handleGo";
import { handleIframeLoadFactory } from "./handleIframeLoad";
import { handleAutomationFactory } from "./handleAutomation";
import { handleUploadClickFactory } from "./handleUploadClick";
import { handleFileChangeFactory } from "./handleFileChange";

export interface AutomationHandlersProps {
  iframeUrl: string;
  setIframeUrl: (v: string) => void;
  setStatus: (v: string) => void;
  setLoading: (v: boolean) => void;
  setResult: (v: any) => void;
  setCommandLog: (fn: any) => void;
  setAutomation: (v: boolean) => void;
  result: any;
  statusMessages: string[];
  fileInputRef: React.RefObject<HTMLInputElement>;
  setUploading: (v: boolean) => void;
  BACKEND_URL: string;
}

export function useAutomationHandlers(props: AutomationHandlersProps) {
  const handleGo = handleGoFactory(props);
  const handleIframeLoad = handleIframeLoadFactory(props);
  const handleAutomation = handleAutomationFactory(props);
  const handleUploadClick = handleUploadClickFactory(props);
  const handleFileChange = handleFileChangeFactory(props);
  return {
    handleGo,
    handleIframeLoad,
    handleAutomation,
    handleUploadClick,
    handleFileChange,
  };
}
