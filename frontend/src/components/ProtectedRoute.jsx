import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-navy text-cream">
        <div className="text-5xl mb-4 flag-wave">🚩</div>
        <p className="font-display font-bold">Checking credentials…</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/mod/login" replace />;
  }

  return children;
}
