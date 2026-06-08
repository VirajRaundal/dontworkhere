import React from "react";

// Renders 1-5 red flags representing the Red Flag Score.
export const FlagScore = ({ score = 0, size = "text-xl", showEmpty = true, className = "" }) => {
  const s = Math.max(0, Math.min(5, score || 0));
  return (
    <div
      className={`inline-flex items-center gap-0.5 ${size} ${className}`}
      data-testid="flag-score"
      title={`Red Flag Score: ${s}/5`}
      aria-label={`Red Flag Score ${s} of 5`}
    >
      {Array.from({ length: 5 }).map((_, i) => (
        <span
          key={i}
          className={i < s ? "" : "opacity-20 grayscale"}
          style={{ display: !showEmpty && i >= s ? "none" : "inline" }}
        >
          🚩
        </span>
      ))}
    </div>
  );
};

export default FlagScore;
