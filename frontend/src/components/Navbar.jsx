import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import Logo from "@/components/Logo";
import { Menu, X } from "lucide-react";

export const Navbar = () => {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const isActive = (p) => location.pathname === p;

  return (
    <nav className="sticky top-0 z-50 bg-navy/80 backdrop-blur-xl border-b border-cream/10">
      <div className="max-w-7xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
        <Logo />

        <div className="hidden md:flex items-center gap-2">
          <Link
            to="/"
            data-testid="nav-directory-link"
            className={`px-4 py-2 rounded-full text-sm font-bold transition-colors ${
              isActive("/") ? "text-coral" : "text-cream/80 hover:text-cream"
            }`}
          >
            Directory
          </Link>
          <Link
            to="/submit"
            data-testid="nav-submit-link"
            className="px-5 py-2.5 rounded-full text-sm font-bold bg-coral text-cream hover:bg-coral-dark transition-colors"
          >
            🚩 Raise a Flag
          </Link>
          <Link
            to="/mod/login"
            data-testid="nav-mod-link"
            className="px-4 py-2 rounded-full text-sm font-bold text-cream/60 hover:text-cream transition-colors"
          >
            Mods
          </Link>
        </div>

        <button
          className="md:hidden text-cream"
          onClick={() => setOpen(!open)}
          data-testid="nav-mobile-toggle"
          aria-label="Toggle menu"
        >
          {open ? <X size={26} /> : <Menu size={26} />}
        </button>
      </div>

      {open && (
        <div className="md:hidden px-5 pb-5 flex flex-col gap-2 border-t border-cream/10 pt-3">
          <Link to="/" onClick={() => setOpen(false)} data-testid="nav-mobile-directory" className="px-4 py-3 rounded-xl font-bold text-cream/90 hover:bg-cream/5">
            Directory
          </Link>
          <Link to="/submit" onClick={() => setOpen(false)} data-testid="nav-mobile-submit" className="px-4 py-3 rounded-xl font-bold bg-coral text-cream text-center">
            🚩 Raise a Flag
          </Link>
          <Link to="/mod/login" onClick={() => setOpen(false)} data-testid="nav-mobile-mod" className="px-4 py-3 rounded-xl font-bold text-cream/70 hover:bg-cream/5">
            Moderators
          </Link>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
