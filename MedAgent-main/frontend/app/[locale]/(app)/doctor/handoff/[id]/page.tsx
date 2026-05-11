"use client";

import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle,
  Download,
  ListChecks,
  Lock,
  Play,
  Printer,
  Square,
} from "lucide-react";
import { useTranslations } from "next-intl";
import { use, useCallback, useEffect, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiRequest } from "@/lib/api/client";
import { useAuthStore } from "@/store/auth";
import { useRouter } from "@/src/i18n/navigation";

type HandoffStatus = "new" | "acknowledged" | "in_progress" | "reviewed" | "closed";

type Handoff = {
  id: string;
  conversation_id: string;
  patient_user_id: string;
  status: HandoffStatus;
  priority: number;
  target_specialty: string | null;
  target_language: string | null;
  auto_routed: boolean;
  sent_at: string | null;
  acknowledged_at: string | null;
  reviewed_at: string | null;
  closed_at: string | null;
  doctor_private_notes: string | null;
  summary_markdown: string;
  created_at: string;
};

const STATUS_TRANSITIONS: Record<HandoffStatus, HandoffStatus[]> = {
  new: ["acknowledged", "in_progress", "reviewed", "closed"],
  acknowledged: ["in_progress", "reviewed", "closed"],
  in_progress: ["reviewed", "closed"],
  reviewed: ["closed"],
  closed: [],
};

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function DoctorHandoffDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const t = useTranslations("doctor");
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const [handoff, setHandoff] = useState<Handoff | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [savingNotes, setSavingNotes] = useState(false);
  const [savedNotes, setSavedNotes] = useState(false);
  const [updatingStatus, setUpdatingStatus] = useState<HandoffStatus | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [pdfNotice, setPdfNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    const res = await apiRequest<Handoff>(`/handoffs/${id}`, { token: accessToken });
    if (res.data) {
      setHandoff(res.data);
      setNotes(res.data.doctor_private_notes || "");
      if (res.data.reviewed_at) setSavedNotes(true);
    } else {
      setLoadError(res.error || "load_failed");
    }
    setLoading(false);
  }, [id, accessToken]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  const handleSaveNotes = async () => {
    if (!handoff) return;
    setSavingNotes(true);
    await apiRequest(`/handoffs/${handoff.id}/review`, {
      method: "POST",
      body: { notes },
      token: accessToken,
    });
    setSavingNotes(false);
    setSavedNotes(true);
    await load();
  };

  const transitionTo = async (next: HandoffStatus) => {
    if (!handoff) return;
    setStatusError(null);
    setUpdatingStatus(next);
    const res = await apiRequest<{ status: HandoffStatus }>(
      `/handoffs/${handoff.id}/status`,
      {
        method: "PATCH",
        body: { status: next },
        token: accessToken,
      },
    );
    setUpdatingStatus(null);
    if (res.error || res.status >= 400) {
      setStatusError(t("handoff.actions.transitionError"));
      return;
    }
    await load();
  };

  const handleDownloadOrPrint = async () => {
    if (!handoff || !accessToken) return;
    setPdfNotice(null);
    const res = await fetch(`${API}/handoffs/${handoff.id}/pdf`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    if (!res.ok) {
      setPdfNotice(t("inbox.loadFailed"));
      return;
    }
    const contentType = res.headers.get("content-type") || "";
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    if (contentType.startsWith("application/pdf")) {
      const a = document.createElement("a");
      a.href = url;
      a.download = `handoff_${handoff.id}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      return;
    }
    setPdfNotice(t("inbox.pdfUnavailableToast"));
    const win = window.open(url, "_blank", "noopener,noreferrer");
    if (win) {
      win.addEventListener("load", () => {
        try {
          win.focus();
          win.print();
        } catch {
          // ignore
        }
        win.addEventListener(
          "afterprint",
          () => URL.revokeObjectURL(url),
          { once: true },
        );
      });
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } else {
      URL.revokeObjectURL(url);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (loadError || !handoff) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 p-6 text-center">
        <AlertTriangle className="h-10 w-10 text-amber-500" />
        <div>
          <p className="font-semibold text-foreground">
            {loadError ? t("inbox.loadFailed") : "Handoff not found"}
          </p>
          <p className="mt-1 text-sm text-ink-3">ID: <span className="font-mono">{id}</span></p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => router.push("/doctor/inbox")}
            className="inline-flex items-center gap-1.5 rounded-lg bg-base-2 px-4 py-2 text-sm font-semibold text-ink-2 hover:bg-line"
          >
            <ArrowLeft className="h-4 w-4" />
            {t("handoff.backToInbox")}
          </button>
          <button
            onClick={load}
            className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:opacity-90"
          >
            {t("inbox.retry")}
          </button>
        </div>
      </div>
    );
  }

  const status = handoff.status || "new";
  const allowed = STATUS_TRANSITIONS[status] ?? [];
  const canTransition = (target: HandoffStatus) => allowed.includes(target);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6 p-6 print:p-0 print:space-y-3"
    >
      <div className="flex flex-wrap items-center justify-between gap-3 print:hidden">
        <button
          onClick={() => router.push("/doctor/inbox")}
          className="inline-flex items-center gap-2 text-sm font-medium text-ink-3 transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          {t("handoff.backToInbox")}
        </button>
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => window.print()}
            className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-card px-3 py-2 text-sm font-semibold text-ink-2 transition-colors hover:border-primary/40 hover:text-primary"
          >
            <Printer className="h-4 w-4" />
            {t("inbox.print")}
          </button>
          <button
            onClick={handleDownloadOrPrint}
            className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
          >
            <Download className="h-4 w-4" />
            {t("inbox.downloadPdf")}
          </button>
        </div>
      </div>

      {pdfNotice && (
        <div className="flex items-start gap-2 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900 print:hidden dark:border-amber-700 dark:bg-amber-950/40 dark:text-amber-200">
          <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          <p className="flex-1">{pdfNotice}</p>
          <button
            onClick={() => setPdfNotice(null)}
            className="text-xs font-medium underline-offset-2 hover:underline"
          >
            ✕
          </button>
        </div>
      )}

      <div>
        <h1 className="font-display text-2xl font-bold text-foreground sm:text-3xl">
          {t("handoff.title")}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {new Date(handoff.created_at).toLocaleDateString()} · Sent:{" "}
          {handoff.sent_at ? new Date(handoff.sent_at).toLocaleString() : "—"} ·{" "}
          <span className="font-medium text-foreground">
            {t(`inbox.status.${handoff.status || "new"}`)}
          </span>
        </p>
      </div>

      {/* Workflow actions */}
      <Card className="print:hidden">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ListChecks className="h-5 w-5" />
            {t("handoff.actions.title")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap gap-2">
            <ActionButton
              icon={<CheckCircle className="h-4 w-4" />}
              label={t("handoff.actions.acknowledge")}
              disabled={!canTransition("acknowledged")}
              loading={updatingStatus === "acknowledged"}
              onClick={() => transitionTo("acknowledged")}
            />
            <ActionButton
              icon={<Play className="h-4 w-4" />}
              label={t("handoff.actions.start")}
              disabled={!canTransition("in_progress")}
              loading={updatingStatus === "in_progress"}
              onClick={() => transitionTo("in_progress")}
            />
            <ActionButton
              icon={<CheckCircle className="h-4 w-4" />}
              label={t("handoff.actions.markReviewed")}
              disabled={!canTransition("reviewed")}
              loading={updatingStatus === "reviewed"}
              onClick={() => transitionTo("reviewed")}
            />
            <ActionButton
              icon={<Square className="h-4 w-4" />}
              label={t("handoff.actions.close")}
              disabled={!canTransition("closed")}
              loading={updatingStatus === "closed"}
              onClick={() => transitionTo("closed")}
            />
          </div>
          {statusError && <p className="text-sm text-red-600">{statusError}</p>}
          {handoff.status === "closed" && (
            <p className="inline-flex items-center gap-1.5 text-sm text-ink-4">
              <Lock className="h-3.5 w-3.5" />
              {t("inbox.status.closed")}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Patient info */}
      <Card>
        <CardHeader>
          <CardTitle>{t("handoff.patientInfo")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 text-sm sm:grid-cols-2">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-ink-4">
                Patient ID
              </p>
              <p className="font-mono text-ink-2">{handoff.patient_user_id}</p>
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-ink-4">
                Conversation ID
              </p>
              <p className="font-mono text-ink-2">{handoff.conversation_id}</p>
            </div>
            {handoff.target_specialty && (
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-wide text-ink-4">
                  Target specialty
                </p>
                <p className="font-medium text-ink-2">{handoff.target_specialty}</p>
              </div>
            )}
            {handoff.target_language && (
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-wide text-ink-4">
                  Language
                </p>
                <p className="font-medium uppercase text-ink-2">{handoff.target_language}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle>{t("handoff.summary")}</CardTitle>
        </CardHeader>
        <CardContent>
          {handoff.summary_markdown ? (
            <div className="whitespace-pre-wrap text-sm text-ink-2 leading-relaxed max-w-none">
              {handoff.summary_markdown}
            </div>
          ) : (
            <p className="text-sm text-ink-4">No summary available</p>
          )}
        </CardContent>
      </Card>

      {/* Private notes */}
      <Card className="print:hidden">
        <CardHeader>
          <CardTitle>{t("inbox.notes")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder={t("inbox.notesPlaceholder")}
            rows={4}
            className="w-full rounded-xl border border-line bg-card p-4 text-sm text-foreground outline-none focus:border-primary"
          />
          <div className="flex items-center gap-3">
            <button
              onClick={handleSaveNotes}
              disabled={savingNotes}
              className="inline-flex items-center gap-1.5 rounded-full bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-60"
            >
              {savingNotes ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
              ) : (
                <CheckCircle className="h-4 w-4" />
              )}
              {t("inbox.saveNotes")}
            </button>
            {savedNotes && (
              <span className="text-sm font-medium text-emerald-600">
                {t("inbox.saved")}
              </span>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function ActionButton({
  icon,
  label,
  disabled,
  loading,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  disabled: boolean;
  loading: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className="inline-flex items-center gap-1.5 rounded-full bg-primary-tint px-4 py-2 text-sm font-semibold text-primary transition-colors hover:bg-primary/10 disabled:cursor-not-allowed disabled:opacity-40"
    >
      {loading ? (
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      ) : (
        icon
      )}
      {label}
    </button>
  );
}
