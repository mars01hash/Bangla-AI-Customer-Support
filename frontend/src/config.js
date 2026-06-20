// In Docker/production: VITE_API_URL is set to empty string so Nginx proxies /api
// In local dev: falls back to the direct backend address
export const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8090'
