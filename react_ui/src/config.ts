// Centralized backend URL for legacy React UI
// Can be overridden at build time with Vite env var VITE_BACKEND_URL
export const BACKEND_URL = (import.meta as any).env?.VITE_BACKEND_URL || 'http://127.0.0.1:5100';
