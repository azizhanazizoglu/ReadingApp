declare global {
	interface Window {
		__DEV_LOGS?: Array<{
			time: string;
			component: string;
			state: string;
			code?: string;
			message?: string;
		}>;
		electronAPI?: {
			setupPdfDownload: (config: { targetDir: string; timeout?: number }) => Promise<{ ok: boolean; targetDir?: string; error?: string }>;
			waitPdfDownload: (config: { timeoutMs: number }) => Promise<{ ok: boolean; path?: string; filename?: string; error?: string }>;
			cleanupPdfDownload: () => Promise<{ ok: boolean; error?: string }>;
		};
	}
	namespace JSX {
		interface IntrinsicElements {
			webview: React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement> & {
				src?: string;
				partition?: string;
				allowpopups?: boolean;
				preload?: string;
				useragent?: string;
			};
		}
	}
}
export {};
