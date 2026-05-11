import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Activity, Heart, Droplet, AlertTriangle, Info, CheckCircle2, ChevronRight, ActivitySquare, ArrowLeft, ArrowRight } from 'lucide-react';
import { Button } from '../ui/Button';

export function FirstAidModal({ isOpen, onClose }) {
  const { t, i18n } = useTranslation();
  const [selectedId, setSelectedId] = useState(null);
  const isRTL = i18n.language === 'ar';

  const firstAidData = [
    {
      id: 'cpr',
      title: t('firstAid.cpr.title'),
      icon: <Heart className="w-6 h-6 text-red-500" />,
      color: 'red',
      steps: [
        t('firstAid.cpr.step1'),
        t('firstAid.cpr.step2'),
        t('firstAid.cpr.step3'),
        t('firstAid.cpr.step4'),
        t('firstAid.cpr.step5'),
        t('firstAid.cpr.step6')
      ]
    },
    {
      id: 'choking',
      title: t('firstAid.choking.title'),
      icon: <Activity className="w-6 h-6 text-orange-500" />,
      color: 'orange',
      steps: [
        t('firstAid.choking.step1'),
        t('firstAid.choking.step2'),
        t('firstAid.choking.step3'),
        t('firstAid.choking.step4'),
        t('firstAid.choking.step5')
      ]
    },
    {
      id: 'bleeding',
      title: t('firstAid.bleeding.title'),
      icon: <Droplet className="w-6 h-6 text-red-600" />,
      color: 'red',
      steps: [
        t('firstAid.bleeding.step1'),
        t('firstAid.bleeding.step2'),
        t('firstAid.bleeding.step3'),
        t('firstAid.bleeding.step4'),
        t('firstAid.bleeding.step5')
      ]
    },
    {
      id: 'stroke',
      title: t('firstAid.stroke.title'),
      icon: <ActivitySquare className="w-6 h-6 text-blue-500" />,
      color: 'blue',
      steps: [
        t('firstAid.stroke.step1'),
        t('firstAid.stroke.step2'),
        t('firstAid.stroke.step3'),
        t('firstAid.stroke.step4'),
        t('firstAid.stroke.step5')
      ]
    },
    {
      id: 'anaphylaxis',
      title: t('firstAid.anaphylaxis.title'),
      icon: <AlertTriangle className="w-6 h-6 text-purple-500" />,
      color: 'purple',
      steps: [
        t('firstAid.anaphylaxis.step1'),
        t('firstAid.anaphylaxis.step2'),
        t('firstAid.anaphylaxis.step3'),
        t('firstAid.anaphylaxis.step4'),
        t('firstAid.anaphylaxis.step5')
      ]
    }
  ];

  const selectedGuide = firstAidData.find(g => g.id === selectedId);

  return (
    <AnimatePresence>
      {isOpen && (
        <React.Fragment>
          {/* Backdrop */}
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-[#0c0d0e]/60 backdrop-blur-md z-[99998]"
          />
          
          {/* Modal Container */}
          <div className="fixed inset-0 z-[99999] flex items-center justify-center p-4 pointer-events-none">
            <motion.div 
              initial={{ opacity: 0, scale: 0.9, y: 40 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 40 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="w-full max-w-2xl bg-white/95 backdrop-blur-3xl rounded-[2.5rem] border border-slate-200/60 shadow-[0_40px_80px_rgba(0,0,0,0.15)] flex flex-col max-h-[90vh] overflow-hidden pointer-events-auto"
            >
              {/* Header */}
              <div className="flex items-center justify-between p-8 border-b border-slate-100 shrink-0">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-red-50 flex items-center justify-center text-red-500 shadow-sm border border-red-100/50">
                    <ActivitySquare className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-black text-slate-800 tracking-tight text-start">{t('firstAid.title')}</h3>
                    <p className="text-xs text-slate-500 font-bold uppercase tracking-widest mt-0.5 text-start">{t('firstAid.subtitle')}</p>
                  </div>
                </div>
                <button 
                  onClick={onClose} 
                  className="p-3 bg-slate-100 hover:bg-slate-200 ms-auto rounded-2xl transition-all active:scale-95 text-slate-500"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              {/* Body */}
              <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
                {!selectedId ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {firstAidData.map((guide) => (
                      <button
                        key={guide.id}
                        onClick={() => setSelectedId(guide.id)}
                        className="p-6 bg-slate-50/50 rounded-3xl border border-slate-200/60 hover:bg-white hover:border-blue-200 hover:shadow-lg hover:shadow-blue-500/5 transition-all group flex items-center justify-between"
                      >
                        <div className="flex items-center gap-4">
                          <div className={`p-3 rounded-xl bg-white shadow-sm border border-slate-100 group-hover:scale-110 transition-transform`}>
                            {guide.icon}
                          </div>
                          <div className="text-start">
                            <h4 className="font-extrabold text-slate-800">{guide.title}</h4>
                            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-tight">{t('firstAid.protocolStepByStep')}</p>
                          </div>
                        </div>
                        <ArrowRight className="w-5 h-5 text-slate-300 group-hover:text-blue-500 group-hover:translate-x-1 rtl:group-hover:-translate-x-1 transition-all rtl:-scale-x-100" />
                      </button>
                    ))}
                  </div>
                ) : (
                  <motion.div 
                    initial={{ opacity: 0, x: isRTL ? -20 : 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="space-y-8"
                  >
                    <button 
                      onClick={() => setSelectedId(null)}
                      className="inline-flex items-center gap-2 text-xs font-black text-blue-600 uppercase tracking-widest hover:opacity-70 transition-all"
                    >
                      <ArrowLeft className="w-4 h-4 rtl:-scale-x-100" />
                      {t('firstAid.backToAll')}
                    </button>
                    
                    <div className="flex items-center gap-4 p-6 bg-slate-50/80 rounded-3xl border border-slate-200/60">
                      <div className="p-4 bg-white rounded-2xl shadow-sm border border-slate-100">
                        {selectedGuide.icon}
                      </div>
                      <div className="text-start">
                        <h4 className="text-2xl font-black text-slate-800 tracking-tight">{selectedGuide.title}</h4>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                          <span className="text-[10px] font-black text-emerald-600 uppercase tracking-widest">{t('firstAid.ahaVerified')}</span>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-4">
                      {selectedGuide.steps.map((step, index) => (
                        <div key={index} className="flex gap-4 items-start p-5 bg-white border border-slate-100 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
                          <div className="w-8 h-8 shrink-0 bg-blue-50 text-blue-600 rounded-lg flex items-center justify-center font-black text-sm">
                            {index + 1}
                          </div>
                          <p className="text-sm font-bold text-slate-700 leading-relaxed pt-1.5 text-start">{step}</p>
                        </div>
                      ))}
                    </div>

                    <div className="p-6 bg-orange-50 border border-orange-100 rounded-3xl flex gap-4">
                      <AlertTriangle className="w-6 h-6 text-orange-500 shrink-0 mt-0.5" />
                      <p className="text-xs font-bold text-orange-800 leading-relaxed text-start">
                        {t('firstAid.emergencyWarning')}
                      </p>
                    </div>
                  </motion.div>
                )}
              </div>

              {/* Footer */}
              <div className="p-8 border-t border-slate-100 shrink-0 flex justify-end">
                <Button variant="secondary" onClick={onClose} className="px-10 font-bold">{t('global.close')}</Button>
              </div>
            </motion.div>
          </div>

          <style>{`
            .custom-scrollbar::-webkit-scrollbar {
              width: 4px;
            }
            .custom-scrollbar::-webkit-scrollbar-track {
              background: transparent;
            }
            .custom-scrollbar::-webkit-scrollbar-thumb {
              background: rgba(0, 0, 0, 0.05);
              border-radius: 10px;
            }
          `}</style>
        </React.Fragment>
      )}
    </AnimatePresence>
  );
}
