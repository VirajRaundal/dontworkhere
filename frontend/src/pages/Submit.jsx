import React, { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Plus, X, ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import TagInput from "@/components/TagInput";

const SOURCE_LABELS = ["Twitter / X", "LinkedIn", "News Article", "Interview", "Podcast", "Archive.org", "Blog", "Other"];

const fieldClass =
  "w-full bg-navy/40 border border-cream/15 text-cream placeholder:text-cream/35 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-coral focus:border-coral transition-all";
const labelClass = "block text-sm font-bold text-cream mb-2";

export default function Submit() {
  const [form, setForm] = useState({
    company_name: "",
    company_domain: "",
    person_name: "",
    person_title: "",
    quote: "",
    statement_date: "",
    submitter_email: "",
  });
  const [sources, setSources] = useState([{ label: "Twitter / X", url: "" }]);
  const [tags, setTags] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const addSource = () => {
    if (sources.length >= 10) {
      toast.error("Maximum 10 sources allowed");
      return;
    }
    setSources((s) => [...s, { label: "News Article", url: "" }]);
  };
  const removeSource = (i) => setSources((s) => s.filter((_, idx) => idx !== i));
  const updateSource = (i, key, val) =>
    setSources((s) => s.map((src, idx) => (idx === i ? { ...src, [key]: val } : src)));

  const validate = () => {
    if (!form.company_name.trim()) return "Company name is required";
    if (!form.person_name.trim()) return "Person's name is required";
    if (form.quote.trim().length < 20) return "Quote must be at least 20 characters";
    const cleaned = sources.filter((s) => s.url.trim());
    if (cleaned.length < 1) return "Add at least one source with a valid URL";
    for (const s of cleaned) {
      if (!/^https?:\/\//i.test(s.url.trim())) return `Source URL must start with http:// or https:// — check "${s.label}"`;
      if (!s.label.trim()) return "Every source needs a label";
    }
    return null;
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    const err = validate();
    if (err) {
      toast.error(err);
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/submissions", {
        ...form,
        sources: sources.filter((s) => s.url.trim()).map((s) => ({ label: s.label.trim(), url: s.url.trim() })),
        tags,
      });
      setDone(true);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e2) {
      const d = e2?.response?.data?.detail;
      toast.error(typeof d === "string" ? d : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  if (done) {
    return (
      <div className="App min-h-screen flex flex-col">
        <Navbar />
        <div className="flex-1 flex items-center justify-center px-5 hero-glow">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            className="text-center max-w-lg py-20"
            data-testid="submit-confirmation"
          >
            <motion.div
              initial={{ rotate: -20 }}
              animate={{ rotate: [-20, 10, -10, 0] }}
              transition={{ duration: 1, repeat: Infinity, repeatDelay: 0.5 }}
              className="text-7xl mb-6"
            >
              🚩
            </motion.div>
            <h1 className="font-display font-black text-4xl sm:text-5xl text-cream tracking-tight">
              Your Red Flag has been raised!
            </h1>
            <p className="mt-5 text-lg text-cream/70">
              Our team will review it shortly. Thanks for keeping the working world honest. 🙌
            </p>
            <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
              <button
                onClick={() => {
                  setDone(false);
                  setForm({ company_name: "", company_domain: "", person_name: "", person_title: "", quote: "", statement_date: "", submitter_email: "" });
                  setSources([{ label: "Twitter / X", url: "" }]);
                  setTags([]);
                }}
                data-testid="submit-another-btn"
                className="rounded-full bg-coral px-6 py-3 font-bold text-cream hover:bg-coral-dark transition-colors"
              >
                Raise Another
              </button>
              <Link to="/" data-testid="back-to-directory-link" className="rounded-full border-2 border-cream/30 px-6 py-3 font-bold text-cream hover:bg-cream hover:text-navy transition-colors">
                Back to Directory
              </Link>
            </div>
          </motion.div>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="App min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 max-w-2xl w-full mx-auto px-5 sm:px-8 py-12">
        <Link to="/" className="inline-flex items-center gap-2 text-cream/60 hover:text-coral font-semibold text-sm mb-6 transition-colors" data-testid="submit-back-link">
          <ArrowLeft size={16} /> Back to directory
        </Link>

        <h1 className="font-display font-black text-4xl sm:text-5xl text-cream tracking-tight">
          🚩 Raise a Red Flag
        </h1>
        <p className="mt-4 text-cream/70">
          Spotted a boss saying the quiet part out loud? Report it. Every submission is reviewed by a moderator before going public.
        </p>

        <form onSubmit={onSubmit} className="mt-10 space-y-6" data-testid="submission-form">
          <div className="grid sm:grid-cols-2 gap-5">
            <div>
              <label className={labelClass}>Company name <span className="text-coral">*</span></label>
              <input data-testid="input-company-name" className={fieldClass} value={form.company_name} onChange={(e) => set("company_name", e.target.value)} placeholder="Acme Corp" />
            </div>
            <div>
              <label className={labelClass}>Company website / domain</label>
              <input data-testid="input-company-domain" className={fieldClass} value={form.company_domain} onChange={(e) => set("company_domain", e.target.value)} placeholder="acme.com" />
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-5">
            <div>
              <label className={labelClass}>Person's name <span className="text-coral">*</span></label>
              <input data-testid="input-person-name" className={fieldClass} value={form.person_name} onChange={(e) => set("person_name", e.target.value)} placeholder="John Doe" />
            </div>
            <div>
              <label className={labelClass}>Title / role</label>
              <input data-testid="input-person-title" className={fieldClass} value={form.person_title} onChange={(e) => set("person_title", e.target.value)} placeholder="Founder & CEO" />
            </div>
          </div>

          <div>
            <label className={labelClass}>The exact quote <span className="text-coral">*</span></label>
            <textarea
              data-testid="input-quote"
              className={`${fieldClass} min-h-[120px] resize-y`}
              value={form.quote}
              onChange={(e) => set("quote", e.target.value)}
              placeholder="“e.g. ‘If you can leave at 5, you're not committed enough.’”"
            />
            <p className={`text-xs mt-1.5 font-medium ${form.quote.trim().length >= 20 ? "text-cream/40" : "text-coral"}`}>
              {form.quote.trim().length}/20 characters minimum
            </p>
          </div>

          {/* SOURCES */}
          <div>
            <label className={labelClass}>Sources <span className="text-coral">*</span> <span className="font-normal text-cream/40">(at least one)</span></label>
            <div className="space-y-3" data-testid="sources-list">
              {sources.map((src, i) => (
                <div key={i} className="flex gap-2 items-start">
                  <select
                    data-testid={`source-label-${i}`}
                    className={`${fieldClass} max-w-[42%] sm:max-w-[180px]`}
                    value={src.label}
                    onChange={(e) => updateSource(i, "label", e.target.value)}
                  >
                    {SOURCE_LABELS.map((l) => (
                      <option key={l} value={l} className="bg-navy">{l}</option>
                    ))}
                  </select>
                  <input
                    data-testid={`source-url-${i}`}
                    className={`${fieldClass} flex-1`}
                    value={src.url}
                    onChange={(e) => updateSource(i, "url", e.target.value)}
                    placeholder="https://…"
                  />
                  <button
                    type="button"
                    onClick={() => removeSource(i)}
                    disabled={sources.length === 1}
                    data-testid={`remove-source-${i}`}
                    className="shrink-0 mt-1 p-2.5 rounded-xl text-cream/60 hover:text-coral hover:bg-coral/10 disabled:opacity-30 disabled:hover:bg-transparent transition-colors"
                    aria-label="Remove source"
                  >
                    <X size={18} />
                  </button>
                </div>
              ))}
            </div>
            <button
              type="button"
              onClick={addSource}
              disabled={sources.length >= 10}
              data-testid="add-source-btn"
              className="mt-3 inline-flex items-center gap-2 text-sm font-bold text-coral hover:text-coral-dark disabled:opacity-40 transition-colors"
            >
              <Plus size={16} /> Add Another Source
            </button>
          </div>

          {/* TAGS */}
          <div>
            <label className={labelClass}>Tags <span className="font-normal text-cream/40">(optional — help people filter)</span></label>
            <TagInput value={tags} onChange={setTags} testid="submit-tags" />
          </div>

          <div className="grid sm:grid-cols-2 gap-5">
            <div>
              <label className={labelClass}>Date of statement</label>
              <input
                type="date"
                data-testid="input-statement-date"
                className={`${fieldClass} [color-scheme:dark]`}
                value={form.statement_date}
                onChange={(e) => set("statement_date", e.target.value)}
                max={new Date().toISOString().slice(0, 10)}
              />
            </div>
            <div>
              <label className={labelClass}>Your email <span className="font-normal text-cream/40">(optional, private)</span></label>
              <input
                type="email"
                data-testid="input-submitter-email"
                className={fieldClass}
                value={form.submitter_email}
                onChange={(e) => set("submitter_email", e.target.value)}
                placeholder="you@example.com"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            data-testid="submit-flag-btn"
            className="w-full rounded-full bg-coral px-6 py-4 font-display font-extrabold text-lg text-cream hover:bg-coral-dark disabled:opacity-60 transition-colors"
          >
            {submitting ? "Raising your flag…" : "🚩 Submit Red Flag"}
          </button>
          <p className="text-center text-xs text-cream/40">
            Submit only real, verifiable quotes with sources. Submissions are moderated before going public.
          </p>
        </form>
      </main>
      <Footer />
    </div>
  );
}
