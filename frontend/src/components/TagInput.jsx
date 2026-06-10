import React, { useState } from "react";
import { X } from "lucide-react";
import { TAG_SUGGESTIONS, normalizeTags } from "@/lib/tags";

// Free-form tag editor with suggestion chips. `value` is a string[]; `onChange`
// receives the normalized string[].
export default function TagInput({ value = [], onChange, max = 6, testid = "tags" }) {
  const [draft, setDraft] = useState("");

  const commit = (next) => onChange(normalizeTags(next, max));

  const add = (raw) => {
    const v = (raw || "").trim();
    if (!v) return;
    commit([...value, v]);
    setDraft("");
  };

  const remove = (tag) => commit(value.filter((t) => t !== tag));

  const onKeyDown = (e) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      add(draft);
    } else if (e.key === "Backspace" && !draft && value.length) {
      remove(value[value.length - 1]);
    }
  };

  const atMax = value.length >= max;

  return (
    <div data-testid={testid}>
      <div className="flex flex-wrap gap-2 mb-2" data-testid={`${testid}-selected`}>
        {value.map((tag) => (
          <span
            key={tag}
            data-testid={`${testid}-chip-${tag}`}
            className="inline-flex items-center gap-1.5 rounded-full bg-coral/15 border border-coral/40 text-coral px-3 py-1 text-xs font-bold"
          >
            {tag}
            <button type="button" onClick={() => remove(tag)} aria-label={`Remove ${tag}`} className="hover:text-coral-dark">
              <X size={12} />
            </button>
          </span>
        ))}
      </div>

      <input
        data-testid={`${testid}-input`}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={onKeyDown}
        onBlur={() => add(draft)}
        disabled={atMax}
        placeholder={atMax ? `Max ${max} tags` : "Add a tag and press Enter…"}
        className="w-full bg-navy/40 border border-cream/15 text-cream placeholder:text-cream/35 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-coral focus:border-coral transition-all disabled:opacity-50"
      />

      {!atMax && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {TAG_SUGGESTIONS.filter((s) => !value.some((v) => v.toLowerCase() === s.toLowerCase())).map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => add(s)}
              data-testid={`${testid}-suggestion-${s}`}
              className="rounded-full border border-cream/15 px-2.5 py-1 text-[11px] font-semibold text-cream/50 hover:text-coral hover:border-coral/40 transition-colors"
            >
              + {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
