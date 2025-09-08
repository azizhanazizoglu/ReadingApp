// Centralized backend URL configuration.
// Prefer IPv4 loopback to avoid IPv6 (::1) mismatch with servers bound to 127.0.0.1.
export const BACKEND_URL = (
  import.meta.env?.VITE_BACKEND_URL || 'http://127.0.0.1:5100'
).toString().replace(/\/$/, '');
