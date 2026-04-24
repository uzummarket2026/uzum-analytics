export const API_BASE_URL = (() => {
  if (typeof window !== 'undefined') {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return 'http://localhost:8000';
    }
  }
  return process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "https://backend-production-1af8.up.railway.app";
})();

export const apiUrl = (path: string): string => {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${normalized}`;
};
