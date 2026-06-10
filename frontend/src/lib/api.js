import axios from "axios";

// When REACT_APP_BACKEND_URL is unset (e.g. backend served same-origin under
// /api, as on Vercel), fall back to a relative base so requests target the
// current origin. When set (local dev, or a separate backend host), use it.
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";
export const API = `${BACKEND_URL}/api`;

// Absolute base — needed for og:image meta (crawlers can't resolve relative URLs).
const ABSOLUTE_BASE = /^https?:\/\//.test(API)
  ? API
  : (typeof window !== "undefined" ? window.location.origin + API : API);

const api = axios.create({
  baseURL: API,
  withCredentials: true,
});

export default api;

// Absolute URL to the server-rendered Open Graph share image for an entry.
export const ogImageUrl = (slug) => (slug ? `${ABSOLUTE_BASE}/entries/${slug}/og.png` : null);

// Build a Clearbit logo URL from a domain.
export const clearbitLogo = (domain) => {
  if (!domain) return null;
  const clean = domain
    .replace(/^https?:\/\//, "")
    .replace(/^www\./, "")
    .replace(/\/.*$/, "")
    .trim();
  if (!clean || !clean.includes(".")) return null;
  return `https://logo.clearbit.com/${clean}`;
};
