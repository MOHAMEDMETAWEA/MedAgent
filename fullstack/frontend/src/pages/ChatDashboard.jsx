import React, { useState, useEffect, useRef } from 'react';
import { GlassCard } from '../components/ui/GlassCard';
import { 
  Share, MoreVertical, BrainCircuit, Activity, Pill, Microscope, History, 
  FolderOpen, Image as ImageIcon, Mic, Languages, PlusCircle, Send, 
  Download, FileText, Loader2, ClipboardList, ShieldCheck, Zap, CloudOff,
  ChevronRight, ChevronDown, FolderPlus, LayoutGrid, Clock, ExternalLink, Stethoscope, X,
  Link as LinkIcon, Mail, MessageCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { AIService } from '../services/api/aiService';
import femaleAvatar from '../assets/female-avatar.svg';
import maleAvatar from '../assets/male-avatar.svg';

export default function ChatDashboard() {
  const { t, i18n } = useTranslation();
  const isRtl = i18n.dir() === 'rtl';
  const { userData } = useAuth();
  
  // States
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isActionsOpen, setIsActionsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  
  // Sidebar States
  const [diagHistory, setDiagHistory] = useState([]);
  const [activeCaseId, setActiveCaseId] = useState('d2');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isShareOpen, setIsShareOpen] = useState(false);

  const chatEndRef = useRef(null);
  const displayAvatar = userData.profileImage || maleAvatar;

  // AI Connection State (Mocked)
  const [isOnline, setIsOnline] = useState(true);

  // Dynamic Telemetry Logic
  const msgCount = messages.filter(m => m.sender === 'user').length;
  const dynamicConfidence = Math.min(99, 40 + msgCount * 12);
  
  const triageSteps = [
    { title: t('sidebarMock.symptomCollection'), status: msgCount >= 1 ? 'completed' : 'active' },
    { title: t('sidebarMock.clinicalDiscovery'), status: msgCount >= 3 ? 'completed' : msgCount >= 1 ? 'active' : 'pending' },
    { title: t('sidebarMock.diagnosisGeneration'), status: msgCount >= 5 ? 'completed' : msgCount >= 3 ? 'active' : 'pending' },
    { title: t('sidebarMock.finalActionPlan'), status: msgCount >= 7 ? 'completed' : msgCount >= 5 ? 'active' : 'pending' }
  ];

  const currentInsights = [
    { text: t('sidebarMock.abnormalEcg'), minMsgs: 1 },
    { text: t('sidebarMock.chestPain'), minMsgs: 3 },
    { text: t('sidebarMock.highPulse'), minMsgs: 5 }
  ].filter(i => msgCount >= i.minMsgs);

  // Global Documents Mock
  const [allDocuments] = useState([
    { id: 1, name: 'Chest_XRay_Ant.dcm', chatTitle: t('sidebarMock.cardiacCheck') },
    { id: 2, name: 'Blood_Panel_Q3.pdf', chatTitle: t('sidebarMock.bloodPanel') },
    { id: 3, name: 'MRI_Scan_Head.png', chatTitle: t('sidebarMock.migraineAssesment') }
  ]);

  // Initialize
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [history, diagnostics] = await Promise.all([
          AIService.getChatHistory(userData.id),
          AIService.getDiagnosisHistory()
        ]);
        setMessages(history);
        setDiagHistory(diagnostics);
      } catch (err) {
        console.error("Failed to load dashboard data", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
    
    // Simulate periodic status check
    const interval = setInterval(() => {
      setIsOnline(navigator.onLine);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!inputValue.trim() || isTyping) return;

    const userMessage = {
      id: Date.now(),
      sender: 'user',
      text: inputValue,
      time: t('global.justNow')
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      const response = await AIService.consult(userData.id, userMessage.text);
      setMessages(prev => [...prev, response]);
    } catch (err) {
      console.error(t('global.aiError'), err);
    } finally {
      setIsTyping(false);
    }
  };

  const handleRecommendStep = () => {
    if (isTyping) return;
    setIsTyping(true);
    setTimeout(() => {
      setMessages(prev => [...prev, {
        id: Date.now(),
        sender: 'ai',
        text: t('sidebarMock.recommendation'),
        time: t('global.justNow')
      }]);
      setIsTyping(false);
    }, 1500);
  };

  const handleMoveToFolder = (diagId) => {
    prompt(t('sidebarMock.enterFolder', { diagId }), t('sidebarMock.cardiology'));
  };

  const handleShare = () => {
    setIsShareOpen(true);
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    alert(t('global.linkCopied'));
    setIsShareOpen(false);
  };

  return (
    <div className="flex h-[calc(100vh-80px)] w-[calc(100%+2rem)] -mx-4 md:w-[calc(100%+4rem)] md:-mx-8 -mt-5 -mb-8 relative overflow-hidden bg-transparent">
      
      {/* LEFT SIDEBAR - Clinical Mission Control */}
      <aside className={`fixed inset-y-0 left-0 z-40 w-full md:w-80 bg-glass backdrop-blur-3xl border-r border-ghost flex flex-col transition-transform duration-500 xl:relative xl:translate-x-0 ${isSidebarOpen ? 'translate-x-0 shadow-2xl xl:shadow-none' : '-translate-x-full'}`}>

        
        {/* Mobile Close */}
        <button onClick={() => setIsSidebarOpen(false)} className="absolute top-4 right-4 p-2 bg-white/50 rounded-full xl:hidden transition-colors hover:bg-white text-slate-500">
          <X className="w-5 h-5" />
        </button>

        <div className="flex-1 overflow-y-auto scrollbar-hide p-6 space-y-8 mt-8 xl:mt-0 pb-12">
          
          {/* Section 1: ChatGPT-Style Diagnosis History */}
          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xs font-black uppercase tracking-widest text-[var(--color-on-surface-variant)] opacity-80 flex items-center gap-2">
                <History className="w-3 h-3" /> {t('sidebar.diagnosis')}
              </h2>
            </div>
            
            <div className="space-y-4">
              {[t('global.today'), t('global.previous7Days')].map((group, gIdx) => {
                const groupItems = diagHistory.filter((_, i) => gIdx === 0 ? i < 2 : i >= 2);
                if (groupItems.length === 0) return null;
                
                return (
                  <div key={group}>
                    <h3 className="text-[10px] font-bold text-slate-400 mb-2 px-2 uppercase">{group}</h3>
                    <div className="space-y-1">
                      {groupItems.map(diag => (
                        <div key={diag.id} className={`group relative w-full text-start px-3 py-2.5 rounded-xl transition-all flex items-center justify-between cursor-pointer border ${activeCaseId === diag.id ? 'bg-white border-blue-200 shadow-[var(--shadow-liquid)]' : 'border-transparent hover:bg-white/40'}`} onClick={() => handleResumeDiagnosis(diag.id)}>
                          <span className={`text-[11px] font-black leading-tight truncate pr-6 transition-colors ${activeCaseId === diag.id ? 'text-blue-600' : 'text-slate-700'}`}>
                            {diag.title}
                          </span>
                          <div className="absolute right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button 
                              onClick={(e) => { e.stopPropagation(); handleMoveToFolder(diag.id); }}
                              className="p-1.5 hover:bg-blue-100 rounded-md text-blue-600 transition-colors bg-white/80 shadow-sm border border-blue-100" 
                              title={t('sidebar.createFolder')}
                            >
                              <FolderPlus className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          </section>

          {/* Section 2: Global Document Inbox */}
          {allDocuments.length > 0 && (
            <section>
              <h2 className="text-xs font-black uppercase tracking-widest text-[var(--color-on-surface-variant)] opacity-80 mb-4 flex items-center gap-2">
                <FolderOpen className="w-3 h-3" /> {t('sidebar.uploads')}
              </h2>
              <div className="grid grid-cols-2 gap-3">
                {allDocuments.map((doc) => (
                  <div key={doc.id} onClick={() => alert(`${t('global.navigatingToChat')}${doc.chatTitle}`)} className="relative aspect-square rounded-[2rem] bg-white border border-white shadow-sm overflow-hidden flex flex-col group cursor-pointer hover:shadow-xl hover:border-indigo-100 transition-all">
                    <div className="flex-1 flex items-center justify-center bg-indigo-50/50 group-hover:bg-indigo-50 transition-colors">
                      <FileText className="w-8 h-8 text-indigo-400 group-hover:scale-110 transition-transform duration-300" />
                    </div>
                    {/* Chat Name Overlay at bottom center */}
                    <div className="absolute bottom-0 inset-x-0 pb-3 pt-6 px-2 bg-gradient-to-t from-slate-900/90 via-slate-900/40 to-transparent">
                      <p className="text-[8px] font-black leading-tight text-white/90 text-center truncate drop-shadow-md">{doc.chatTitle}</p>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Section 3: Dynamic Clinical Insights */}
          <section>
            <h2 className="text-xs font-black uppercase tracking-widest text-[var(--color-on-surface-variant)] opacity-80 mb-4 flex items-center gap-2">
              <BrainCircuit className="w-3 h-3" /> {t('sidebar.insights')}
            </h2>
            <div className="space-y-2.5">
              <AnimatePresence>
                {currentInsights.length > 0 ? currentInsights.map((note, i) => (
                  <motion.div 
                    initial={{ opacity: 0, x: -10, y: 10 }}
                    animate={{ opacity: 1, x: 0, y: 0 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    key={note.text} 
                    className="flex gap-3 p-4 rounded-3xl bg-indigo-50/50 border border-indigo-100/50 hover:bg-indigo-50 transition-colors shadow-sm"
                  >
                    <Activity className="w-4 h-4 text-indigo-600 flex-shrink-0" />
                    <p className="text-[10px] font-extrabold text-indigo-900 leading-tight">{note.text}</p>
                  </motion.div>
                )) : (
                  <motion.div 
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                    className="text-center p-4 border border-dashed border-slate-200 rounded-2xl"
                  >
                    <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">{t('global.awaitingData')}</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </section>

          {/* Section 4: Dynamic AI Confidence Gauge */}
          <section>
            <h2 className="text-xs font-black uppercase tracking-widest text-[var(--color-on-surface-variant)] opacity-80 mb-4 flex items-center gap-2">
              <LayoutGrid className="w-3 h-3" /> {t('sidebar.confidence')}
            </h2>
            <div className="card-premium flex flex-col items-center">
              <div className="relative w-36 h-24 mb-2 flex items-center justify-center">
                <svg className="absolute inset-0 w-full h-full p-2 overflow-visible" viewBox="0 0 100 60">
                  <path d="M10,50 A40,40 0 0,1 90,50" fill="none" stroke="#f1f5f9" strokeWidth="12" strokeLinecap="round" />
                  <motion.path 
                    initial={{ pathLength: 0 }}
                    animate={{ pathLength: dynamicConfidence / 100 }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    d="M10,50 A40,40 0 0,1 90,50" 
                    fill="none" stroke="url(#confidenceGradient)" strokeWidth="12" strokeLinecap="round" 
                    className="drop-shadow-sm"
                  />
                  <defs>
                    <linearGradient id="confidenceGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#3b82f6" />
                      <stop offset="100%" stopColor="#22c55e" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="mt-8 flex flex-col items-center">
                  <motion.span 
                    key={dynamicConfidence}
                    initial={{ scale: 1.2, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="text-2xl font-black text-slate-900 leading-none"
                  >
                    {dynamicConfidence}%
                  </motion.span>
                  <span className="text-[8px] font-black uppercase text-blue-600 tracking-tighter mt-1">
                    {dynamicConfidence > 80 ? t('global.highIntegrity') : dynamicConfidence > 50 ? t('global.moderate') : t('global.collectingInfo')}
                  </span>
                </div>
              </div>
            </div>
          </section>

        </div>

        {/* Bottom Actions Sticky */}
        <div className="p-6 bg-white/40 backdrop-blur-3xl border-t border-ghost space-y-4">
          
          {/* Triage Progress Path Moved Here */}
          <div className="card-premium mb-4">
            <h4 className="text-[9px] font-black text-slate-400 mb-3 uppercase tracking-widest flex items-center gap-2">
              <ClipboardList className="w-3.5 h-3.5" /> {t('sidebar.timeline')}
            </h4>
            <div className="space-y-3.5 relative pl-3.5">
              <div className="absolute left-1.5 top-0 bottom-0 w-0.5 bg-slate-100" />
              {triageSteps.map((step, i) => (
                <div key={i} className="relative flex items-center gap-4 group">
                  <div className={`absolute -left-4 w-4 h-4 rounded-full border-2 border-white shadow-sm z-10 transition-colors duration-500 delay-100 ${step.status === 'completed' ? 'bg-emerald-500' : step.status === 'active' ? 'bg-blue-600 animate-pulse' : 'bg-slate-200 group-hover:bg-slate-300'}`} />
                  <p className={`text-[10px] font-black tracking-tight transition-colors duration-300 ${step.status === 'active' ? 'text-blue-600' : step.status === 'completed' ? 'text-slate-800' : 'text-slate-400 group-hover:text-slate-500'}`}>{step.title}</p>
                </div>
              ))}
            </div>
          </div>

          <button onClick={handleRecommendStep} className="w-full py-4 bg-blue-600/80 backdrop-blur-xl text-white hover:bg-blue-600 rounded-[1.5rem] text-[11px] font-black flex items-center justify-center gap-2.5 shadow-none transition-all group overflow-hidden relative border border-blue-500/30">
            <Stethoscope className="w-4 h-4 text-white group-hover:scale-110 transition-transform" /> {t('sidebar.nextStep')}
          </button>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 overflow-hidden flex flex-col relative z-20 bg-white/10 min-w-0">
        <header className="px-4 md:px-8 py-4 md:py-6 flex justify-between items-center bg-glass border-b border-ghost shadow-sm relative z-10 backdrop-blur-3xl">
          <div className="flex items-center gap-3 md:gap-4">
            <button 
              className="p-2 md:p-2.5 rounded-xl border border-ghost hover:bg-white/50 transition-colors bg-glass shadow-sm text-slate-500 xl:hidden mr-1"
              onClick={() => setIsSidebarOpen(true)}
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <div className="relative hidden sm:block">
              <div className="w-10 h-10 md:w-12 md:h-12 rounded-2xl bg-white border border-slate-100 flex items-center justify-center text-[var(--color-primary)] shadow-[0_8px_16px_rgba(45,91,255,0.06)]">
                <BrainCircuit className={`w-5 h-5 md:w-6 md:h-6 text-blue-600 ${isTyping ? 'animate-pulse' : ''}`} />
              </div>
              <div className="absolute -bottom-1 -right-1 w-3 h-3 md:w-4 md:h-4 bg-emerald-500 border-2 border-white rounded-full shadow-sm animate-pulse"></div>
            </div>
            <div>
              <h1 className="text-lg md:text-xl font-extrabold tracking-tight text-[#191c1e] leading-none mb-1 flex items-center gap-2">
                {t('chat.medagent')}
              </h1>
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                <p className="text-[10px] md:text-xs text-slate-500 font-bold tracking-wide uppercase opacity-70">
                  {isTyping ? t('global.processing') : t('chat.specialized')}
                </p>
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={handleShare} className="p-2 md:p-2.5 rounded-xl border border-ghost hover:bg-white/50 transition-colors bg-glass shadow-sm text-slate-500">
              <Share className="w-4 h-4" />
            </button>
          </div>
        </header>

        <section className="flex-1 flex flex-col overflow-y-auto px-4 md:px-8 py-6 pb-48 scrollbar-hide relative z-0">
          {isLoading ? (
            <div className="flex-1 flex items-center justify-center">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500 opacity-20" />
            </div>
          ) : (
            <div className="space-y-8">
              {messages.map((msg) => (
                <motion.div 
                  layout
                  initial={{ opacity: 0, y: 10, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  key={msg.id} 
                  className={`flex gap-3 md:gap-4 max-w-3xl w-full ${msg.sender === 'user' ? 'ms-auto flex-row-reverse' : ''}`}
                >
                  <div className={`flex-shrink-0 w-8 h-8 md:w-10 md:h-10 rounded-xl overflow-hidden shadow-sm border border-white/60 ${msg.sender === 'ai' ? 'bg-indigo-100 flex items-center justify-center' : 'bg-slate-200'}`}>
                    {msg.sender === 'ai' 
                      ? <BrainCircuit className="w-4 h-4 md:w-5 md:h-5 text-indigo-600" /> 
                      : <img src={displayAvatar} alt="User" className="w-full h-full object-cover" />
                    }
                  </div>
                  <div className={`space-y-2 md:space-y-3 max-w-[85%] ${msg.sender === 'user' ? 'text-end' : ''}`}>
                    <div className={`${
                        msg.sender === 'ai' 
                        ? 'bg-glass-heavy p-4 md:p-6 rounded-2xl rounded-ss-none shadow-liquid-glass border border-white/80'
                        : 'bg-primary-gradient text-white p-4 md:p-6 rounded-2xl rounded-se-none shadow-[0_10px_25px_rgba(0,91,192,0.15)] border border-white/20'
                      }`}
                    >
                      <p className={`text-sm leading-relaxed font-bold ${msg.sender === 'ai' ? 'text-[var(--color-on-surface)]' : 'text-white'}`}>
                        {msg.text}
                      </p>
                      
                      {msg.file && (
                        <div className="mt-4 flex items-center gap-3 p-3 bg-white/70 backdrop-blur border border-white rounded-xl hover:bg-white transition-colors cursor-pointer group shadow-[var(--shadow-liquid)]">
                          <div className="w-10 h-10 rounded-lg bg-red-100/80 flex items-center justify-center text-red-600">
                            <FileText className="w-5 h-5" />
                          </div>
                          <div className="flex-1 min-w-0 text-start">
                            <p className="text-xs font-black text-slate-900 truncate">{msg.file.name}</p>
                            <p className="text-[10px] font-bold text-slate-500">{msg.file.desc}</p>
                          </div>
                          <Download className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition-colors" />
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
              {isTyping && (
                <div className="flex gap-4">
                  <div className="w-10 h-10 rounded-xl bg-indigo-100 flex items-center justify-center border border-white/60">
                    <BrainCircuit className="w-5 h-5 text-indigo-600 animate-pulse" />
                  </div>
                  <div className="bg-glass-heavy p-6 rounded-2xl rounded-tl-none border border-white/80">
                    <div className="flex gap-1.5">
                      <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce"></div>
                      <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:0.2s]"></div>
                      <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:0.4s]"></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
          )}
        </section>

        {/* Center Input Area */}
        <div className="absolute bottom-0 left-0 right-0 p-2 md:p-4 z-30 pointer-events-none">
          <div className="max-w-4xl mx-auto pointer-events-auto">


            <AnimatePresence>
              {isActionsOpen && (
                <motion.div 
                  initial={{ opacity: 0, y: 10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 10, scale: 0.95 }}
                  className="flex flex-wrap lg:flex-nowrap gap-2 w-max max-w-[95%] mx-auto mb-6 justify-center bg-[#333d4d]/90 backdrop-blur-3xl p-3 md:p-4 rounded-full shadow-2xl border border-white/10"
                >
                  <button className="group flex items-center gap-2.5 px-4 py-2.5 rounded-2xl bg-white border border-white text-slate-800 hover:bg-blue-600 hover:text-white transition-all shadow-sm">
                    <FolderOpen className="w-5 h-5 text-blue-600 group-hover:text-white transition-colors" />
                    <span className="text-[11px] font-bold">{t('chat.files')}</span>
                  </button>
                  <button className="group flex items-center gap-2.5 px-4 py-2.5 rounded-2xl bg-white border border-white text-slate-800 hover:bg-blue-600 hover:text-white transition-all shadow-sm">
                    <ImageIcon className="w-5 h-5 text-blue-600 group-hover:text-white transition-colors" />
                    <span className="text-[11px] font-bold">{t('chat.images')}</span>
                  </button>
                  <button className="group flex items-center gap-2.5 px-4 py-2.5 rounded-2xl bg-white border border-white text-slate-800 hover:bg-blue-600 hover:text-white transition-all shadow-sm">
                    <Mic className="w-5 h-5 text-blue-600 group-hover:text-white transition-colors" />
                    <span className="text-[11px] font-bold">{t('chat.audio')}</span>
                  </button>
                  <button className="group flex items-center gap-2.5 px-4 py-2.5 rounded-2xl bg-white border border-white text-slate-800 hover:bg-blue-600 hover:text-white transition-all shadow-sm">
                    <Languages className="w-5 h-5 text-blue-600 group-hover:text-white transition-colors" />
                    <span className="text-[11px] font-bold">{t('chat.translate')}</span>
                  </button>
                  <button className="group flex items-center gap-2.5 px-4 py-2.5 rounded-2xl bg-[#fceeda]/90 border border-orange-200 text-[#c05f01] hover:bg-orange-600 hover:text-white transition-all shadow-sm">
                    <Microscope className="w-5 h-5 group-hover:text-white transition-colors" />
                    <span className="text-[11px] font-bold">{t('chat.lab')}</span>
                  </button>
                </motion.div>
              )}
            </AnimatePresence>

            <div className="bg-white/40 backdrop-blur-3xl border border-white p-2 md:p-3 rounded-[2rem] shadow-[var(--shadow-liquid)] relative z-10">
              <form onSubmit={handleSend} className="flex items-center gap-2 md:gap-4 h-12 md:h-14">
                <button 
                  type="button" 
                  onClick={() => setIsActionsOpen(!isActionsOpen)}
                  className={`flex-shrink-0 w-10 h-10 md:w-12 md:h-12 rounded-xl flex items-center justify-center transition-all border border-transparent ${isActionsOpen ? 'bg-red-500 text-white rotate-45 shadow-[var(--shadow-liquid)]' : 'bg-white/60 text-[#191c1e] hover:bg-white hover:border-ghost shadow-sm'}`}
                >
                  <PlusCircle className="w-5 h-5 md:w-6 md:h-6" />
                </button>
                <input 
                  type="text" 
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder={t('chat.placeholder')}
                  className="flex-1 bg-transparent border-none outline-none focus:ring-0 text-black dark:text-black caret-black text-base md:text-lg font-bold placeholder:text-slate-600 placeholder:opacity-70 tracking-wide"
                  disabled={isTyping}
                />
                <button 
                  type="submit"
                  disabled={!inputValue.trim() || isTyping}
                  className="flex-shrink-0 w-10 h-10 md:w-12 md:h-12 rounded-xl bg-primary-gradient text-white flex items-center justify-center shadow-liquid-glass hover:shadow-liquid-hover hover:scale-[1.02] transition-all disabled:opacity-50 disabled:hover:scale-100 disabled:cursor-not-allowed active:scale-95"
                >
                  <Send className="w-5 h-5 md:w-6 md:h-6 rtl:-scale-x-100" />
                </button>
              </form>
            </div>
            {/* Compact Footer for Home Page */}
            <div className="mt-1 flex flex-col items-center gap-0">
              
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1.5 opacity-90 translate-y-[1px]">
                  <Activity className="w-2.5 h-2.5 text-[var(--color-primary)]" />
                  <span className="text-[9px] font-extrabold text-[var(--color-primary)] tracking-tighter">MedAgent</span>
                </div>
                <div className="w-px h-2.5 bg-slate-300/60" />
                <p className="text-[8px] font-black text-slate-400 uppercase tracking-[0.15em] leading-none">
                  © 2026 MedAgent | {t('global.yourAiDoctor')}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Floating AI Orb Indicator */}
        <div className="fixed bottom-44 end-8 z-[100]">
          <div className="relative flex items-center group">
            
            <AnimatePresence>
              {isTyping && isOnline && (
                <motion.div 
                  className="absolute end-full me-4 top-1/2 -translate-y-1/2 bg-blue-600/90 backdrop-blur-xl text-white text-[10px] uppercase font-black tracking-widest px-5 py-2 rounded-full whitespace-nowrap shadow-xl border border-blue-400/30"
                  initial={{ opacity: 0, x: isRtl ? -20 : 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: isRtl ? -10 : 10 }}
                >
                  <span className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping"></span>
                    {triageSteps.find(s => s.status === 'active')?.title || t('global.processing')}
                  </span>
                </motion.div>
              )}
            </AnimatePresence>

            <div className="relative">
              <AnimatePresence>
                {isTyping && isOnline && (
                  <motion.div 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ repeat: Infinity, duration: 4, ease: "linear" }}
                    className="absolute inset-0 rounded-full border border-dashed border-blue-500/30"
                  />
                )}
              </AnimatePresence>
              <motion.div 
                animate={!isOnline ? { scale: 0.95 } : isTyping ? { scale: [1, 1.2, 1], opacity: [0.3, 0.6, 0.3] } : { scale: [1, 1.1, 1], opacity: [0.1, 0.3, 0.1] }}
                transition={{ repeat: Infinity, duration: isTyping ? 1.5 : 3, ease: "easeInOut" }}
                className={`absolute inset-0 rounded-full ${!isOnline ? 'bg-slate-500/10 blur-xl' : isTyping ? 'bg-blue-600/20 blur-xl' : 'bg-blue-500/10 blur-xl'}`}
              />
              <motion.div 
                whileHover={isOnline ? { scale: 1.1 } : {}}
                className={`w-12 h-12 rounded-full flex items-center justify-center text-white border border-white/20 shadow-xl relative z-10 overflow-hidden transition-all duration-300 ${!isOnline ? 'bg-slate-300 grayscale opacity-80' : 'bg-primary-gradient'}`}
              >
                <AnimatePresence mode="wait">
                  {!isOnline ? <CloudOff className="w-5 h-5 text-white" /> : isTyping ? <Zap className="w-5 h-5 fill-white" /> : <ShieldCheck className="w-5 h-5" />}
                </AnimatePresence>
              </motion.div>
            </div>
          </div>
        </div>
      </main>

      {/* Glassmorphism Share Modal */}
      <AnimatePresence>
        {isShareOpen && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm"
            onClick={() => setIsShareOpen(false)}
          >
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-sm bg-glass-heavy backdrop-blur-3xl border border-white/60 p-6 rounded-[2rem] shadow-[var(--shadow-liquid)] relative overflow-hidden"
            >
              <div className="absolute top-0 inset-x-0 h-32 bg-gradient-to-b from-blue-500/10 to-transparent pointer-events-none" />
              
              <div className="flex justify-between items-center mb-6 relative">
                <h3 className="text-sm font-black text-slate-800 uppercase tracking-widest">{t('global.shareSession')}</h3>
                <button onClick={() => setIsShareOpen(false)} className="p-2 hover:bg-slate-100 rounded-full transition-colors text-slate-400">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-3 relative">
                <button onClick={handleCopyLink} className="w-full group flex items-center gap-4 p-4 rounded-2xl bg-white/40 hover:bg-white border border-white transition-all shadow-sm">
                  <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                    <LinkIcon className="w-5 h-5" />
                  </div>
                  <div className="flex-1 text-start">
                    <p className="text-xs font-black text-slate-800">{t('global.copyLink')}</p>
                    <p className="text-[10px] font-bold text-slate-400">{t('global.placeholder')}</p>
                  </div>
                </button>

                <button onClick={() => setIsShareOpen(false)} className="w-full group flex items-center gap-4 p-4 rounded-2xl bg-white/40 hover:bg-white border border-white transition-all shadow-sm">
                  <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                    <MessageCircle className="w-5 h-5" />
                  </div>
                  <div className="flex-1 text-start">
                    <p className="text-xs font-black text-slate-800">{t('global.whatsapp')}</p>
                    <p className="text-[10px] font-bold text-slate-400">{t('global.whatsappDesc')}</p>
                  </div>
                </button>

                <button onClick={() => setIsShareOpen(false)} className="w-full group flex items-center gap-4 p-4 rounded-2xl bg-white/40 hover:bg-white border border-white transition-all shadow-sm">
                  <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                    <Mail className="w-5 h-5" />
                  </div>
                  <div className="flex-1 text-start">
                    <p className="text-xs font-black text-slate-800">{t('global.emailDoctor')}</p>
                    <p className="text-[10px] font-bold text-slate-400">{t('global.emailDesc')}</p>
                  </div>
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
}
