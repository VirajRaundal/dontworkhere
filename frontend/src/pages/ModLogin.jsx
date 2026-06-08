import React, { useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, ShieldCheck } from "lucide-react";
import Logo from "@/components/Logo";
import { useAuth } from "@/context/AuthContext";

export default function ModLogin() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && user) navigate("/mod/dashboard", { replace: true });
  }, [user, loading, navigate]);

  const handleLogin = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + "/mod/dashboard";
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <div className="App min-h-screen flex flex-col hero-glow">
      <div className="px-5 sm:px-8 py-6">
        <Link to="/" className="inline-flex items-center gap-2 text-cream/60 hover:text-coral font-semibold text-sm transition-colors" data-testid="login-back-link">
          <ArrowLeft size={16} /> Back to site
        </Link>
      </div>

      <div className="flex-1 flex items-center justify-center px-5 pb-20">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md text-center"
        >
          <div className="mb-8 flex justify-center">
            <Logo size="text-3xl" />
          </div>

          <div className="bg-cream/[0.04] border border-cream/10 rounded-3xl p-9 backdrop-blur-xl">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-coral/15 text-coral mb-5">
              <ShieldCheck size={28} />
            </div>
            <h1 className="font-display font-black text-3xl text-cream tracking-tight">Moderator Access</h1>
            <p className="mt-3 text-cream/60 text-sm">
              Sign in to review submissions and manage the directory. Restricted to approved moderators only.
            </p>

            <button
              onClick={handleLogin}
              data-testid="google-login-btn"
              className="mt-8 w-full inline-flex items-center justify-center gap-3 rounded-full bg-cream text-navy px-6 py-3.5 font-bold hover:bg-white transition-colors"
            >
              <svg width="20" height="20" viewBox="0 0 48 48" aria-hidden>
                <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.4 29.3 35 24 35c-6.1 0-11-4.9-11-11s4.9-11 11-11c2.8 0 5.4 1.1 7.3 2.8l5.7-5.7C33.6 6.1 29.1 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.3-.4-3.5z"/>
                <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 16 19 13 24 13c2.8 0 5.4 1.1 7.3 2.8l5.7-5.7C33.6 6.1 29.1 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/>
                <path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35 26.7 36 24 36c-5.3 0-9.7-3.4-11.3-8.1l-6.5 5C9.5 39.6 16.2 44 24 44z"/>
                <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.1-4.1 5.5l6.2 5.2C41.4 36.2 44 30.6 44 24c0-1.3-.1-2.3-.4-3.5z"/>
              </svg>
              Continue with Google
            </button>
          </div>

          <p className="mt-5 text-xs text-cream/40">
            Not a moderator? <Link to="/submit" className="text-coral font-semibold hover:underline">Submit a red flag instead →</Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
