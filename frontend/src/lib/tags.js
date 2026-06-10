// Curated, satirical category suggestions shown on the submit form and editor.
// Tags are free-form on the backend; this list is only a convenience.
export const TAG_SUGGESTIONS = [
  "Hustle Culture",
  "Anti-Sleep",
  "996",
  "Burnout Denial",
  "Anti-Work-Life-Balance",
  "Fake Family",
  "Work Over Family",
  "Anti-Vacation",
  "Unpaid Overtime",
  "Toxic Positivity",
  "Crunch Culture",
  "Anti-Remote",
];

// Normalize a raw tag list: trim, drop empties, de-dupe (case-insensitive), cap.
export const normalizeTags = (tags, max = 6) => {
  const out = [];
  const seen = new Set();
  for (const t of tags || []) {
    const v = (t || "").trim();
    const key = v.toLowerCase();
    if (v && !seen.has(key)) {
      seen.add(key);
      out.push(v);
    }
    if (out.length >= max) break;
  }
  return out;
};
