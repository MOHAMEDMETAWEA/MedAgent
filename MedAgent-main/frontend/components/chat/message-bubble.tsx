"use client";

import type { ChatEvent } from "@/lib/api/chat";
import { cn } from "@/lib/utils";
import {
  Activity,
  AlertTriangle,
  Baby,
  BarChart3,
  BookOpen,
  Brain,
  CheckCircle2,
  ClipboardList,
  Crosshair,
  Eye,
  FileText,
  FlaskConical,
  Heart,
  Microscope,
  ShieldAlert,
  Stethoscope,
  User,
} from "lucide-react";

type Props = {
  role: "user" | "assistant" | "tool" | "system";
  content: string;
  events?: ChatEvent[];
  senderName?: string;
  modelColor?: string;
  reasoning?: ReasoningStep[];
  imagePreview?: string;
};

const MODEL_COLORS: Record<string, string> = {
  "Qwen 3 32B": "#10B981",
  "Qwen 2.5 72B": "#8B5CF6",
  "Allam 2 7B": "#059669",
  "Llama 3.3 70B": "#6366F1",
  "Llama 4 Scout 17B": "#4F46E5",
  "Llama 3.1 8B": "#818CF8",
  "GPT-4o": "#2563EB",
  "GPT-4o Mini": "#3B82F6",
  "GPT-4.1": "#1D4ED8",
  "Claude 3.5 Sonnet": "#D97706",
  "Gemini 2.5 Flash": "#F59E0B",
  "Gemini 2.5 Pro": "#D97706",
  "DeepSeek V3": "#0EA5E9",
  "Llama 4 Maverick": "#7C3AED",
};

const DEFAULT_COLOR = "#6B7280";

function getModelColor(name: string): string {
  return MODEL_COLORS[name] || DEFAULT_COLOR;
}

export type ReasoningStep = { tool: string; result: string };

export function buildReasoningSteps(events: ChatEvent[]): ReasoningStep[] {
  const steps: ReasoningStep[] = [];
  const seen = new Set<string>();

  for (const event of events) {
    if (event.type === "tool_result") {
      const tool = (event.data?.tool as string) || "";
      if (!tool || seen.has(tool)) continue;
      seen.add(tool);

      const result = event.data?.result as Record<string, unknown> | undefined;
      if (!result) continue;

      let summary = "";

      if (tool === "detect_red_flags") {
        const flags = result.flags;
        if (Array.isArray(flags) && flags.length > 0) {
          const flagTexts = flags.map((f: unknown) => {
            if (typeof f === "string") return f;
            if (typeof f === "object" && f !== null) return (f as Record<string, string>).text || (f as Record<string, string>).name || (f as Record<string, string>).keyword || String(f);
            return String(f);
          });
          summary = `⚠️ ${flagTexts.join("، ")}`;
        } else {
          summary = "لا توجد علامات طارئة";
        }
      } else if (tool === "score_triage") {
        const level = (result.level as string) || "?";
        const score = result.score as number || 0;
        summary = `${level} · Score ${score}`;
      } else if (tool === "retrieve_medical_knowledge") {
        const chunks = result.chunks as Array<{ title?: string }> | undefined;
        summary = chunks?.length ? `تم العثور على ${chunks.length} مصادر` : "لا توجد نتائج";
      } else if (tool === "check_medication_interactions") {
        const interactions = result.interactions as Array<unknown> | undefined;
        summary = interactions?.length ? `تم العثور على ${interactions.length} تفاعلات` : "لا توجد تفاعلات";
      } else {
        const err = result.error as string | undefined;
        summary = err ? `خطأ: ${err}` : "اكتمل";
      }

      steps.push({ tool, result: summary });
    }
  }

  return steps;
}

