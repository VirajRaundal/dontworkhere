import React, { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { LogOut, ExternalLink, Check, Ban, Pencil, EyeOff, Trash2, UserPlus, Mail } from "lucide-react";
import api from "@/lib/api";
import Logo from "@/components/Logo";
import FlagScore from "@/components/FlagScore";
import CompanyLogo from "@/components/CompanyLogo";
import EntryEditorModal from "@/components/EntryEditorModal";
import { useAuth } from "@/context/AuthContext";

const TABS = [
  { key: "pending", label: "Pending Queue" },
  { key: "approved", label: "Live Entries" },
  { key: "rejected", label: "Rejected" },
  { key: "moderators", label: "Moderators" },
];

const StatCard = ({ label, value, accent, testid }) => (
  <div className="rounded-xl border border-cream/10 bg-cream/[0.03] px-5 py-4" data-testid={testid}>
    <div className={`font-display font-black text-3xl ${accent}`}>{value}</div>
    <div className="text-xs font-bold uppercase tracking-wider text-cream/50 mt-1">{label}</div>
  </div>
);

const fmt = (d) => {
  if (!d) return "—";
  try { return new Date(d).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" }); }
  catch { return d; }
};

export default function ModDashboard() {
  const { user, logout } = useAuth();
  const [tab, setTab] = useState("pending");
  const [stats, setStats] = useState({ live: 0, pending: 0, total: 0, rejected: 0 });
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null); // {entry, approveMode}
  const [saving, setSaving] = useState(false);
  const [scores, setScores] = useState({}); // per-entry pending score
  const [mods, setMods] = useState([]);
  const [meEmail, setMeEmail] = useState("");
  const [newMod, setNewMod] = useState("");

  const loadStats = useCallback(async () => {
    const res = await api.get("/mod/stats");
    setStats(res.data);
  }, []);

  const loadEntries = useCallback(async (status) => {
    setLoading(true);
    try {
      const res = await api.get("/mod/entries", { params: { status } });
      setEntries(res.data.items);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadMods = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get("/mod/moderators");
      setMods(res.data.items);
      setMeEmail(res.data.me);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadStats(); }, [loadStats]);
  useEffect(() => {
    if (tab === "moderators") loadMods();
    else loadEntries(tab);
  }, [tab, loadEntries, loadMods]);

  const refresh = async () => {
    await loadStats();
    if (tab === "moderators") await loadMods();
    else await loadEntries(tab);
  };

  const approve = async (entry, score) => {
    try {
      await api.post(`/mod/entries/${entry.id}/approve`, { red_flag_score: score });
      toast.success("Entry approved & published 🚩");
      await refresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to approve");
    }
  };

  const reject = async (entry) => {
    const reason = window.prompt("Reason for rejection (optional):", "");
    if (reason === null) return;
    try {
      await api.post(`/mod/entries/${entry.id}/reject`, { rejection_reason: reason });
      toast.success("Entry rejected");
      await refresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to reject");
    }
  };

  const unpublish = async (entry) => {
    if (!window.confirm("Unpublish this entry? It will move back to the pending queue.")) return;
    try {
      await api.post(`/mod/entries/${entry.id}/unpublish`);
      toast.success("Entry unpublished");
      await refresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed");
    }
  };

  const saveEdit = async (payload) => {
    setSaving(true);
    try {
      if (editing.approveMode) {
        await api.post(`/mod/entries/${editing.entry.id}/approve`, payload);
        toast.success("Approved & published 🚩");
      } else {
        await api.put(`/mod/entries/${editing.entry.id}`, payload);
        toast.success("Entry updated");
      }
      setEditing(null);
      await refresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const addModerator = async (e) => {
    e.preventDefault();
    if (!newMod.trim()) return;
    try {
      await api.post("/mod/moderators", { email: newMod.trim() });
      toast.success("Moderator added");
      setNewMod("");
      await loadMods();
    } catch (e2) {
      toast.error(e2?.response?.data?.detail || "Failed to add moderator");
    }
  };

  const removeModerator = async (email) => {
    if (!window.confirm(`Remove ${email} as a moderator?`)) return;
    try {
      await api.delete(`/mod/moderators/${encodeURIComponent(email)}`);
      toast.success("Moderator removed");
      await loadMods();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to remove");
    }
  };

  return (
    <div className="App min-h-screen">
      {/* top bar */}
      <header className="sticky top-0 z-50 bg-navy/90 backdrop-blur-xl border-b border-cream/10">
        <div className="max-w-7xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Logo size="text-xl" />
            <span className="hidden sm:inline text-xs font-bold uppercase tracking-wider text-coral bg-coral/10 border border-coral/30 rounded-full px-3 py-1">
              Control Room
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden sm:inline text-sm text-cream/60 font-medium" data-testid="mod-email">{user?.email}</span>
            {user?.picture && <img src={user.picture} alt="" className="w-8 h-8 rounded-full border border-cream/20" />}
            <button onClick={logout} data-testid="logout-btn" className="inline-flex items-center gap-2 text-sm font-bold text-cream/70 hover:text-coral transition-colors">
              <LogOut size={16} /> <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-5 sm:px-8 py-8">
        {/* stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard label="Live Entries" value={stats.live} accent="text-cream" testid="stat-live" />
          <StatCard label="Pending" value={stats.pending} accent="text-coral" testid="stat-pending" />
          <StatCard label="Rejected" value={stats.rejected} accent="text-cream/60" testid="stat-rejected" />
          <StatCard label="Total Submissions" value={stats.total} accent="text-gold" testid="stat-total" />
        </div>

        {/* tabs */}
        <div className="flex flex-wrap gap-2 mb-6 border-b border-cream/10">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              data-testid={`tab-${t.key}`}
              className={`px-4 py-3 font-bold text-sm border-b-2 -mb-px transition-colors ${
                tab === t.key ? "border-coral text-coral" : "border-transparent text-cream/50 hover:text-cream"
              }`}
            >
              {t.label}
              {t.key === "pending" && stats.pending > 0 && (
                <span className="ml-2 rounded-full bg-coral text-cream text-xs px-2 py-0.5">{stats.pending}</span>
              )}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-40 rounded-xl shimmer" />)}
          </div>
        ) : tab === "moderators" ? (
          <ModeratorsPanel mods={mods} me={meEmail} onAdd={addModerator} newMod={newMod} setNewMod={setNewMod} onRemove={removeModerator} />
        ) : entries.length === 0 ? (
          <div className="text-center py-20" data-testid="dash-empty">
            <div className="text-5xl mb-3">{tab === "pending" ? "✅" : "🗂️"}</div>
            <p className="font-display font-bold text-lg text-cream">
              {tab === "pending" ? "Queue is clear. No pending submissions." : `No ${tab} entries.`}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5" data-testid="entries-list">
            {entries.map((entry) => (
              <div key={entry.id} className="rounded-xl border border-cream/10 bg-cream/[0.03] p-5" data-testid={`dash-entry-${entry.id}`}>
                <div className="flex items-start gap-3">
                  <CompanyLogo domain={entry.company_domain} name={entry.company_name} size={44} />
                  <div className="flex-1 min-w-0">
                    <h3 className="font-display font-extrabold text-cream truncate">{entry.company_name}</h3>
                    <p className="text-xs text-cream/60 truncate">{entry.person_name}{entry.person_title ? ` · ${entry.person_title}` : ""}</p>
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-wide text-cream/40">{fmt(entry.created_at)}</span>
                </div>

                <p className="mt-3 font-display italic text-cream/90 text-sm leading-snug line-clamp-3">“{entry.quote}”</p>

                <div className="mt-3 flex flex-wrap items-center gap-2">
                  {entry.sources?.map((s, i) => (
                    <a key={i} href={s.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-[11px] font-bold rounded-full bg-navy border border-cream/15 px-2.5 py-1 text-cream/70 hover:text-coral hover:border-coral/40 transition-colors">
                      {s.label} <ExternalLink size={10} />
                    </a>
                  ))}
                  {entry.statement_date && <span className="text-[11px] text-cream/40">· said {fmt(entry.statement_date)}</span>}
                </div>

                {entry.submitter_email && (
                  <p className="mt-2 text-[11px] text-cream/40 flex items-center gap-1"><Mail size={11} /> {entry.submitter_email}</p>
                )}
                {entry.status === "rejected" && entry.rejection_reason && (
                  <p className="mt-2 text-xs text-coral/80">Rejected: {entry.rejection_reason}</p>
                )}
                {entry.status === "approved" && (
                  <div className="mt-3"><FlagScore score={entry.red_flag_score} size="text-base" /></div>
                )}

                {/* actions */}
                <div className="mt-4 pt-4 border-t border-cream/10">
                  {tab === "pending" && (
                    <>
                      <div className="flex items-center gap-1 mb-3" data-testid={`quick-score-${entry.id}`}>
                        <span className="text-[11px] font-bold text-cream/50 mr-1">Score:</span>
                        {[1, 2, 3, 4, 5].map((n) => {
                          const cur = scores[entry.id] || 3;
                          return (
                            <button key={n} onClick={() => setScores((s) => ({ ...s, [entry.id]: n }))} className={`text-lg hover:scale-125 transition-transform ${n <= cur ? "" : "opacity-25 grayscale"}`} data-testid={`quick-score-${entry.id}-${n}`}>🚩</button>
                          );
                        })}
                        <span className="ml-1 text-xs font-bold text-cream/50">{scores[entry.id] || 3}/5</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <button onClick={() => approve(entry, scores[entry.id] || 3)} data-testid={`approve-btn-${entry.id}`} className="inline-flex items-center gap-1.5 rounded-full bg-coral px-4 py-2 text-xs font-bold text-cream hover:bg-coral-dark transition-colors">
                          <Check size={14} /> Approve
                        </button>
                        <button onClick={() => reject(entry)} data-testid={`reject-btn-${entry.id}`} className="inline-flex items-center gap-1.5 rounded-full border border-cream/20 px-4 py-2 text-xs font-bold text-cream/80 hover:border-coral hover:text-coral transition-colors">
                          <Ban size={14} /> Reject
                        </button>
                        <button onClick={() => setEditing({ entry, approveMode: true })} data-testid={`edit-approve-btn-${entry.id}`} className="inline-flex items-center gap-1.5 rounded-full border border-cream/20 px-4 py-2 text-xs font-bold text-cream/80 hover:border-cream transition-colors">
                          <Pencil size={14} /> Edit & Review
                        </button>
                      </div>
                    </>
                  )}

                  {tab === "approved" && (
                    <div className="flex flex-wrap gap-2">
                      <Link to={`/entry/${entry.slug}`} target="_blank" data-testid={`view-btn-${entry.id}`} className="inline-flex items-center gap-1.5 rounded-full border border-cream/20 px-4 py-2 text-xs font-bold text-cream/80 hover:border-cream transition-colors">
                        <ExternalLink size={14} /> View
                      </Link>
                      <button onClick={() => setEditing({ entry, approveMode: false })} data-testid={`edit-btn-${entry.id}`} className="inline-flex items-center gap-1.5 rounded-full border border-cream/20 px-4 py-2 text-xs font-bold text-cream/80 hover:border-cream transition-colors">
                        <Pencil size={14} /> Edit
                      </button>
                      <button onClick={() => unpublish(entry)} data-testid={`unpublish-btn-${entry.id}`} className="inline-flex items-center gap-1.5 rounded-full border border-cream/20 px-4 py-2 text-xs font-bold text-cream/80 hover:border-coral hover:text-coral transition-colors">
                        <EyeOff size={14} /> Unpublish
                      </button>
                    </div>
                  )}

                  {tab === "rejected" && (
                    <div className="flex flex-wrap gap-2">
                      <button onClick={() => setEditing({ entry, approveMode: true })} data-testid={`reapprove-btn-${entry.id}`} className="inline-flex items-center gap-1.5 rounded-full bg-coral px-4 py-2 text-xs font-bold text-cream hover:bg-coral-dark transition-colors">
                        <Check size={14} /> Review & Approve
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {editing && (
        <EntryEditorModal
          entry={editing.entry}
          approveMode={editing.approveMode}
          saving={saving}
          onClose={() => setEditing(null)}
          onSave={saveEdit}
        />
      )}
    </div>
  );
}

function ModeratorsPanel({ mods, me, onAdd, newMod, setNewMod, onRemove }) {
  return (
    <div className="max-w-2xl" data-testid="moderators-panel">
      <form onSubmit={onAdd} className="flex flex-col sm:flex-row gap-3 mb-7">
        <input
          type="email"
          value={newMod}
          onChange={(e) => setNewMod(e.target.value)}
          placeholder="new.moderator@email.com"
          data-testid="add-mod-input"
          className="flex-1 bg-navy/40 border border-cream/15 text-cream placeholder:text-cream/35 rounded-full px-5 py-3 focus:outline-none focus:ring-2 focus:ring-coral"
        />
        <button type="submit" data-testid="add-mod-btn" className="inline-flex items-center justify-center gap-2 rounded-full bg-coral px-6 py-3 font-bold text-cream hover:bg-coral-dark transition-colors">
          <UserPlus size={16} /> Add Moderator
        </button>
      </form>

      <div className="space-y-2" data-testid="mods-list">
        {mods.map((m) => (
          <div key={m.email} className="flex items-center justify-between rounded-xl border border-cream/10 bg-cream/[0.03] px-4 py-3" data-testid={`mod-row-${m.email}`}>
            <div className="flex items-center gap-3 min-w-0">
              {m.picture ? <img src={m.picture} alt="" className="w-9 h-9 rounded-full" /> : <div className="w-9 h-9 rounded-full bg-coral/15 text-coral flex items-center justify-center font-bold">{m.email[0]?.toUpperCase()}</div>}
              <div className="min-w-0">
                <p className="font-bold text-cream text-sm truncate">{m.email} {m.email === me && <span className="text-coral text-xs">(you)</span>}</p>
                <p className="text-[11px] text-cream/40">
                  {m.name ? `${m.name} · ` : ""}{m.added_by === "bootstrap" ? "Founding moderator" : `Added by ${m.added_by}`}
                </p>
              </div>
            </div>
            {m.email !== me && (
              <button onClick={() => onRemove(m.email)} data-testid={`remove-mod-${m.email}`} className="text-cream/50 hover:text-coral p-2" aria-label="Remove moderator">
                <Trash2 size={16} />
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
