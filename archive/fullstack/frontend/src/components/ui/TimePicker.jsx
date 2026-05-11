import React, { useState, useRef, useEffect } from 'react';
import { Clock, Check, ChevronUp, ChevronDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { createPortal } from 'react-dom';

export function TimePicker({ label, value, onChange, onOpenChange, shiftY = 0, className = '' }) {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef(null);
  const [coords, setCoords] = useState({ top: 0, left: 0, width: 0 });

  // Translation helpers
  const amLabel = t('global.am', 'AM');
  const pmLabel = t('global.pm', 'PM');
  const hourLabel = t('global.hourLabel', 'HOUR');
  const minLabel = t('global.minLabel', 'MIN');
  const confirmText = t('global.confirm', 'Confirm');
  const cancelText = t('global.cancel', 'Cancel');

  // Parser: value like "08:30 AM" or "08:30 ص"
  const parseTime = (val) => {
    if (!val) return { hour: '08', minute: '00', period: amLabel };
    
    // Normalize period from value
    let period = amLabel;
    if (val.includes('PM') || val.includes('م')) period = pmLabel;

    const [h, m] = val.split(':');
    const minute = m ? m.split(' ')[0] : '00';
    return { hour: h || '08', minute, period };
  };

  const [tempTime, setTempTime] = useState(parseTime(value));

  useEffect(() => {
    if (onOpenChange) {
      onOpenChange(isOpen);
    }
  }, [isOpen, onOpenChange]);

  const updateCoords = () => {
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const scrollY = window.scrollY;
      const scrollX = window.scrollX;
      
      setCoords({
        top: rect.bottom + scrollY + 8,
        left: rect.left + scrollX,
        width: rect.width
      });
    }
  };

  const toggleOpen = () => {
    if (!isOpen) {
      setTempTime(parseTime(value));
      updateCoords();
    }
    setIsOpen(!isOpen);
  };

  const handleDone = () => {
    const formatted = `${tempTime.hour}:${tempTime.minute} ${tempTime.period}`;
    onChange({ target: { value: formatted } });
    setIsOpen(false);
  };

  const hours = Array.from({ length: 12 }, (_, i) => (i + 1).toString().padStart(2, '0'));
  const minutes = Array.from({ length: 12 }, (_, i) => (i * 5).toString().padStart(2, '0'));

  return (
    <div className={`relative ${className}`} ref={containerRef}>
      {label && (
        <label className="block text-[10px] font-black text-slate-400 uppercase tracking-[0.15em] mb-2.5 px-1 text-start">
          {label}
        </label>
      )}
      
      <button
        type="button"
        onClick={toggleOpen}
        className={`w-full flex items-center justify-between px-5 py-3.5 bg-slate-50 border border-slate-200/60 rounded-2xl transition-all duration-300 hover:border-blue-400/50 hover:bg-white hover:shadow-sm group ${
          isOpen ? 'ring-2 ring-blue-500/20 border-blue-500 bg-white shadow-md' : ''
        }`}
      >
        <div className="flex items-center gap-3">
          <Clock className={`w-4 h-4 ${isOpen ? 'text-blue-500' : 'text-slate-400'} group-hover:text-blue-500 transition-colors`} />
          <span className="text-sm font-bold text-slate-700">{value || `08:00 ${amLabel}`}</span>
        </div>
        <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform duration-300 ${isOpen ? 'rotate-180 text-blue-500' : ''}`} />
      </button>

      {createPortal(
        <div className="timepicker-portal-container" style={{ position: 'absolute', top: 0, left: 0, width: '100%', pointerEvents: 'none', zIndex: 9999999 }}>
          <AnimatePresence>
            {isOpen && (
              <motion.div
                initial={{ opacity: 0, y: -10, scale: 0.95 }}
                animate={{ 
                  opacity: 1, 
                  y: shiftY, 
                  scale: 1 
                }}
                exit={{ opacity: 0, y: -10, scale: 0.95 }}
                transition={{ duration: 0.25, ease: "easeOut" }}
                style={{
                  position: 'absolute',
                  top: coords.top,
                  left: coords.left,
                  width: coords.width,
                  minWidth: '280px',
                  pointerEvents: 'auto'
                }}
                className="bg-white border border-slate-200 shadow-[0_20px_50px_rgba(0,0,0,0.12)] rounded-[2rem] p-6 overflow-hidden"
              >
                <div className="grid grid-cols-3 gap-6 mb-6">
                  {/* Hour */}
                  <div className="space-y-4">
                    <span className="block text-[9px] font-black text-slate-400 text-center tracking-widest">{hourLabel}</span>
                    <div className="h-40 overflow-y-auto no-scrollbar snap-y snap-mandatory bg-slate-50/50 rounded-2xl border border-slate-100 flex flex-col items-center">
                      {hours.map(h => (
                        <button
                          key={h}
                          onClick={() => setTempTime({ ...tempTime, hour: h })}
                          className={`w-full py-3 snap-center text-sm font-black transition-all ${
                            tempTime.hour === h ? 'text-blue-600 bg-white shadow-sm' : 'text-slate-300 hover:text-slate-500'
                          }`}
                        >
                          {h}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Minute */}
                  <div className="space-y-4">
                    <span className="block text-[9px] font-black text-slate-400 text-center tracking-widest">{minLabel}</span>
                    <div className="h-40 overflow-y-auto no-scrollbar snap-y snap-mandatory bg-slate-50/50 rounded-2xl border border-slate-100 flex flex-col items-center">
                      {minutes.map(m => (
                        <button
                          key={m}
                          onClick={() => setTempTime({ ...tempTime, minute: m })}
                          className={`w-full py-3 snap-center text-sm font-black transition-all ${
                            tempTime.minute === m ? 'text-blue-600 bg-white shadow-sm' : 'text-slate-300 hover:text-slate-500'
                          }`}
                        >
                          {m}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Period */}
                  <div className="space-y-4">
                    <span className="block text-[9px] font-black text-slate-400 text-center tracking-widest">&nbsp;</span>
                    <div className="flex flex-col gap-2">
                      {[amLabel, pmLabel].map(p => (
                        <button
                          key={p}
                          onClick={() => setTempTime({ ...tempTime, period: p })}
                          className={`py-6 rounded-2xl text-xs font-black transition-all border ${
                            tempTime.period === p 
                            ? 'bg-blue-600 text-white border-blue-600 shadow-md' 
                            : 'bg-white text-slate-400 border-slate-100 hover:border-slate-200'
                          }`}
                        >
                          {p}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="flex gap-3 pt-4 border-t border-slate-100">
                  <button 
                    onClick={() => setIsOpen(false)}
                    className="flex-1 py-3 text-xs font-black text-slate-400 hover:text-slate-600 transition-colors"
                  >
                    {cancelText}
                  </button>
                  <button 
                    onClick={handleDone}
                    className="flex-1 py-3 bg-blue-600 text-white rounded-xl text-xs font-black shadow-lg shadow-blue-600/20 active:scale-95 transition-all"
                  >
                    {confirmText}
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>,
        document.body
      )}
    </div>
  );
}
