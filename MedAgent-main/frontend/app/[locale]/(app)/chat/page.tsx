"use client";

import { chatApi, type ChatEvent } from "@/lib/api/chat";
import { useAuthStore } from "@/store/auth";
import { MessageBubble, TypingIndicator } from "@/components/chat/message-bubble";
import { ChatComposer, type ComposerAttachment } from "@/components/chat/composer";
import { TriagePanel, triageFromEvents } from "@/components/chat/triage-panel";
import { DifferentialPanel } from "@/components/chat/DifferentialPanel";
import { DoctorSearchDialog } from "@/components/chat/DoctorSearchDialog";
import { Activity, Clock, Hash, MessageSquare, Plus, Search, Send, Sparkles, Trash2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

// Strip Qwen3 thinking tags from response
function cleanResponse(text: string): string {
  return text
    .replace(/<think>/g, "\n💭 ")
    .replace(/<\/think>/g, "\n")
    .replace(/<\/?response>/g, "")
    .trim();
}

function getProviderName(model: string): string {
  if (model.startsWith("groq/")) return "Groq";
  if (model.startsWith("oa/")) return "OpenAI";
  if (model.startsWith("gemini/")) return "Google";
  if (model.startsWith("hf/")) return "HuggingFace";
  return "OpenRouter";
}

function getModelLabel(model: string): string {
  const base = MODEL_LABELS[model] || model;
  const provider = getProviderName(model);
  return `${base} · ${provider}`;
}

const triageBadge: Record<string, string> = {
  emergency: "badge-emergency",
  urgent: "badge-urgent",
  routine: "badge-routine",
};

const MODEL_LABELS: Record<string, string> = {
  "qwen/qwen-2.5-72b-instruct": "Qwen 2.5 72B",
  "openai/gpt-4o": "GPT-4o",
  "anthropic/claude-3.5-sonnet": "Claude 3.5 Sonnet",
  "google/gemini-2.5-flash": "Gemini 2.5 Flash",
  "meta-llama/llama-4-maverick": "Llama 4 Maverick",
  "deepseek/deepseek-chat": "DeepSeek V3",
  "groq/qwen/qwen3-32b": "Qwen 3 32B",
  "groq/allam-2-7b": "Allam 2 7B",
  "groq/llama-3.3-70b-versatile": "Llama 3.3 70B",
  "groq/meta-llama/llama-4-scout-17b-16e-instruct": "Llama 4 Scout 17B",
  "groq/llama-3.1-8b-instant": "Llama 3.1 8B",
  "oa/gpt-4o": "GPT-4o",
  "oa/gpt-4o-mini": "GPT-4o Mini",
  "oa/gpt-4.1": "GPT-4.1",
  "gemini/gemini-2.5-flash": "Gemini 2.5 Flash",
  "gemini/gemini-2.5-pro": "Gemini 2.5 Pro",
  "hf/Qwen/Qwen2.5-72B-Instruct": "Qwen 2.5 72B",
  "hf/meta-llama/Llama-3.1-8B-Instruct": "Llama 3.1 8B",
  "hf/google/gemma-2-9b-it": "Gemma 2 9B",
};

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  thinkingText?: string;
  events?: ChatEvent[];
  modelLabel?: string;
  triageLevel?: string | null;
  triageScore?: number | null;
  latencyMs?: number;
  tokenCount?: number;
  imagePreview?: string;
};

