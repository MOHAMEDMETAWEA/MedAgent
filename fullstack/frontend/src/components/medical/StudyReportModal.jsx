import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Download, Share2, ShieldCheck, CheckCircle2, AlertCircle, FileText, Activity, BrainCircuit } from 'lucide-react';
import { Button } from '../ui/Button';
import { useTranslation } from 'react-i18next';

export function StudyReportModal({ isOpen, onClose, scan }) {
  const { i18n } = useTranslation();
  const isRtl = i18n.dir() === 'rtl';
  if (!scan) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[150] flex items-center justify-center p-4 md:p-8 overflow-hidden" onClick={onClose}>
          {/* Backdrop */}
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-slate-900/60 backdrop-blur-md"
          />

          {/* Modal Content */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            onClick={(e) => e.stopPropagation()}
            className="relative z-10 w-full max-w-4xl bg-white rounded-[2.5rem] shadow-[0_40px_100px_rgba(0,0,0,0.25)] flex flex-col md:flex-row overflow-hidden max-h-[90vh]"
          >
            {/* Left Side: Study Image & Stats */}
            <div className="w-full md:w-[45%] bg-slate-50 p-6 md:p-10 flex flex-col items-center justify-center border-r border-slate-100 overflow-y-auto">
              <div className="w-full aspect-square rounded-[2rem] overflow-hidden shadow-2xl border-8 border-white mb-8 group relative cursor-zoom-in">
                <img src={scan.imgUrl} alt={scan.type} className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" />
                <div className={`absolute top-4 ${isRtl ? 'right-4' : 'left-4'}`}>
                  <span className="px-3 py-1 bg-blue-600 text-white text-[10px] font-black uppercase tracking-widest rounded-full shadow-lg">HD NEURAL CAPTURE</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 w-full">
                <div className="p-4 bg-white rounded-2xl border border-slate-100 shadow-sm">
                  <p className="text-[10px] uppercase font-bold text-slate-400 tracking-widest mb-1">Study Date</p>
                  <p className="text-sm font-extrabold text-slate-700">{new Date(scan.id).toLocaleDateString()}</p>
                </div>
                <div className="p-4 bg-white rounded-2xl border border-slate-100 shadow-sm">
                  <p className="text-[10px] uppercase font-bold text-slate-400 tracking-widest mb-1">Neural Match</p>
                  <p className="text-sm font-extrabold text-blue-600">99.4% Precision</p>
                </div>
              </div>
            </div>

            {/* Right Side: Clinical Report */}
            <div className="flex-1 p-8 md:p-10 flex flex-col h-full overflow-y-auto custom-scrollbar">
              <div className="flex justify-between items-start mb-8">
                <div>
                  <h2 className="text-2xl font-black text-slate-900 leading-tight">{scan.type} Analysis Report</h2>
                  <p className="text-sm text-slate-500 font-bold mt-1 uppercase tracking-widest">Digital Healthcare Protocol v9.4</p>
                </div>
                <button onClick={onClose} className="p-2 hover:bg-slate-100 rounded-full transition-colors text-slate-400">
                  <X className="w-6 h-6" />
                </button>
              </div>

              {/* Status Section */}
              <div className={`p-5 rounded-[1.5rem] mb-8 flex items-center gap-4 border ${
                scan.status === 'Anomaly Detected' ? 'bg-red-50 border-red-100' : 'bg-green-50 border-green-100'
              }`}>
                {scan.status === 'Anomaly Detected' ? <AlertCircle className="w-8 h-8 text-red-600 shrink-0" /> : <CheckCircle2 className="w-8 h-8 text-green-600 shrink-0" />}
                <div>
                  <h4 className={`text-lg font-black ${scan.status === 'Anomaly Detected' ? 'text-red-900' : 'text-green-900'}`}>
                    Status: {scan.status}
                  </h4>
                  <p className={`text-xs font-bold leading-relaxed ${scan.status === 'Anomaly Detected' ? 'text-red-700' : 'text-green-700'}`}>
                    {scan.status === 'Anomaly Detected' ? "Requires immediate clinical review." : "No critical abnormalities detected by the neural engine."}
                  </p>
                </div>
              </div>

              {/* Clinical Summary */}
              <div className="space-y-6 mb-8">
                <section>
                  <div className="flex items-center gap-2 mb-3">
                    <Activity className="w-5 h-5 text-blue-600" />
                    <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest">Clinical Identification</h3>
                  </div>
                  <p className="text-slate-600 font-medium leading-relaxed">
                    The MedAgent AI identified consistent tissue density and markers matching the standard protocol for {scan.type}. Analysis confirms proper alignment of structural elements within the study frame.
                  </p>
                </section>

                <section>
                  <div className="flex items-center gap-2 mb-3">
                    <BrainCircuit className="w-5 h-5 text-purple-600" />
                    <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest">Neural Key Insights</h3>
                  </div>
                  <ul className="grid grid-cols-1 gap-2">
                    {scan.insights.map((insight, idx) => (
                      <li key={idx} className="flex gap-2 items-start py-2 px-4 bg-slate-50 rounded-xl text-slate-700 font-bold text-sm">
                        <CheckCircle2 className="w-4 h-4 text-blue-500 mt-0.5 shrink-0" />
                        {insight}
                      </li>
                    ))}
                  </ul>
                </section>

                <section>
                  <div className="flex items-center gap-2 mb-3">
                    <ShieldCheck className="w-5 h-5 text-emerald-600" />
                    <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest">Clinical Recommendation</h3>
                  </div>
                  <p className="text-slate-600 font-medium leading-relaxed">
                    MedAgent recommends sharing this report with your Primary Care Physician. Continue following your prescribed health protocol and alert your provider if symptoms change.
                  </p>
                </section>
              </div>

              {/* Actions Footer */}
              <div className="mt-auto pt-8 border-t border-slate-100 flex flex-wrap gap-4">
                <Button variant="primary" className="flex-1 bg-blue-600 hover:bg-blue-700 gap-2 font-black py-4">
                  <Download className="w-5 h-5" /> {t('medicalId.downloadReport', 'Download Report PDF')}
                </Button>
                <div className="flex gap-3 w-full sm:w-auto">
                  <button className="p-4 rounded-2xl bg-slate-100 hover:bg-slate-200 transition-all text-slate-600">
                    <Share2 className="w-5 h-5" />
                  </button>
                  <button 
                    onClick={onClose}
                    className="p-4 px-8 rounded-2xl bg-white border border-slate-200 hover:bg-slate-50 transition-all text-slate-700 font-black uppercase tracking-widest text-xs"
                  >
                    {t('medicalId.close', 'Close')}
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
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
    </AnimatePresence>
  );
}
