import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API,
  withCredentials: true,
});

export default api;

// Absolute URL to the server-rendered Open Graph share image for an entry.
export const ogImageUrl = (slug) => (slug ? `${API}/entries/${slug}/og.png` : null);

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
