import React, { useState, useEffect, useCallback, useRef } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Search, Plus } from "lucide-react";
import api from "@/lib/api";
import Navbar from "@/components/Navbar";
import RedFlagCard from "@/components/RedFlagCard";
import Footer from "@/components/Footer";

const PAGE = 9;

const CONFETTI = Array.from({ length: 14 }).map((_, i) => ({
  id: i,
  left: `${(i * 53) % 96}%`,
  top: `${(i * 37) % 90}%`,
  size: `${1.6 + ((i * 7) % 30) / 10}rem`,
  dur: `${6 + (i % 5)}s`,
  delay: `${(i % 6) * 0.5}s`,
  rot: `${((i * 47) % 60) - 30}deg`,
}));

export default function Home() {
  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const sentinelRef = useRef(null);

  // debounce search input
  useEffect(() => {
    const t = setTimeout(() => setDebounced(search), 350);
    return () => clearTimeout(t);
  }, [search]);

  const fetchPage = useCallback(async (skip, q, replace) => {
    const res = await api.get("/entries", { params: { search: q || undefined, skip, limit: PAGE } });
    setTotal(res.data.total);
    setItems((prev) => (replace ? res.data.items : [...prev, ...res.data.items]));
  }, []);

  // load / reload on search change
  useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      try {
        const res = await api.get("/entries", { params: { search: debounced || undefined, skip: 0, limit: PAGE } });
        if (!active) return;
        setTotal(res.data.total);
        setItems(res.data.items);
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, [debounced]);

  // infinite scroll
  useEffect(() => {
    const node = sentinelRef.current;
    if (!node) return;
    const obs = new IntersectionObserver(async (entries) => {
      if (entries[0].isIntersecting && !loadingMore && !loading && items.length < total) {
        setLoadingMore(true);
        try {
          await fetchPage(items.length, debounced, false);
        } finally {
          setLoadingMore(false);
        }
      }
    }, { rootMargin: "300px" });
    obs.observe(node);
    return () => obs.disconnect();
  }, [items.length, total, loadingMore, loading, debounced, fetchPage]);

  return (
    <div className="App min-h-screen">
      <Navbar />

      {/* HERO */}
      <header className="relative overflow-hidden hero-glow">
        <div className="absolute inset-0 pointer-events-none">
          {CONFETTI.map((c) => (
            <span
              key={c.id}
              className="confetti-flag"
              style={{ left: c.left, top: c.top, fontSize: c.size, "--dur": c.dur, "--delay": c.delay, "--rot": c.rot }}
            >
              🚩
            </span>
          ))}
        </div>

        <div className="relative max-w-5xl mx-auto px-5 sm:px-8 pt-20 pb-16 sm:pt-28 sm:pb-24 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2 rounded-full border border-coral/40 bg-coral/10 px-4 py-1.5 text-xs sm:text-sm font-bold text-coral mb-7"
          >
            🚩 The toxic-boss accountability directory
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.05 }}
            className="font-display font-black tracking-tighter text-5xl sm:text-6xl lg:text-7xl leading-[0.95] text-cream"
          >
            Know Before <br className="hidden sm:block" />
            You <span className="text-coral">Go.</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.12 }}
            className="mt-6 text-base sm:text-lg text-cream/70 max-w-2xl mx-auto font-medium"
          >
            A community-powered archive of the things bosses really said about
            work culture. Search the quotes. Spot the red flags. Dodge the burnout.
          </motion.p>

          {/* search */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.18 }}
            className="mt-9 max-w-2xl mx-auto"
          >
            <div className="relative">
              <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-cream/50" size={22} />
              <input
                data-testid="search-input"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by company, person, or quote…"
                className="w-full bg-white/10 backdrop-blur-xl border border-white/20 text-cream placeholder:text-cream/40 rounded-full pl-14 pr-6 py-4 text-base sm:text-lg shadow-[0_0_30px_rgba(255,77,77,0.15)] focus:outline-none focus:ring-2 focus:ring-coral transition-all"
              />
            </div>
            <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
              <Link
                to="/submit"
                data-testid="hero-submit-link"
                className="inline-flex items-center gap-2 rounded-full bg-coral px-6 py-3 font-bold text-cream hover:bg-coral-dark transition-colors"
              >
                <Plus size={18} /> Raise a Red Flag
              </Link>
              <span className="text-sm text-cream/50 font-medium">
                {total} flag{total === 1 ? "" : "s"} raised
              </span>
            </div>
          </motion.div>
        </div>
      </header>

      {/* DIRECTORY */}
      <main className="max-w-7xl mx-auto px-5 sm:px-8 pb-24">
        <div className="flex items-end justify-between mb-8">
          <h2 className="font-display font-extrabold text-2xl sm:text-3xl text-cream">
            {debounced ? `Results for “${debounced}”` : "The Wall of Red Flags"}
          </h2>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-7">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-64 rounded-2xl shimmer" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="text-center py-24" data-testid="empty-state">
            <div className="text-6xl mb-4">🤷</div>
            <p className="font-display font-bold text-xl text-cream">No red flags found.</p>
            <p className="text-cream/60 mt-2">
              {debounced ? "Try a different search — " : ""}
              <Link to="/submit" className="text-coral font-bold hover:underline">be the first to raise one</Link>.
            </p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-7">
              {items.map((entry, i) => (
                <RedFlagCard key={entry.id} entry={entry} index={i} />
              ))}
            </div>
            <div ref={sentinelRef} className="h-12" />
            {loadingMore && (
              <p className="text-center text-cream/60 font-semibold py-4">Loading more flags…</p>
            )}
            {!loadingMore && items.length >= total && total > PAGE && (
              <p className="text-center text-cream/40 font-medium py-6">🚩 You've reached the bottom of the toxicity.</p>
            )}
          </>
        )}
      </main>

      <Footer />
    </div>
  );
}