export function MessageBubble({ role, content, events, senderName, modelColor, reasoning, imagePreview }: Props) {
  const isUser = role === "user";
  const hasTriage = events?.some((e) => e.type === "triage");
  const hasRedFlag = events?.some((e) => e.type === "red_flag");

  const initials = senderName ? senderName.split(" ").map((s) => s[0]).join("").slice(0, 2).toUpperCase() : "";
  const color = modelColor || getModelColor(senderName || "");



  return (
    <div className={cn("flex gap-3 mb-6", isUser && "flex-row-reverse")}>
      {/* Avatar */}
      <div
        className={cn(
          "flex-shrink-0 grid place-items-center w-9 h-9 rounded-xl text-[11px] font-bold text-white shadow-sm",
        )}
        style={{ background: isUser ? "linear-gradient(135deg, #4B5563, #374151)" : `linear-gradient(135deg, ${color}, ${color}dd)` }}
      >
        {isUser ? (
          senderName ? initials : <User className="h-4 w-4" />
        ) : (
          <Stethoscope className="h-4 w-4" />
        )}
      </div>

      {/* Content */}
      <div className="max-w-[80%] space-y-2.5">
        {/* Sender name */}
        {senderName && !isUser && (
          <p className="text-xs font-semibold px-1" style={{ color }}>{senderName}</p>
        )}

        {/* Red flag alert */}
        {hasRedFlag && (
          <div className="flex items-center gap-2.5 text-[13px] font-semibold text-white rounded-xl px-4 py-3 shadow-sm" style={{ background: `linear-gradient(135deg, ${color}, #DC2626)` }}>
            <AlertTriangle className="h-4 w-4 flex-shrink-0" />
            Emergency — seek immediate care
          </div>
        )}

        {/* Attached image preview (user only) */}
        {isUser && imagePreview && (
          <div className="overflow-hidden rounded-2xl rounded-br-md border border-border max-w-[260px] shadow-sm">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={imagePreview} alt="Uploaded medical image" className="w-full h-auto object-cover max-h-[260px]" />
          </div>
        )}

        {/* Message text */}
        {content && (
          <div
            className={cn(
              "px-4 py-3 text-sm leading-relaxed shadow-sm",
              isUser
                ? "rounded-2xl rounded-br-md bg-[#374151] text-white"
                : "rounded-2xl rounded-bl-md bg-card border border-border text-foreground"
            )}
          >
            <span className="whitespace-pre-wrap">{content}</span>
          </div>
        )}

        {/* Triage card */}
        {hasTriage && (
          <div className="rounded-xl overflow-hidden border border-border bg-card shadow-sm" style={{ borderLeftColor: color, borderLeftWidth: 3 }}>
            <div className="flex items-center gap-2 px-4 py-2.5 text-[12px] font-semibold text-white" style={{ background: `linear-gradient(90deg, ${color}, ${color}cc)` }}>
              <Activity className="h-3.5 w-3.5" />
              {(events?.find((e) => e.type === "triage")?.data?.level as string)?.toUpperCase() || "TRIAGE"} · Score {String(events?.find((e) => e.type === "triage")?.data?.score ?? "—")}
            </div>
            <div className="p-4 text-[13px] text-foreground/80 space-y-1.5">
              <p>{String(events?.find((e) => e.type === "triage")?.data?.reasoning || "Assessment complete.")}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className="flex gap-3 mb-6">
      <div className="flex-shrink-0 grid place-items-center w-9 h-9 rounded-xl text-[11px] font-bold text-white shadow-sm" style={{ background: "linear-gradient(135deg, #6B7280, #9CA3AF)" }}>
        <Stethoscope className="h-4 w-4" />
      </div>
      <div className="rounded-2xl rounded-bl-md bg-card border border-border px-4 py-3 shadow-sm">
        <div className="flex gap-1">
          {[0, 1, 2].map((i) => (
            <span key={i} className="w-1.5 h-1.5 rounded-full bg-muted-foreground/40 animate-[typing_1.4s_ease-in-out_infinite_both]" style={{ animationDelay: `${-0.32 + i * 0.16}s` }} />
          ))}
        </div>
      </div>
    </div>
  );
}
