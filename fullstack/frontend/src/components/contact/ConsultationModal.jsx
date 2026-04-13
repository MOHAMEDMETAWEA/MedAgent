import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Calendar, Clock, CheckCircle2, ArrowRight } from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { Button } from '../ui/Button';
import { DatePicker } from '../ui/DatePicker';
import { Select } from '../ui/Select';
import femaleAvatar from '../../assets/female-avatar.svg';
import maleAvatar from '../../assets/male-avatar.svg';

export function ConsultationModal({ isOpen, onClose, doctor, onBookSuccess }) {
  const { t, i18n } = useTranslation();
  const isRtl = i18n.dir() === 'rtl';
  const [activeTab, setActiveTab] = useState('book'); // 'book' or 'schedule'
  const [date, setDate] = useState('');
  
  // Internal values stay in English/Standard for logic, but display is localized
  const [time, setTime] = useState('09:00 AM');
  const [type, setType] = useState('video');
  const [isBooking, setIsBooking] = useState(false);
  const [booked, setBooked] = useState(false);
  const [modalShiftY, setModalShiftY] = useState(0);

  const timeSlots = [
    "09:00 AM", "10:30 AM", "01:00 PM", "02:30 PM", "04:00 PM", "05:30 PM"
  ];

  const formatTimeSlot = (slot) => {
    if (!slot) return '';
    const isPM = slot.includes('PM');
    const timeOnly = slot.split(' ')[0];
    const period = isPM ? t('global.pm', 'PM') : t('global.am', 'AM');
    return `${timeOnly} ${period}`;
  };

  const handleBook = async () => {
    if (!date) return;
    setIsBooking(true);
    
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const newBooking = {
      id: Date.now(),
      doctorId: doctor.id,
      doctorName: doctor.name,
      date,
      time,
      type,
      status: 'CONFIRMED'
    };

    const existing = JSON.parse(localStorage.getItem(`medagent_bookings`) || '[]');
    localStorage.setItem(`medagent_bookings`, JSON.stringify([...existing, newBooking]));

    setIsBooking(false);
    setBooked(true);
    
    if (onBookSuccess) onBookSuccess(newBooking);
    
    setTimeout(() => {
      onClose();
      setTimeout(() => {
        setBooked(false);
        setDate('');
      }, 500);
    }, 2000);
  };

  if (!doctor) return null;

  const consultationOptions = [
    { label: t('doctors.types.video', 'Video Consultation'), value: 'video' },
    { label: t('doctors.types.audio', 'Audio Clinic'), value: 'audio' },
    { label: t('doctors.types.physical', 'Physical Visit'), value: 'physical' }
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-[200]"
          />
          <div className="fixed inset-0 z-[201] flex items-center justify-center p-4" onClick={onClose}>
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: modalShiftY }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-md"
            >
              <GlassCard className="p-8 bg-white/90 border-white/60 shadow-2xl rounded-[2.5rem] relative overflow-hidden">
                {!booked ? (
                  <>
                    <button onClick={onClose} className={`absolute top-6 ${isRtl ? 'left-6' : 'right-6'} p-2 rounded-full hover:bg-slate-100/50 transition-colors text-slate-400`}>
                      <X className="w-5 h-5" />
                    </button>

                    <div className="flex items-center gap-4 mb-8">
                      <div className="w-14 h-14 bg-blue-50 rounded-2xl flex items-center justify-center text-blue-600 border border-blue-100 shadow-sm shrink-0 overflow-hidden">
                        <img src={doctor.avatarUrl || (doctor.gender === 'F' ? femaleAvatar : maleAvatar)} alt={doctor.name} className="w-full h-full object-cover" />
                      </div>
                      <div>
                        <h3 className="text-xl font-black text-slate-800">{doctor.name}</h3>
                        <p className="text-xs font-bold text-blue-600 uppercase tracking-widest">{doctor.specialty}</p>
                      </div>
                    </div>

                    <div className="flex bg-slate-100/50 p-1 rounded-2xl mb-8 border border-slate-200/30">
                        <button 
                          onClick={() => setActiveTab('book')}
                          className={`flex-1 py-2.5 text-xs font-black uppercase tracking-widest rounded-xl transition-all ${activeTab === 'book' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-400 hover:text-slate-600'}`}
                        >
                          {t('doctors.bookSlot')}
                        </button>
                        <button 
                          onClick={() => setActiveTab('schedule')}
                          className={`flex-1 py-2.5 text-xs font-black uppercase tracking-widest rounded-xl transition-all ${activeTab === 'schedule' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-400 hover:text-slate-600'}`}
                        >
                          {t('doctors.availability')}
                        </button>
                    </div>

                    {activeTab === 'book' ? (
                      <div className="space-y-6">
                        <DatePicker 
                          label={t('doctors.selectDate')} 
                          value={date} 
                          onChange={(e) => setDate(e.target.value)}
                          shiftY={modalShiftY}
                        />
                        <Select 
                          label={t('doctors.preferredTime')}
                          value={time}
                          options={timeSlots.map(slot => ({ label: formatTimeSlot(slot), value: slot }))}
                          onChange={(e) => setTime(e.target.value)}
                          onOpenChange={(open) => setModalShiftY(open ? -120 : 0)}
                          shiftY={modalShiftY}
                        />
                        <Select 
                          label={t('doctors.consultationType')}
                          value={type}
                          options={consultationOptions}
                          onChange={(e) => setType(e.target.value)}
                          onOpenChange={(open) => setModalShiftY(open ? -160 : 0)}
                          shiftY={modalShiftY}
                        />

                        <Button 
                          variant="primary" 
                          className="w-full py-5 rounded-[1.5rem] mt-4 shadow-blue-500/20"
                          onClick={handleBook}
                          disabled={isBooking || !date}
                        >
                          {isBooking ? (
                            <span className="flex items-center gap-2">
                              <Clock className="w-4 h-4 animate-spin" /> {t('doctors.finalizing')}
                            </span>
                          ) : (
                            <span className="flex items-center gap-2">
                              {t('doctors.confirmAppointment')} <ArrowRight className="w-4 h-4 ms-2 rtl:-scale-x-100" />
                            </span>
                          )}
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-4 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar no-scrollbar">
                        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest px-1">{t('firstAid.upcomingSlots')}</p>
                        {timeSlots.map((slot, idx) => (
                          <div key={idx} className="bg-white border border-slate-100 p-4 rounded-2xl flex items-center justify-between group hover:border-blue-200 transition-all cursor-pointer" onClick={() => { setTime(slot); setActiveTab('book'); }}>
                            <div className="flex items-center gap-3">
                              <Calendar className="w-4 h-4 text-slate-300 group-hover:text-blue-500 transition-colors" />
                              <span className="text-sm font-bold text-slate-700">{t('doctors.tomorrow')}, {formatTimeSlot(slot)}</span>
                            </div>
                            <span className="text-[10px] font-black text-emerald-500 bg-emerald-50 px-2 py-1 rounded-lg">{t('firstAid.available')}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <div className="w-20 h-20 bg-emerald-500 text-white rounded-full flex items-center justify-center mb-8 shadow-xl shadow-emerald-500/20">
                      <CheckCircle2 className="w-10 h-10" />
                    </div>
                    <h3 className="text-2xl font-black text-slate-800 mb-2">{t('doctors.bookingConfirmed')}</h3>
                    <div className="text-slate-500 font-bold mb-8">
                      {t('doctors.appointmentScheduled', { 
                        date: new Intl.DateTimeFormat(i18n.language, { month: 'long', day: 'numeric', year: 'numeric' }).format(new Date(date)), 
                        time: formatTimeSlot(time) 
                      })}
                    </div>
                    <div className="p-4 bg-emerald-50 rounded-2xl border border-emerald-100 w-full mb-8">
                       <p className="text-[10px] font-black text-emerald-600 uppercase tracking-widest text-start mb-1">{t('doctors.electronicReceipt')}</p>
                       <p className="text-xs text-emerald-700 font-medium text-start leading-relaxed">
                         {t('doctors.confirmationSent')}
                       </p>
                    </div>
                    <Button variant="secondary" className="w-full" onClick={onClose}>{t('global.close')}</Button>
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
