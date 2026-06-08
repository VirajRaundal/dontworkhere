import React from "react";
import { Link } from "react-router-dom";

export const Logo = ({ className = "", size = "text-2xl" }) => {
  return (
    <Link
      to="/"
      data-testid="logo-home-link"
      className={`font-display font-extrabold ${size} tracking-tight flex items-center gap-2 ${className}`}
    >
      <span className="flag-wave text-[1.1em]">🚩</span>
      <span>
        <span className="text-cream">dont</span>
        <span className="text-coral">workhere</span>
      </span>
    </Link>
  );
};

export default Logo;
