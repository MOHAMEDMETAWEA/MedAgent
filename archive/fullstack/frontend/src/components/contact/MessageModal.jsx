import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Send, CheckCircle2, MessageSquare, ClipboardList, Pill, Activity, Stethoscope } from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { Button } from '../ui/Button';
import femaleAvatar from '../../assets/female-avatar.svg';
import maleAvatar from '../../assets/male-avatar.svg';

export function MessageModal({ isOpen, onClose, doctor, onSendSuccess }) {
  const { t, i18n } = useTranslation();
  const isRtl = i18n.dir() === 'rtl';
  const [message, setMessage] = useState('');
  const [selectedTopic, setSelectedTopic] = useState('General');
  const [isSending, setIsSending] = useState(false);
  const [sent, setSent] = useState(false);

  const topics = [
    { id: 'General', label: t('doctors.generalAdvice'), icon: MessageSquare },
    { id: 'Symptoms', label: t('doctors.symptomsCheck'), icon: Stethoscope },
    { id: 'Prescription', label: t('doctors.prescriptionRefill'), icon: Pill },
    { id: 'Labs', label: t('doctors.labAnalysis'), icon: ClipboardList },
  ];

  const handleSend = async () => {
    if (!message.trim()) return;
    setIsSending(true);
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1800));
    
    const newMessage = {
      id: Date.now(),
      doctorId: doctor.id,
      doctorName: doctor.name,
      topic: selectedTopic,
      content: message,
      timestamp: new Date().toISOString(),
      direction: 'OUTGOING'
    };

    // Functional Mocking: Persist to local storage
    const existing = JSON.parse(localStorage.getItem(`medagent_messages`) || '[]');
    localStorage.setItem(`medagent_messages`, JSON.stringify([...existing, newMessage]));

    setIsSending(false);
    setSent(true);
    
    if (onSendSuccess) onSendSuccess(newMessage);
    
    setTimeout(() => {
      onClose();
      // Reset after modal closes
      setTimeout(() => {
        setSent(false);
        setMessage('');
        setSelectedTopic('General');
      }, 500);
    }, 2000);
  };

  if (!doctor) return null;

  const doctorImg = doctor.avatarUrl || (doctor.gender === 'F' ? femaleAvatar : maleAvatar);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-[250]"
          />
          <div className="fixed inset-0 z-[251] flex items-center justify-center p-4" onClick={onClose}>
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-lg"
            >
              <GlassCard className="bg-white/90 border-white/60 shadow-2xl rounded-[3rem] p-8 md:p-10 relative overflow-hidden">
                {!sent ? (
                  <>
                    <button onClick={onClose} className={`absolute top-6 ${isRtl ? 'left-6' : 'right-6'} p-2 rounded-full hover:bg-slate-100 transition-colors text-slate-400`}>
                      <X className="w-6 h-6" />
                    </button>

                    <div className="flex items-center gap-5 mb-10">
                      <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center text-blue-600 border border-blue-100 shadow-sm shrink-0 overflow-hidden relative">
                         <img src={doctorImg} alt={doctor.name} className="w-full h-full object-cover" />
                      </div>
                      <div>
                        <h3 className="text-2xl font-black text-slate-800 tracking-tight">{doctor.name}</h3>
                        <div className="flex items-center gap-2 mt-1">
                           <span className="w-2 h-2 rounded-full bg-green-500"></span>
                           <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{doctor.specialty} • {t('doctors.activeNow')}</span>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-8">
                       {/* Topic Selection Tokens */}
                       <div className="space-y-4">
                          <label className="text-[10px] font-black uppercase tracking-[0.2em] text-blue-600 ml-1">{t('doctors.inquiryTopic')}</label>
                          <div className="grid grid-cols-2 gap-3">
                             {topics.map((topic) => {
                               const Icon = topic.icon;
                               const isSelected = selectedTopic === topic.id;
                               return (
                                 <button
                                   key={topic.id}
                                   onClick={() => setSelectedTopic(topic.id)}
                                   className={`flex items-center gap-3 p-3 rounded-2xl border transition-all ${isSelected ? 'bg-blue-600 border-blue-600 text-white shadow-lg shadow-blue-500/20' : 'bg-white border-slate-100 text-slate-600 hover:border-blue-200'}`}
                                 >
                                   <div className={`p-1.5 rounded-lg ${isSelected ? 'bg-white/20' : 'bg-blue-50'}`}>
                                      <Icon className={`w-4 h-4 ${isSelected ? 'text-white' : 'text-blue-500'}`} />
                                   </div>
                                   <span className="text-xs font-bold">{topic.label}</span>
                                 </button>
                               );
                             })}
                          </div>
                       </div>

                       {/* Message Textarea */}
                       <div className="space-y-4">
                          <label className="text-[10px] font-black uppercase tracking-[0.2em] text-blue-600 ml-1">{t('doctors.yourMessage')}</label>
                          <textarea 
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            placeholder={t('doctors.describeConcern', { doctor: doctor.name })}
                            className="w-full min-h-[160px] bg-slate-50/50 border border-slate-100 rounded-[2rem] p-6 text-sm font-bold text-slate-900 focus:bg-white focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 outline-none transition-all resize-none shadow-inner"
                          />
                       </div>

                       <Button 
                         variant="primary" 
                         className="w-full py-5 rounded-[1.5rem] shadow-blue-600/30 font-black text-base group"
                         onClick={handleSend}
                         disabled={isSending || !message.trim()}
                       >
                         {isSending ? (
                           <span className="flex items-center gap-2">
                             <Activity className="w-5 h-5 animate-spin" /> {t('doctors.dispatching')}
                           </span>
                         ) : (
                           <span className="flex items-center gap-2">
                             {t('doctors.sendSecure')} <Send className={`w-5 h-5 transition-transform ${isRtl ? 'group-hover:-translate-x-1' : 'group-hover:translate-x-1'} group-hover:-translate-y-1`} />
                           </span>
                         )}
                       </Button>
                    </div>
                  </>
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <motion.div 
                      initial={{ scale: 0 }} 
                      animate={{ scale: 1 }}
                      className="w-24 h-24 bg-green-500 text-white rounded-full flex items-center justify-center mb-8 shadow-2xl shadow-green-500/20"
                    >
                      <CheckCircle2 className="w-12 h-12" />
                    </motion.div>
                    <h3 className="text-3xl font-black text-slate-800 mb-4 tracking-tight">{t('doctors.messageDispatched')}</h3>
                    <p className="text-slate-500 font-bold text-lg leading-relaxed max-w-[280px] mb-10">
                      {t('doctors.processInquiry')}
                    </p>
                    <Button variant="secondary" className="w-full py-4 rounded-2xl" onClick={onClose}>{t('doctors.returnDashboard')}</Button>
                  </div>
                )}
              </GlassCard>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
