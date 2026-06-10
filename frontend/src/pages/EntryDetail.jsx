import React, { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, ExternalLink, Share2, Calendar, Eye, Flag } from "lucide-react";
import { toast } from "sonner";
import api, { ogImageUrl } from "@/lib/api";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import CompanyLogo from "@/components/CompanyLogo";
import FlagScore from "@/components/FlagScore";
import AppealModal from "@/components/AppealModal";

const fmtDate = (d) => {
  if (!d) return null;
  try {
    return new Date(d).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
  } catch {
    return d;
  }
};

export default function EntryDetail() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const [entry, setEntry] = useState(null);
  const [status, setStatus] = useState("loading");
  const [appealOpen, setAppealOpen] = useState(false);

  useEffect(() => {
    let active = true;
    (async () => {
      setStatus("loading");
      try {
        const res = await api.get(`/entries/${slug}`);
        if (active) {
          setEntry(res.data);
          setStatus("ok");
        }
      } catch {
        if (active) setStatus("notfound");
      }
    })();
    return () => { active = false; };
  }, [slug]);

  // Inject Open Graph / Twitter meta for rich link previews.
  useEffect(() => {
    if (!entry) return;
    const prevTitle = document.title;
    document.title = `🚩 ${entry.company_name} — dontworkhere`;
    const desc = `“${entry.quote}” — ${entry.person_name}${entry.person_title ? `, ${entry.person_title}` : ""}`;
    const img = ogImageUrl(entry.slug);
    const setMeta = (attr, key, content) => {
      let el = document.head.querySelector(`meta[${attr}="${key}"]`);
      if (!el) {
        el = document.createElement("meta");
        el.setAttribute(attr, key);
        document.head.appendChild(el);
      }
      el.setAttribute("content", content);
    };
    setMeta("name", "description", desc);
    setMeta("property", "og:title", `${entry.company_name} — Red Flag`);
    setMeta("property", "og:description", desc);
    setMeta("property", "og:type", "article");
    setMeta("property", "og:image", img);
    setMeta("name", "twitter:card", "summary_large_image");
    setMeta("name", "twitter:image", img);
    return () => { document.title = prevTitle; };
  }, [entry]);

  const share = async () => {
    const url = window.location.href;
    try {
      if (navigator.share) {
        await navigator.share({ title: `Red Flag: ${entry.company_name}`, url });
      } else {
        await navigator.clipboard.writeText(url);
        toast.success("Link copied to clipboard 🚩");
      }
    } catch {
      /* user cancelled */
    }
  };

  if (status === "loading") {
    return (
      <div className="App min-h-screen flex flex-col">
        <Navbar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-5xl flag-wave">🚩</div>
        </div>
      </div>
    );
  }

  if (status === "notfound") {
    return (
      <div className="App min-h-screen flex flex-col">
        <Navbar />
        <div className="flex-1 flex flex-col items-center justify-center text-center px-5" data-testid="entry-not-found">
          <div className="text-6xl mb-4">🕳️</div>
          <h1 className="font-display font-black text-3xl text-cream">Red Flag not found</h1>
          <p className="text-cream/60 mt-3">It may have been unpublished or never existed.</p>
          <button onClick={() => navigate("/")} className="mt-6 rounded-full bg-coral px-6 py-3 font-bold text-cream hover:bg-coral-dark transition-colors">
            Back to Directory
          </button>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="App min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 max-w-3xl w-full mx-auto px-5 sm:px-8 py-10">
        <Link to="/" className="inline-flex items-center gap-2 text-cream/60 hover:text-coral font-semibold text-sm mb-6 transition-colors" data-testid="entry-back-link">
          <ArrowLeft size={16} /> Back to directory
        </Link>

        <motion.article
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="bg-cream text-navy rounded-3xl border-l-8 border-coral shadow-2xl overflow-hidden"
          data-testid="entry-detail-card"
        >
          <div className="p-7 sm:p-10">
            <div className="flex items-start gap-5 flex-wrap">
              <CompanyLogo domain={entry.company_domain} name={entry.company_name} size={72} />
              <div className="flex-1 min-w-0">
                <h1 className="font-display font-black text-3xl sm:text-4xl tracking-tight leading-tight" data-testid="entry-company-name">
                  {entry.company_name}
                </h1>
                <p className="text-navy/70 font-semibold mt-1" data-testid="entry-person">
                  {entry.person_name}
                  {entry.person_title ? ` · ${entry.person_title}` : ""}
                </p>
              </div>
              <FlagScore score={entry.red_flag_score} size="text-2xl" />
            </div>

            {/* QUOTE */}
            <div className="relative mt-9 mb-2">
              <span className="quote-mark absolute -top-6 -left-2 text-7xl sm:text-8xl text-coral/25">“</span>
              <blockquote className="relative font-display italic font-bold text-2xl sm:text-3xl leading-snug pl-6 pr-2" data-testid="entry-quote">
                {entry.quote}
              </blockquote>
            </div>

            <div className="mt-6 flex items-center flex-wrap gap-x-5 gap-y-2 text-sm font-semibold text-navy/60">
              {entry.statement_date && (
                <span className="flex items-center gap-2">
                  <Calendar size={15} /> Said on {fmtDate(entry.statement_date)}
                </span>
              )}
              <span className="flex items-center gap-1.5" data-testid="entry-views">
                <Eye size={15} /> {entry.views || 0} view{entry.views === 1 ? "" : "s"}
              </span>
            </div>

            {entry.tags?.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2" data-testid="entry-tags">
                {entry.tags.map((t) => (
                  <span key={t} className="rounded-full bg-navy/5 border border-navy/10 px-3 py-1 text-xs font-bold text-navy/60">
                    {t}
                  </span>
                ))}
              </div>
            )}

            {/* SOURCES */}
            {entry.sources?.length > 0 && (
              <div className="mt-8">
                <p className="text-xs font-bold uppercase tracking-wider text-navy/50 mb-3">Sources</p>
                <div className="flex flex-wrap gap-2.5" data-testid="entry-sources">
                  {entry.sources.map((s, i) => (
                    <a
                      key={i}
                      href={s.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      data-testid={`entry-source-${i}`}
                      className="inline-flex items-center gap-1.5 rounded-full bg-navy text-cream px-4 py-2 text-sm font-bold hover:bg-coral transition-colors"
                    >
                      {s.label} <ExternalLink size={13} />
                    </a>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-9 pt-6 border-t border-navy/10 flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-2 flex-wrap">
                <button onClick={share} data-testid="entry-share-btn" className="inline-flex items-center gap-2 rounded-full bg-coral px-5 py-2.5 text-sm font-bold text-cream hover:bg-coral-dark transition-colors">
                  <Share2 size={15} /> Share this flag
                </button>
                <button onClick={() => setAppealOpen(true)} data-testid="entry-appeal-btn" className="inline-flex items-center gap-2 rounded-full border border-navy/20 px-5 py-2.5 text-sm font-bold text-navy/70 hover:border-coral hover:text-coral transition-colors">
                  <Flag size={15} /> Request a correction
                </button>
              </div>
              <Link to="/submit" className="text-sm font-bold text-navy/60 hover:text-coral transition-colors" data-testid="entry-report-link">
                Spotted another? Raise a flag →
              </Link>
            </div>
          </div>
        </motion.article>
      </main>
      {appealOpen && (
        <AppealModal slug={entry.slug} companyName={entry.company_name} onClose={() => setAppealOpen(false)} />
      )}
      <Footer />
    </div>
  );
}