export default function ChatPage() {
  const user = useAuthStore((s) => s.user);
  const accessToken = useAuthStore((s) => s.accessToken);

  const [convId, setConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [currentEvents, setCurrentEvents] = useState<ChatEvent[]>([]);
  const [triageExpanded, setTriageExpanded] = useState(false);
  const [selectedModels, setSelectedModels] = useState<string[]>(["groq/meta-llama/llama-4-scout-17b-16e-instruct"]);
  const [sendToDoctorOpen, setSendToDoctorOpen] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const [convs, setConvs] = useState<Array<{ id: string; title: string | null; triage_level: string | null; updated_at: string }>>([]);
  const [convLoading, setConvLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [portalReady, setPortalReady] = useState(false);

  const isCompareMode = selectedModels.length > 1;
  const triage = triageFromEvents(currentEvents);

  const loadConvs = useCallback(async () => {
    setConvLoading(true);
    const res = await chatApi.listConversations(1);
    if (res.data) setConvs(res.data.items);
    setConvLoading(false);
  }, []);

  useEffect(() => { loadConvs(); }, [loadConvs]);
  useEffect(() => { setPortalReady(true); }, []);
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const loadConversation = async (id: string) => {
    setConvId(id);
    const msgs = await chatApi.getMessages(id);
    if (msgs.data) {
      setMessages(Array.isArray(msgs.data) ? msgs.data.map((m: { role: string; content: string }) => ({ role: m.role, content: m.content })) : []);
    }
  };

  const deleteConv = async (id: string) => {
    if (!confirm("Delete this conversation?")) return;
    await chatApi.deleteConversation(id);
    if (convId === id) { setConvId(null); setMessages([]); }
    loadConvs();
  };

  const deleteAll = async () => {
    if (!confirm("Delete ALL conversations?")) return;
    setStreaming(true);
    let deleted = 0;
    for (const c of convs) {
      try { const res = await chatApi.deleteConversation(c.id); if (res.status === 204 || res.status === 200) deleted++; } catch { /* */ }
    }
    setConvs([]); setConvId(null); setMessages([]);
    setStreaming(false);
    if (deleted > 0) loadConvs();
  };

  const newChat = () => { setConvId(null); setMessages([]); setCurrentEvents([]); };

  const getToken = () => {
    if (accessToken) return accessToken;
    try { const raw = localStorage.getItem("medagent-auth"); if (raw) return JSON.parse(raw).state?.accessToken || null; } catch { /* */ }
    return null;
  };

  const refreshToken = () => {
    try { const raw = localStorage.getItem("medagent-auth"); if (raw) return JSON.parse(raw).state?.accessToken || null; } catch { /* */ }
    return null;
  };


  const handleSend = async (message: string, attachment?: ComposerAttachment) => {
    let token = getToken();
    if (!token) return;

    setStreaming(true); setCurrentEvents([]);

    let id = convId;
    if (!id) {
      const res = await chatApi.createConversation("ar");
      if (res.error || !res.data) { setStreaming(false); return; }
      id = res.data.id; setConvId(id); loadConvs();
    }
    token = refreshToken() || token;

    const imageData = attachment?.dataUri;
    const imageKind = attachment?.kind;

    if (!isCompareMode) {
      // ── Single model (streaming live display) ──
      const [model] = selectedModels;
      const label = getModelLabel(model);

      // Add user message + placeholder assistant message
      const placeholder: ChatMessage = { role: "assistant", content: "", thinkingText: "", events: [], modelLabel: label };
      setMessages((prev) => [...prev, { role: "user", content: message, imagePreview: imageData }, placeholder]);
      const msgIdx = messages.length + 1; // index of placeholder after set

      const start = performance.now();

      const streamText = (fullText: string, msgIdx: number, field: "content" | "thinkingText", events: ChatEvent[]) => {
        let pos = 0;
        const total = fullText.length;
        return new Promise<void>((resolve) => {
          const tick = () => {
            if (pos >= total) { resolve(); return; }
            const chunk = fullText.slice(0, pos + 1);
            pos = chunk.length;
            setMessages((prev) => prev.map((m, i) =>
              i === msgIdx ? { ...m, [field]: chunk, events } : m
            ));
            setTimeout(() => requestAnimationFrame(tick), 12);
          };
          requestAnimationFrame(tick);
        });
      };

      const events: ChatEvent[] = [];
      let fullTxt = "";
      let thinkingTxt = "";

      try {
        for await (const event of chatApi.streamChat(id, message, token, model, imageData, imageKind)) {
          events.push(event);
          if (event.type === "token") fullTxt += event.content;
          if (event.type === "thinking") thinkingTxt += event.content;
          if (event.type === "red_flag") fullTxt = "🚨 تم اكتشاف علامات طارئة — يرجى التوجه للطوارئ فوراً";
          if (event.type === "error") fullTxt = event.content || "⚠️ خطأ من النموذج";
          if (event.type === "done") break;
        }
      } catch (e) { console.error("Chat error:", e); fullTxt = "عذراً، حدث خطأ."; }

      // Animate thinking text first (if any), then the response
      if (thinkingTxt) {
        await streamText(thinkingTxt, msgIdx, "thinkingText", events);
      }

      const clean = cleanResponse(fullTxt);
      const fallback = events.some(e => e.type === "red_flag")
        ? "🚨 تم اكتشاف علامات طارئة — يرجى التوجه للطوارئ فوراً"
        : events.some(e => e.type === "tool_result")
          ? "⚠️ اكتمل التحليل ولكن لم يتم إنشاء رد. حاول إعادة الصياغة."
          : "⚠️ لم يتم إنشاء رد. حاول مرة أخرى.";
      await streamText(clean || fallback, msgIdx, "content", events);

      const triageEvt = events.find((e) => e.type === "triage");
      setMessages((prev) => prev.map((m, i) =>
        i === msgIdx ? {
          ...m,
          content: clean || "⚠️ No response",
          thinkingText: thinkingTxt || undefined,
          events,
          latencyMs: performance.now() - start,
          tokenCount: events.filter((e) => e.type === "token").length,
          triageLevel: triageEvt?.data?.level as string || null,
          triageScore: triageEvt?.data?.score as number || null,
        } : m
      ));
      if (fullTxt) loadConvs();
    } else {
      // ── Compare mode: stack model responses vertically ──
      const userMsg: ChatMessage = { role: "user", content: message, imagePreview: imageData };
      const startIdx = messages.length; // user message index after set
      const modelMsgs: ChatMessage[] = selectedModels.map((model) => ({
        role: "assistant",
        content: "",
        thinkingText: "",
        modelLabel: getModelLabel(model),
        events: [],
      }));
      setMessages((prev) => [...prev, userMsg, ...modelMsgs]);

      const streams = selectedModels.map(async (model, idx) => {
        const msgIdx = startIdx + 1 + idx; // position in messages array
        const start = performance.now();
        const events: ChatEvent[] = [];
        let fullTxt = "";
        let thinkingTxt = "";
        let triageLevel: string | null = null;
        let triageScore: number | null = null;

        try {
          for await (const event of chatApi.streamChat(id, message, token, model, imageData, imageKind)) {
            events.push(event);
            if (event.type === "token") fullTxt += event.content;
            if (event.type === "thinking") thinkingTxt += event.content;
            if (event.type === "red_flag") fullTxt = "🚨 تم اكتشاف علامات طارئة — يرجى التوجه للطوارئ فوراً";
            if (event.type === "error") fullTxt = event.content || "⚠️ خطأ من النموذج";
            if (event.type === "triage") {
              triageLevel = (event.data?.level as string) || null;
              triageScore = (event.data?.score as number) || null;
            }
            if (event.type === "done") break;
          }
        } catch (e: unknown) {
          fullTxt = e instanceof Error ? e.message : "Request failed";
        }

        // Animate thinking text first
        if (thinkingTxt) {
          const total = thinkingTxt.length;
          let pos = 0;
          await new Promise<void>((resolve) => {
            const tick = () => {
              if (pos >= total) { resolve(); return; }
              const chunk = thinkingTxt.slice(0, pos + 1);
              pos = chunk.length;
              setMessages((prev) => prev.map((m, i) =>
                i === msgIdx ? { ...m, thinkingText: chunk, events } : m
              ));
              setTimeout(() => requestAnimationFrame(tick), 8);
            };
            requestAnimationFrame(tick);
          });
        }

        // Smooth character-by-character reveal via rAF for the response
        const clean = cleanResponse(fullTxt);
        const total = clean.length;
        let pos = 0;
        await new Promise<void>((resolve) => {
          const tick = () => {
            if (pos >= total) { resolve(); return; }
            const chunk = clean.slice(0, pos + 1);
            pos = chunk.length;
            setMessages((prev) => prev.map((m, i) =>
              i === msgIdx ? { ...m, content: chunk, events, triageLevel, triageScore } : m
            ));
            setTimeout(() => requestAnimationFrame(tick), 8);
          };
          requestAnimationFrame(tick);
        });

        setMessages((prev) => prev.map((m, i) =>
          i === msgIdx ? {
            ...m,
            content: clean || (events.some(e => e.type === "red_flag") ? "🚨 تم اكتشاف علامات طارئة" : events.some(e => e.type === "error") ? (events.find(e => e.type === "error")?.content || "⚠️ خطأ") : events.some(e => e.type === "tool_result") ? "⚠️ اكتمل التحليل بدون رد" : "⚠️ No response"),
            thinkingText: thinkingTxt || undefined,
            events,
            triageLevel,
            triageScore,
            latencyMs: performance.now() - start,
            tokenCount: events.filter((e) => e.type === "token").length,
          } : m
        ));
      });

      await Promise.all(streams);
      loadConvs();
    }

    setStreaming(false); setCurrentEvents([]);
  };

  const filtered = searchTerm ? convs.filter((c) => (c.title || "").toLowerCase().includes(searchTerm.toLowerCase())) : convs;

  const historyList = (
    <div className="flex flex-col h-full">
      <div className="p-2 space-y-2 flex-shrink-0">
        <button onClick={newChat} className="btn-primary flex w-full items-center justify-center gap-1.5 rounded-lg py-1.5 text-[11px] font-semibold">
          <Plus className="h-3 w-3" /> New Chat
        </button>
        <div className="flex items-center gap-1.5 rounded-md bg-muted/50 px-2 py-1.5">
          <Search className="h-3 w-3 text-muted-foreground flex-shrink-0" />
          <input value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} placeholder="Search..." className="w-full bg-transparent text-[11px] text-foreground placeholder:text-muted-foreground outline-none" />
        </div>
      </div>
      <div className="flex-1 overflow-y-auto px-1.5 pb-2 space-y-0.5 min-h-0">
        {convLoading ? (
          <p className="text-[11px] text-muted-foreground text-center py-4">Loading...</p>
        ) : filtered.length === 0 ? (
          <p className="text-[11px] text-muted-foreground text-center py-4">{searchTerm ? "No results" : "No conversations"}</p>
        ) : (
          filtered.map((c) => (
            <div key={c.id} onClick={() => loadConversation(c.id)}
              className={`group flex items-start gap-1.5 w-full text-left px-2 py-1.5 rounded-md cursor-pointer transition-colors ${c.id === convId ? "bg-sidebar-accent text-sidebar-accent-foreground" : "hover:bg-muted/50 text-sidebar-foreground"}`}>
              <MessageSquare className="h-3 w-3 mt-0.5 flex-shrink-0 text-muted-foreground" />
              <div className="flex-1 min-w-0">
                <p className="text-[11px] leading-tight truncate">{c.title || "New conversation"}</p>
                <div className="flex items-center gap-1 mt-0.5">
                  {c.triage_level && <span className={`text-[8px] font-semibold px-1 py-0 rounded-full ${triageBadge[c.triage_level] || "bg-muted text-ink-4"}`}>{c.triage_level}</span>}
                  <span className="text-[9px] text-muted-foreground">{new Date(c.updated_at).toLocaleDateString()}</span>
                </div>
              </div>
              <button onClick={(e) => { e.stopPropagation(); deleteConv(c.id); }} className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-red-100 dark:hover:bg-red-950/30 text-muted-foreground hover:text-red-600 flex-shrink-0">
                <Trash2 className="h-2.5 w-2.5" />
              </button>
            </div>
          ))
        )}
      </div>
      {convs.length > 0 && (
        <div className="px-1.5 pb-2 flex-shrink-0">
          <button onClick={deleteAll} className="flex w-full items-center justify-center gap-1 rounded-md py-1.5 text-[10px] text-muted-foreground hover:bg-red-50 dark:hover:bg-red-950/30 hover:text-red-600 transition-colors">
            <Trash2 className="h-2.5 w-2.5" /> Delete all
          </button>
        </div>
      )}
    </div>
  );

  return (
    <div className="flex h-[calc(100vh-3.5rem)]">
      {portalReady && createPortal(historyList, document.getElementById("sidebar-history-slot") || document.body)}

      <div className="flex-1 flex flex-col min-w-0">
        {triage.level && <TriagePanel state={triage} collapsed={!triageExpanded} onToggle={() => setTriageExpanded(!triageExpanded)} />}
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4">
          <div className="max-w-5xl mx-auto">
            {messages.length === 0 && !streaming && (
              <div className="flex flex-col items-center justify-center h-full min-h-[40vh] text-center">
                <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 text-primary mb-5 shadow-sm">
                  <Sparkles className="h-7 w-7" />
                </div>
                <h3 className="text-xl font-semibold text-foreground">MedAgent Triage</h3>
                <p className="mt-2 text-sm text-muted-foreground max-w-xs">Describe your symptoms in Arabic or English.</p>
              </div>
            )}

            {messages.map((msg, i) => {
              if (msg.role === "user") {
                return <MessageBubble key={i} role="user" content={msg.content} senderName={user?.full_name || undefined} imagePreview={msg.imagePreview} />;
              }
              return (
                <div key={i}>
                  {/* Model name label */}
                  {msg.modelLabel && (
                    <div className="ml-12 mb-2 text-xs font-semibold text-muted-foreground/70">
                      {msg.modelLabel}
                    </div>
                  )}





                  {/* Response card */}
                  <MessageBubble
                    role="assistant"
                    content={msg.content}
                    events={msg.events}
                    senderName={undefined}
                  />

                  {/* ToT branches */}
                  {Boolean(msg.events?.find((e) => e.type === "tot_branches")?.data?.branches) && (
                    <div className="mt-3 ml-11 max-w-[85%]">
                      <DifferentialPanel branches={(msg.events!.find((e) => e.type === "tot_branches")!.data.branches) as Array<{ name: string; confidence: number; evidence: string }>} />
                    </div>
                  )}

                  {/* Triage card */}
                  {msg.triageLevel && (
                    <div className={`ml-11 mt-2 mb-2 max-w-[85%] rounded-xl border px-3 py-2 ${
                      msg.triageLevel === "emergency" ? "border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950" :
                      msg.triageLevel === "urgent" ? "border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950" :
                      "border-emerald-200 bg-emerald-50 dark:border-emerald-900 dark:bg-emerald-950"
                    }`}>
                      <div className="flex items-center gap-2 text-xs">
                        <Activity className={`h-3.5 w-3.5 ${
                          msg.triageLevel === "emergency" ? "text-red-600" :
                          msg.triageLevel === "urgent" ? "text-amber-600" :
                          "text-emerald-600"
                        }`} />
                        <span className="font-bold uppercase">{msg.triageLevel}</span>
                        {msg.triageScore != null && <span className="text-muted-foreground">· Score {msg.triageScore}</span>}
                      </div>
                    </div>
                  )}

                  {/* Metrics row */}
                  {msg.modelLabel && (
                    <div className="ml-12 mb-4 flex items-center gap-4 text-[11px] text-muted-foreground">
                      {msg.latencyMs != null && (
                        <span className="inline-flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {(msg.latencyMs / 1000).toFixed(1)}s
                        </span>
                      )}
                      {msg.tokenCount != null && (
                        <span className="inline-flex items-center gap-1">
                          <Hash className="h-3 w-3" />
                          {msg.tokenCount} tok
                        </span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}

            {streaming && !isCompareMode && !currentEvents.some((e) => e.type === "token") && <TypingIndicator />}
          </div>
        </div>

        {/* Send to Doctor button */}
        {messages.length > 0 && convId && !streaming && (
          <div className="flex justify-center px-4 -mt-1 pb-1">
            <button
              onClick={() => setSendToDoctorOpen(true)}
              className="flex items-center gap-2 text-xs font-medium text-muted-foreground hover:text-primary transition-colors px-4 py-2 rounded-xl border border-border/60 hover:border-primary/30 hover:bg-primary/5"
            >
              <Send className="h-3.5 w-3.5" />
              Send to Doctor
            </button>
          </div>
        )}

        <ChatComposer onSend={handleSend} disabled={streaming} selectedModels={selectedModels} onModelsChange={setSelectedModels} />
      </div>

      {/* Doctor search dialog */}
      {convId && (
        <DoctorSearchDialog
          conversationId={convId}
          open={sendToDoctorOpen}
          onClose={() => setSendToDoctorOpen(false)}
        />
      )}
    </div>
  );
}
