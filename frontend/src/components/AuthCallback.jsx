import React, { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";

// REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
export default function AuthCallback() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const hasProcessed = useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const hash = window.location.hash || "";
    const match = hash.match(/session_id=([^&]+)/);
    const sessionId = match ? match[1] : null;

    if (!sessionId) {
      navigate("/mod/login");
      return;
    }

    (async () => {
      try {
        const res = await api.post(
          "/auth/session",
          {},
          { headers: { "X-Session-ID": sessionId } }
        );
        setUser(res.data);
        // clean the hash
        window.history.replaceState(null, "", "/mod/dashboard");
        navigate("/mod/dashboard", { state: { user: res.data } });
      } catch (e) {
        const msg = e?.response?.data?.detail || "Authentication failed";
        toast.error(msg);
        window.history.replaceState(null, "", "/mod/login");
        navigate("/mod/login");
      }
    })();
  }, [navigate, setUser]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-navy text-cream">
      <div className="text-6xl mb-4 flag-wave">🚩</div>
      <p className="font-display text-xl font-bold">Raising your flag…</p>
    </div>
  );
}
