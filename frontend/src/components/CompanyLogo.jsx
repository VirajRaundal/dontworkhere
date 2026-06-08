import React, { useState } from "react";
import { clearbitLogo } from "@/lib/api";

// Company logo via Clearbit, with a 🏢 emoji fallback.
export const CompanyLogo = ({ domain, name, size = 56 }) => {
  const [failed, setFailed] = useState(false);
  const url = clearbitLogo(domain);

  if (!url || failed) {
    return (
      <div
        className="flex items-center justify-center rounded-xl bg-navy/5 border border-navy/10 shrink-0"
        style={{ width: size, height: size, fontSize: size * 0.5 }}
        data-testid="company-logo-fallback"
        title={name}
      >
        🏢
      </div>
    );
  }

  return (
    <img
      src={url}
      alt={name ? `${name} logo` : "Company logo"}
      onError={() => setFailed(true)}
      className="rounded-xl object-contain bg-white border border-navy/10 shrink-0 p-1"
      style={{ width: size, height: size }}
      data-testid="company-logo"
    />
  );
};

export default CompanyLogo;
