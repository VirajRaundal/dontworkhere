import React, { useState } from "react";
import { X } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";

// Lets anyone flag a published entry for correction / dispute. Posts to the
// public appeal endpoint; moderators review it from the dashboard.
export default function AppealModal({ slug, companyName, onClose }) {
  const [message, setMessage] = useState("");
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (message.trim().length < 10) {
      toast.error("Please describe the issue (at least 10 characters).");
      return;
    }
    setSubmitting(true);
    try {
      await api.post(`/entries/${slug}/appeal`, { message: message.trim(), email: email.trim() });
      setDone(true);
    } catch (e2) {
      const d = e2?.response?.data?.detail;
      toast.error(typeof d === "string" ? d : "Could not submit. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-navy/80 backdrop-blur-sm" data-testid="appeal-modal">
      <div className="bg-[#12233a] border border-cream/15 rounded-2xl w-full max-w-lg shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-cream/10">
          <h3 className="font-display font-extrabold text-lg text-cream">Request a correction</h3>
          <button onClick={onClose} data-testid="appeal-close-btn" className="text-cream/60 hover:text-coral p-1"><X size={20} /></button>
        </div>

        {done ? (
          <div className="p-8 text-center" data-testid="appeal-confirmation">
            <div className="text-5xl mb-3">🙏</div>
            <p className="font-display font-bold text-lg text-cream">Thanks — a moderator will review it.</p>
            <button onClick={onClose} className="mt-6 rounded-full bg-coral px-6 py-2.5 font-bold text-cream hover:bg-coral-dark transition-colors">
              Close
            </button>
          </div>
        ) : (
          <form onSubmit={submit} className="p-6 space-y-4">
            <p className="text-sm text-cream/60">
              Spotted something wrong about <span className="font-bold text-cream">{companyName}</span>?
              Tell us what's inaccurate or missing context and a moderator will take a look.
            </p>
            <div>
              <label className="block text-xs font-bold text-cream/70 mb-1.5">What's the issue? <span className="text-coral">*</span></label>
              <textarea
                data-testid="appeal-message"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="This quote is missing context / the source no longer works / this is misattributed…"
                className="w-full bg-navy/40 border border-cream/15 text-cream placeholder:text-cream/35 rounded-xl px-4 py-3 min-h-[110px] resize-y focus:outline-none focus:ring-2 focus:ring-coral"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-cream/70 mb-1.5">Your email <span className="font-normal text-cream/40">(optional)</span></label>
              <input
                type="email"
                data-testid="appeal-email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full bg-navy/40 border border-cream/15 text-cream placeholder:text-cream/35 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-coral"
              />
            </div>
            <button
              type="submit"
              disabled={submitting}
              data-testid="appeal-submit-btn"
              className="w-full rounded-full bg-coral px-6 py-3 font-bold text-cream hover:bg-coral-dark disabled:opacity-60 transition-colors"
            >
              {submitting ? "Submitting…" : "Submit for review"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
