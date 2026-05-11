"use client";

import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle, Eye, ImageIcon, Info } from "lucide-react";
import { useState } from "react";
import { springSmooth } from "@/lib/motion";

export interface VisionResult {
  findings: string[];
  urgency: "emergency" | "urgent" | "routine" | "none";
  confidence: number;
  disclaimer: string;
  imageUrl?: string;
}

interface Props {
  result: VisionResult;
}

const urgencyConfig = {
  emergency: { icon: AlertTriangle, color: "text-emergency", bg: "bg-emergency/10", label: "Urgent Review Needed" },
  urgent: { icon: Info, color: "text-urgent", bg: "bg-urgent/10", label: "Prompt Review" },
  routine: { icon: CheckCircle, color: "text-routine", bg: "bg-routine/10", label: "Routine" },
  none: { icon: Info, color: "text-ink-3", bg: "bg-muted", label: "No urgency detected" },
};

export function VisionResultCard({ result }: Props) {
  const [showFull, setShowFull] = useState(false);
  const uc = urgencyConfig[result.urgency];
  const Icon = uc.icon;
  const pct = Math.round(result.confidence * 100);

  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 8 },
        visible: { opacity: 1, y: 0 },
      }}
      initial="hidden"
      animate="visible"
      transition={springSmooth}
      className="rounded-2xl border border-border bg-card overflow-hidden shadow-sm"
    >
      {/* Header */}
      <div className={`flex items-center gap-3 px-4 py-3 ${uc.bg}`}>
        <ImageIcon className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-semibold text-foreground">Image Analysis</span>
        <div className={`ml-auto flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${uc.bg}`}>
          <Icon className={`h-3 w-3 ${uc.color}`} />
          <span className={uc.color}>{uc.label}</span>
        </div>
      </div>

      {/* Image thumbnail */}
      {result.imageUrl && (
        <div className="relative">
          <img
            src={result.imageUrl}
            alt="Analyzed"
            className="w-full h-32 object-cover cursor-pointer"
            onClick={() => setShowFull(true)}
          />
          <button
            type="button"
            onClick={() => setShowFull(true)}
            className="absolute bottom-2 right-2 flex items-center gap-1 rounded-lg bg-black/60 px-2 py-1 text-[11px] text-white"
          >
            <Eye className="h-3 w-3" /> View full
          </button>
        </div>
      )}

      <div className="px-4 py-3 space-y-2.5">
        {/* Confidence bar */}
        <div>
          <div className="flex justify-between text-[11px] text-muted-foreground mb-1">
            <span>Confidence</span>
            <span className="tabular-nums">{pct}%</span>
          </div>
          <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
            <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${pct}%` }} />
          </div>
        </div>

        {/* Findings */}
        {result.findings.length > 0 && (
          <div>
            <span className="text-[11px] font-semibold text-muted-foreground uppercase">Findings</span>
            <ul className="mt-1 space-y-0.5">
              {result.findings.map((f, i) => (
                <li key={i} className="flex items-start gap-1.5 text-[13px] text-foreground">
                  <span className="mt-1.5 w-1 h-1 rounded-full bg-primary flex-shrink-0" />
                  {f}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Disclaimer */}
        <div className="flex items-start gap-2 rounded-lg bg-emergency/5 p-2.5 text-[11px] leading-relaxed text-muted-foreground">
          <AlertTriangle className="mt-0.5 h-3 w-3 flex-shrink-0 text-emergency" />
          {result.disclaimer}
        </div>
      </div>

      {/* Full image modal */}
      {showFull && result.imageUrl && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
          onClick={() => setShowFull(false)}
        >
          <img src={result.imageUrl} alt="Full size" className="max-h-[90vh] max-w-full rounded-xl object-contain" />
        </div>
      )}
    </motion.div>
  );
}
