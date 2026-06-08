import React from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import CompanyLogo from "@/components/CompanyLogo";
import FlagScore from "@/components/FlagScore";

const fmtDate = (d) => {
  if (!d) return null;
  try {
    return new Date(d).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
  } catch {
    return d;
  }
};

export const RedFlagCard = ({ entry, index = 0 }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: Math.min(index * 0.05, 0.4) }}
      className="h-full"
    >
      <Link
        to={`/entry/${entry.slug}`}
        data-testid={`entry-card-${entry.slug}`}
        className="group block h-full bg-cream text-navy rounded-2xl border-l-4 border-coral shadow-lg hover:shadow-2xl hover:-translate-y-2 transition-all duration-300 ease-out overflow-hidden"
      >
        <div className="p-7 flex flex-col h-full">
          {/* header */}
          <div className="flex items-start gap-4">
            <CompanyLogo domain={entry.company_domain} name={entry.company_name} size={52} />
            <div className="min-w-0 flex-1">
              <h3 className="font-display font-extrabold text-lg leading-tight truncate">
                {entry.company_name}
              </h3>
              <p className="text-sm text-navy/70 truncate">
                {entry.person_name}
                {entry.person_title ? ` · ${entry.person_title}` : ""}
              </p>
            </div>
          </div>

          {/* quote */}
          <div className="relative mt-5 flex-1">
            <span className="quote-mark absolute -top-3 -left-1 text-5xl text-coral/30">“</span>
            <p className="relative font-display italic font-semibold text-lg leading-snug pl-5 pr-1 line-clamp-5">
              {entry.quote}
            </p>
          </div>

          {/* footer */}
          <div className="mt-6 flex items-center justify-between border-t border-navy/10 pt-4">
            <FlagScore score={entry.red_flag_score} size="text-base" />
            <span className="text-xs font-semibold text-navy/50">
              {fmtDate(entry.statement_date) || "—"}
            </span>
          </div>
        </div>
      </Link>
    </motion.div>
  );
};

export default RedFlagCard;
