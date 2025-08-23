import { Header } from "@/components/Header";
import { BrowserView } from "@/components/BrowserView";
import { CommandPanel } from "@/components/CommandPanel";
import { Footer } from "@/components/Footer";

interface MainLayoutProps {
  appName: string;
  darkMode: boolean;
  fontStack: string;
  address: string;
  setAddress: (v: string) => void;
  handleGo: (address: string) => void;
  loading: boolean;
  automation: boolean;
  handleAutomation: () => void;
  iframeUrl: string;
  uploading: boolean;
  handleUploadClick: () => void;
  fileInputRef: React.RefObject<HTMLInputElement>;
  handleFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  result: any;
  handleIframeLoad: () => void;
  commandLog: any[];
  status: string;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
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
  result,
  handleIframeLoad,
  commandLog,
  status,
}) => (
  <div
    className="h-screen w-screen flex flex-col items-center justify-between bg-gradient-to-br from-[#f8fafc] to-[#e6f0fa] dark:from-[#1a2233] dark:to-[#223a5e] transition-colors overflow-hidden"
    style={{
      fontFamily: fontStack,
      minHeight: 0,
      minWidth: 0,
      height: '100vh',
      width: '100vw',
    }}
  >
    <Header
      appName={appName}
      darkMode={darkMode}
      fontStack={fontStack}
      address={address}
      setAddress={setAddress}
      handleGo={() => handleGo(address)}
      loading={loading}
      automation={automation}
      handleAutomation={handleAutomation}
      iframeUrl={iframeUrl}
      uploading={uploading}
      handleUploadClick={handleUploadClick}
      fileInputRef={fileInputRef}
      handleFileChange={handleFileChange}
    />
    <main
      className="flex flex-col items-center w-full flex-1 px-8"
      style={{
        maxWidth: 1400,
        width: "100%",
        flex: 1,
        minHeight: 0,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-start',
      }}
    >
      <BrowserView
        iframeUrl={iframeUrl}
        loading={loading}
        uploading={uploading}
        darkMode={darkMode}
        fontStack={fontStack}
        handleIframeLoad={handleIframeLoad}
        result={result}
        style={{ minHeight: 520, height: 'calc(70vh + 80px)' }}
      />
      <div style={{ height: 38 }} />
      <CommandPanel
        commandLog={commandLog}
        fontStack={fontStack}
        darkMode={darkMode}
      />
    </main>
    <Footer fontStack={fontStack} status={status} darkMode={darkMode} />
  </div>
);
