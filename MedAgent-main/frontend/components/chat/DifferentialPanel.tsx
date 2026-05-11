"use client";

import {
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Stethoscope,
} from "lucide-react";
import { useState } from "react";

interface Branch {
  hypothesis: string;
  probability: number;
  reasoning: string;
  supporting_evidence: string[];
  contradicting_evidence: string[];
  recommended_action: string;
  urgency: "emergency" | "urgent" | "routine";
  color: string;
}

interface DifferentialPanelProps {
  branches: Branch[];
}

function BranchCard({ branch, index }: { branch: Branch; index: number }) {
  const [expanded, setExpanded] = useState(index === 0);
  const pct = Math.round(branch.probability * 100);

  return (
    <div
      className="rounded-xl border border-border bg-card overflow-hidden shadow-sm"
      style={{ borderColor: branch.color + "40" }}
    >
      {/* Header */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-muted/50 transition-colors"
      >
        <span
          className="flex-shrink-0 w-8 h-8 rounded-full grid place-items-center text-xs font-bold text-white"
          style={{ backgroundColor: branch.color }}
        >
          {index + 1}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-foreground truncate">
              {branch.hypothesis}
            </span>
            {branch.urgency === "emergency" && (
              <AlertTriangle className="h-3.5 w-3.5 text-emergency flex-shrink-0" />
            )}
          </div>
          {/* Confidence bar */}
          <div className="mt-1.5 w-full h-1.5 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${pct}%`,
                backgroundColor: branch.color,
              }}
            />
          </div>
        </div>
        <span
          className="text-xs font-semibold flex-shrink-0"
          style={{ color: branch.color }}
        >
          {pct}%
        </span>
        {expanded ? (
          <ChevronUp className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
        )}
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-border pt-3">
          {/* Reasoning */}
          <div>
            <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wide">
              Clinical Reasoning
            </span>
            <p className="mt-1 text-[13px] leading-relaxed text-foreground">
              {branch.reasoning}
            </p>
          </div>

          {/* Supporting evidence */}
          {branch.supporting_evidence.length > 0 && (
            <div>
              <span className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wide">
                Supporting Evidence
              </span>
              <ul className="mt-1 space-y-0.5">
                {branch.supporting_evidence.map((e, i) => (
                  <li
                    key={i}
                    className="text-[13px] text-foreground flex items-start gap-1.5"
                  >
                    <span className="mt-1.5 w-1 h-1 rounded-full bg-emerald-400 flex-shrink-0" />
                    {e}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Contradicting evidence */}
          {branch.contradicting_evidence.length > 0 && (
            <div>
              <span className="text-[11px] font-semibold text-amber-600 dark:text-amber-400 uppercase tracking-wide">
                Contradicting Evidence
              </span>
              <ul className="mt-1 space-y-0.5">
                {branch.contradicting_evidence.map((e, i) => (
                  <li
                    key={i}
                    className="text-[13px] text-foreground flex items-start gap-1.5"
                  >
                    <span className="mt-1.5 w-1 h-1 rounded-full bg-amber-400 flex-shrink-0" />
                    {e}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommended action */}
          <div
            className="rounded-lg px-3 py-2 text-[13px] font-medium"
            style={{
              backgroundColor: branch.color + "15",
              color: branch.color,
            }}
          >
            <span className="font-semibold">Recommended: </span>
            {branch.recommended_action}
          </div>
        </div>
      )}
    </div>
  );
}

export function DifferentialPanel({ branches }: DifferentialPanelProps) {
  if (!branches || branches.length === 0) return null;

  return (
    <div className="rounded-2xl border border-border bg-card overflow-hidden shadow-sm">
      <div className="flex items-center gap-2 px-4 py-3 bg-[linear-gradient(135deg,#667eea,#764ba2)]">
        <Stethoscope className="h-4 w-4 text-white" />
        <span className="text-sm font-semibold text-white">
          Differential Diagnosis — {branches.length} hypotheses
        </span>
      </div>
      <div className="p-3 space-y-2">
        {branches.map((branch, i) => (
          <BranchCard key={i} branch={branch} index={i} />
        ))}
      </div>
    </div>
  );
}
