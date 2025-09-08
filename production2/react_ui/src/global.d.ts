declare global {
	interface Window {
		__DEV_LOGS?: Array<{
			time: string;
			component: string;
			state: string;
			code?: string;
			message?: string;
		}>;
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
