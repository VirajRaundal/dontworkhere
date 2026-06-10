import React from "react";
import { Link } from "react-router-dom";
import Logo from "@/components/Logo";

export const Footer = () => {
  return (
    <footer className="border-t border-cream/10 bg-navy/60">
      <div className="max-w-7xl mx-auto px-5 sm:px-8 py-12">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div>
            <Logo size="text-xl" />
            <p className="mt-3 text-sm text-cream/50 max-w-md">
              A community-powered accountability directory.
            </p>
          </div>
          <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm font-semibold text-cream/70">
            <Link to="/" className="hover:text-coral transition-colors" data-testid="footer-directory">Directory</Link>
            <Link to="/submit" className="hover:text-coral transition-colors" data-testid="footer-submit">Raise a Flag</Link>
          </div>
        </div>
        <div className="mt-8 pt-6 border-t border-cream/10 text-xs text-cream/40">
          Sample entries shown for demo purposes are fictional and satirical. Submitted entries are reviewed by moderators before publishing.
        </div>
      </div>
    </footer>
  );
};

export default Footer;
