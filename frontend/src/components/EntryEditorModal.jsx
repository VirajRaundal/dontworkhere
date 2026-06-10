import React, { useState, useEffect } from "react";
import { Plus, X } from "lucide-react";
import TagInput from "@/components/TagInput";

const fieldClass =
  "w-full bg-navy/40 border border-cream/15 text-cream placeholder:text-cream/35 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-coral focus:border-coral transition-all";
const labelClass = "block text-xs font-bold text-cream/70 mb-1.5";

const SOURCE_LABELS = ["Twitter / X", "LinkedIn", "News Article", "Interview", "Podcast", "Archive.org", "Blog", "Memo", "Other"];

// Modal to edit an entry's fields, sources and red-flag score.
// onSave receives the full payload. If `approveMode`, the primary button approves.
export default function EntryEditorModal({ entry, approveMode, onClose, onSave, saving }) {
  const [form, setForm] = useState({
    company_name: "",
    company_domain: "",
    person_name: "",
    person_title: "",
    quote: "",
    statement_date: "",
  });
  const [sources, setSources] = useState([]);
  const [tags, setTags] = useState([]);
  const [score, setScore] = useState(3);

  useEffect(() => {
    if (!entry) return;
    setForm({
      company_name: entry.company_name || "",
      company_domain: entry.company_domain || "",
      person_name: entry.person_name || "",
      person_title: entry.person_title || "",
      quote: entry.quote || "",
      statement_date: entry.statement_date || "",
    });
    setSources(entry.sources?.length ? entry.sources.map((s) => ({ ...s })) : [{ label: "Twitter / X", url: "" }]);
    setTags(entry.tags || []);
    setScore(entry.red_flag_score || 3);
  }, [entry]);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const updateSource = (i, key, val) => setSources((s) => s.map((src, idx) => (idx === i ? { ...src, [key]: val } : src)));
  const addSource = () => sources.length < 10 && setSources((s) => [...s, { label: "News Article", url: "" }]);
  const removeSource = (i) => setSources((s) => s.filter((_, idx) => idx !== i));

  const submit = () => {
    const payload = {
      ...form,
      sources: sources.filter((s) => s.url.trim()).map((s) => ({ label: s.label.trim(), url: s.url.trim() })),
      tags,
      red_flag_score: score,
    };
    onSave(payload);
  };

  if (!entry) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-start sm:items-center justify-center p-4 bg-navy/80 backdrop-blur-sm overflow-y-auto" data-testid="entry-editor-modal">
      <div className="bg-[#12233a] border border-cream/15 rounded-2xl w-full max-w-2xl my-8 shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-cream/10 sticky top-0 bg-[#12233a] rounded-t-2xl">
          <h3 className="font-display font-extrabold text-lg text-cream">
            {approveMode ? "Review & Approve" : "Edit Entry"}
          </h3>
          <button onClick={onClose} data-testid="editor-close-btn" className="text-cream/60 hover:text-coral p-1"><X size={20} /></button>
        </div>

        <div className="p-6 space-y-4">
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Company name</label>
              <input data-testid="editor-company-name" className={fieldClass} value={form.company_name} onChange={(e) => set("company_name", e.target.value)} />
            </div>
            <div>
              <label className={labelClass}>Company domain</label>
              <input data-testid="editor-company-domain" className={fieldClass} value={form.company_domain} onChange={(e) => set("company_domain", e.target.value)} />
            </div>
            <div>
              <label className={labelClass}>Person's name</label>
              <input data-testid="editor-person-name" className={fieldClass} value={form.person_name} onChange={(e) => set("person_name", e.target.value)} />
            </div>
            <div>
              <label className={labelClass}>Title / role</label>
              <input data-testid="editor-person-title" className={fieldClass} value={form.person_title} onChange={(e) => set("person_title", e.target.value)} />
            </div>
          </div>

          <div>
            <label className={labelClass}>Quote</label>
            <textarea data-testid="editor-quote" className={`${fieldClass} min-h-[90px] resize-y`} value={form.quote} onChange={(e) => set("quote", e.target.value)} />
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Date of statement</label>
              <input type="date" data-testid="editor-date" className={`${fieldClass} [color-scheme:dark]`} value={form.statement_date ? form.statement_date.slice(0, 10) : ""} onChange={(e) => set("statement_date", e.target.value)} />
            </div>
            <div>
              <label className={labelClass}>Red Flag Score</label>
              <div className="flex items-center gap-1 pt-1" data-testid="editor-score">
                {[1, 2, 3, 4, 5].map((n) => (
                  <button
                    key={n}
                    type="button"
                    onClick={() => setScore(n)}
                    data-testid={`editor-score-${n}`}
                    className={`text-2xl transition-transform hover:scale-125 ${n <= score ? "" : "opacity-25 grayscale"}`}
                    aria-label={`Set score ${n}`}
                  >
                    🚩
                  </button>
                ))}
                <span className="ml-2 text-sm font-bold text-cream/60">{score}/5</span>
              </div>
            </div>
          </div>

          <div>
            <label className={labelClass}>Sources</label>
            <div className="space-y-2">
              {sources.map((src, i) => (
                <div key={i} className="flex gap-2">
                  <select className={`${fieldClass} max-w-[150px]`} value={src.label} onChange={(e) => updateSource(i, "label", e.target.value)} data-testid={`editor-source-label-${i}`}>
                    {SOURCE_LABELS.map((l) => <option key={l} value={l} className="bg-navy">{l}</option>)}
                    {!SOURCE_LABELS.includes(src.label) && <option value={src.label} className="bg-navy">{src.label}</option>}
                  </select>
                  <input className={`${fieldClass} flex-1`} value={src.url} onChange={(e) => updateSource(i, "url", e.target.value)} placeholder="https://…" data-testid={`editor-source-url-${i}`} />
                  <button type="button" onClick={() => removeSource(i)} className="text-cream/50 hover:text-coral p-2" data-testid={`editor-remove-source-${i}`}><X size={16} /></button>
                </div>
              ))}
            </div>
            <button type="button" onClick={addSource} className="mt-2 inline-flex items-center gap-1.5 text-xs font-bold text-coral hover:text-coral-dark" data-testid="editor-add-source">
              <Plus size={14} /> Add source
            </button>
          </div>

          <div>
            <label className={labelClass}>Tags</label>
            <TagInput value={tags} onChange={setTags} testid="editor-tags" />
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-cream/10 sticky bottom-0 bg-[#12233a] rounded-b-2xl">
          <button onClick={onClose} className="rounded-full px-5 py-2.5 font-bold text-cream/70 hover:text-cream text-sm" data-testid="editor-cancel-btn">Cancel</button>
          <button onClick={submit} disabled={saving} data-testid="editor-save-btn" className="rounded-full bg-coral px-6 py-2.5 font-bold text-cream hover:bg-coral-dark disabled:opacity-60 text-sm transition-colors">
            {saving ? "Saving…" : approveMode ? `Approve with ${score} 🚩` : "Save Changes"}
          </button>
        </div>
      </div>
    </div>
  );
}
