import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { PhoneOff, Mic, MicOff, Video, VideoOff, Volume2, User, Activity } from 'lucide-react';
import femaleAvatar from '../../assets/female-avatar.svg';
import maleAvatar from '../../assets/male-avatar.svg';
import { GlassCard } from '../ui/GlassCard';

export function CallingModal({ isOpen, onClose, doctor }) {
  const { t } = useTranslation();
  const [callStatus, setCallStatus] = useState(t('doctors.connecting'));
  const [duration, setDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOn, setIsVideoOn] = useState(true);

  useEffect(() => {
    if (!isOpen) return;

    const timer = setTimeout(() => {
      setCallStatus(t('doctors.ringing'));
      setTimeout(() => {
        setCallStatus(t('doctors.inCall'));
      }, 3000);
    }, 1500);

    return () => clearTimeout(timer);
  }, [isOpen]);

  useEffect(() => {
    let interval;
    if (callStatus === t('doctors.inCall')) {
      interval = setInterval(() => {
        setDuration(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [callStatus]);

  const formatDuration = (sec) => {
    const mins = Math.floor(sec / 60);
    const secs = sec % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (!doctor) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <React.Fragment>
          {/* Dark Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-slate-900/95 backdrop-blur-3xl z-[300] flex items-center justify-center p-4 md:p-8"
          />
          
          <div className="fixed inset-0 z-[301] flex items-center justify-center p-4" onClick={onClose}>
            <motion.div
              initial={{ scale: 0.9, y: 40, opacity: 0 }}
              animate={{ scale: 1, y: 0, opacity: 1 }}
              exit={{ scale: 0.9, y: 40, opacity: 0 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-lg h-[80vh] min-h-[600px] flex flex-col relative"
            >
              {/* Main Call UI */}
              <GlassCard className="flex-1 rounded-[3rem] bg-gradient-to-b from-slate-900/40 to-slate-800/60 border-slate-700/50 shadow-2xl overflow-hidden flex flex-col items-center justify-between p-12 relative">
                
                {/* Background Decoration */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full opacity-10 pointer-events-none">
                   <div className="absolute top-[-20%] left-[-20%] w-[140%] h-[140%] bg-blue-500 rounded-full blur-[150px] animate-pulse"></div>
                </div>

                <div className="flex flex-col items-center z-10 w-full mt-8">
                  <div className="relative mb-10">
                    {/* Ringing Animation */}
                    <div className="absolute inset-0 bg-blue-500/20 rounded-full animate-ping scale-[2]"></div>
                    <div className="absolute inset-0 bg-blue-400/10 rounded-full animate-ping scale-[1.5] repeat-1000"></div>
                    
                    <div className="w-32 h-32 rounded-[2.5rem] bg-slate-800 border-4 border-slate-700/50 shadow-2xl overflow-hidden relative group">
                       <img src={doctor.avatarUrl || (doctor.gender === 'F' ? femaleAvatar : maleAvatar)} alt={doctor.name} className="w-full h-full object-cover" />
                       {isVideoOn && callStatus === 'In Call' && (
                         <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center">
                            <Video className="w-8 h-8 text-white opacity-40" />
                         </div>
                       )}
                    </div>
                  </div>

                  <h2 className="text-3xl font-black text-white mb-2 tracking-tight">{doctor.name}</h2>
                  <div className="flex flex-col items-center gap-2">
                    <span className="px-4 py-1.5 bg-white/10 rounded-full text-xs font-black text-blue-300 uppercase tracking-widest border border-white/5">
                      {doctor.specialty}
                    </span>
                    <span className={`text-sm font-bold mt-2 ${callStatus === t('doctors.inCall') ? 'text-green-400' : 'text-slate-400 animate-pulse'}`}>
                      {callStatus === t('doctors.inCall') ? formatDuration(duration) : callStatus}
                    </span>
                  </div>
                </div>

                {/* Call Status Pill */}
                <div className="bg-white/5 backdrop-blur-xl px-6 py-3 rounded-2xl border border-white/10 flex items-center gap-3 z-10">
                   <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></div>
                   <span className="text-[10px] font-black text-white/60 uppercase tracking-[0.2em]">{t('doctors.encryptionActive')}</span>
                   <Activity className="w-4 h-4 text-white/20" />
                </div>

                {/* Controls */}
                <div className="flex items-center gap-6 z-10 mt-12 mb-4">
                   <button 
                     onClick={() => setIsMuted(!isMuted)}
                     className={`w-16 h-16 rounded-3xl flex items-center justify-center transition-all ${isMuted ? 'bg-red-500/80 text-white shadow-xl shadow-red-500/20' : 'bg-white/10 text-white hover:bg-white/20'}`}
                   >
                     {isMuted ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
                   </button>
                   
                   <button 
                      onClick={onClose}
                      className="w-20 h-20 bg-red-600 rounded-[2rem] flex items-center justify-center text-white shadow-2xl shadow-red-600/40 hover:bg-red-500 hover:scale-110 active:scale-95 transition-all group"
                   >
                     <PhoneOff className="w-8 h-8 group-hover:rotate-[135deg] transition-transform duration-500" />
                   </button>

                   <button 
                     onClick={() => setIsVideoOn(!isVideoOn)}
                     className={`w-16 h-16 rounded-3xl flex items-center justify-center transition-all ${!isVideoOn ? 'bg-slate-700 text-white' : 'bg-white/10 text-white hover:bg-white/20'}`}
                   >
                     {isVideoOn ? <Video className="w-6 h-6" /> : <VideoOff className="w-6 h-6" />}
                   </button>
                </div>
              </GlassCard>
            </motion.div>
          </div>
        </React.Fragment>
      )}
    </AnimatePresence>
  );
}
