import React from 'react';
import { GlassCard } from '../ui/GlassCard';
import { Button } from '../ui/Button';
import { MessageCircle, Video, Calendar, Star, Send, PhoneCall } from 'lucide-react';
import femaleAvatar from '../../assets/female-avatar.svg';
import maleAvatar from '../../assets/male-avatar.svg';
import { useTranslation } from 'react-i18next';

export function DoctorCard({ doc, onCall, onBook, onSchedule, onMessage }) {
  const { t } = useTranslation();
  const isOnline = doc.status === 'ONLINE';
  const isBusy = doc.status === 'BUSY';
  
  return (
    <div className="group relative flex flex-col bg-white/80 backdrop-blur-3xl rounded-[2rem] p-6 transition-all duration-300 hover:translate-y-[-8px] border-ghost shadow-[0_10px_40px_rgba(0,0,0,0.03)] border border-white">
      <div className="absolute inset-0 bg-[var(--color-primary)]/5 rounded-[2rem] opacity-0 group-hover:opacity-100 transition-opacity"></div>
      <div className="flex items-start justify-between mb-6 relative">
        <div className="relative">
          <img alt={doc.name} className="w-20 h-20 rounded-2xl object-cover grayscale group-hover:grayscale-0 transition-all border border-[rgba(158,181,200,0.15)] shadow-sm" src={doc.avatarUrl || (doc.gender === 'F' ? femaleAvatar : maleAvatar)} />
          <span className={`absolute -bottom-2 -right-2 w-6 h-6 border-4 border-white rounded-full ${isOnline ? 'bg-green-500' : isBusy ? 'bg-amber-500' : 'bg-slate-300'}`}></span>
        </div>
        <div className="text-end">
          <div className={`text-xs font-bold px-3 py-1 rounded-full inline-block ${isOnline ? 'bg-blue-100 text-[var(--color-primary)]' : isBusy ? 'bg-slate-100 text-slate-500' : 'bg-slate-100 text-slate-400'}`}>
            {t(`doctors.${doc.status.toLowerCase()}`)}
          </div>
        </div>
      </div>

      <div className="relative mb-6">
        <h3 className="text-xl font-extrabold text-[#191c1e] group-hover:text-[var(--color-primary)] transition-colors">{doc.name}</h3>
        <p className="text-[#434656] font-bold text-sm tracking-wide mt-1">{doc.specialty}</p>
        <div className="mt-3 flex items-center gap-1 text-sm text-[#434656]">
          <Star className="w-4 h-4 text-orange-400 fill-orange-400" />
          <span className="font-bold text-black">{doc.rating}</span>
          <span className="mx-1 opacity-30">•</span>
          <span className="font-semibold">{doc.exp}</span>
        </div>
      </div>

      <div className="flex gap-3 mt-auto relative">
        {isOnline || isBusy ? (
          <button 
            onClick={() => isOnline ? onCall?.(doc) : onBook?.(doc)}
            className={`flex-1 py-3 text-sm font-bold rounded-xl transition-all shadow-sm flex items-center justify-center gap-2 ${isOnline ? 'bg-[var(--color-primary)] text-white hover:bg-opacity-90' : 'bg-blue-50 text-[var(--color-primary)] hover:bg-blue-100'}`}
          >
            {isOnline ? t('doctors.callNow') : t('doctors.bookSlot')}
          </button>
        ) : (
          <button className="flex-1 py-3 bg-slate-100 text-slate-400 rounded-xl font-bold text-sm cursor-not-allowed">
            {t('doctors.unavailable')}
          </button>
        )}
        
        <button 
          onClick={() => onMessage?.(doc)}
          className="p-3 border border-slate-200/60 bg-white/60 rounded-xl text-[var(--color-primary)] hover:bg-blue-50 transition-colors"
          title={t('doctors.sendQuickMessage')}
        >
          <MessageCircle className="w-5 h-5" />
        </button>

        <button 
          onClick={() => onSchedule?.(doc)}
          className="p-3 border border-slate-200/60 bg-white/60 rounded-xl text-[var(--color-primary)] hover:bg-blue-50 transition-colors"
          title={t('doctors.viewSchedule')}
        >
          <Calendar className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
