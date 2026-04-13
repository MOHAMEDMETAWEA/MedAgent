import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Shield, CheckCircle2, Calendar, FileText, User, ArrowLeft, Activity } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export default function SharedInsurance() {
  const { t } = useTranslation();
  const { id } = useParams();
  
  // Extract info from the ID (simple mock reconstruction)
  const parts = id.split('-');
  const firstName = parts[1] || 'Valued';
  const memberId = parts[2] || 'XXXX-XXXX-XXXX';

  return (
    <div className="min-h-screen bg-[#F8FAFF] py-12 px-6 flex flex-col items-center justify-center relative overflow-hidden">
      {/* Background Decor */}
      <div className="absolute top-[-10%] right-[-10%] w-[50vw] h-[50vw] bg-blue-100/40 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[40vw] h-[40vw] bg-indigo-100/30 rounded-full blur-[80px] pointer-events-none" />

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-[480px] w-full bg-white rounded-[3rem] shadow-[0_40px_100px_rgba(0,0,0,0.08)] border border-slate-100 p-10 relative z-10"
      >
        <div className="flex flex-col items-center text-center space-y-6">
          {/* Status Icon */}
          <div className="w-20 h-20 bg-emerald-50 rounded-[2rem] flex items-center justify-center relative shadow-sm border border-emerald-100/50">
            <CheckCircle2 className="w-10 h-10 text-emerald-500" />
            <div className="absolute -bottom-2 -right-2 bg-white p-1.5 rounded-full shadow-md border border-emerald-100">
              <Shield className="w-4 h-4 text-emerald-600" />
            </div>
          </div>

          <div className="space-y-2">
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">{t('shared.verifiedToken')}</h1>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-[0.2em]">{t('shared.secureAccess')}</p>
          </div>

          <div className="w-full h-px bg-gradient-to-r from-transparent via-slate-100 to-transparent" />

          {/* Member Details */}
          <div className="w-full space-y-4">
            <div className="bg-slate-50 p-6 rounded-[2rem] border border-slate-100/50 flex flex-col gap-4">
              <div className="flex justify-between items-center group">
                <div className="flex items-center gap-3">
                  <User className="w-4 h-4 text-blue-500 opacity-60" />
                  <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{t('global.policyHolder')}</span>
                </div>
                <span className="font-bold text-slate-700 capitalize">{firstName} User</span>
              </div>
              <div className="flex justify-between items-center group">
                <div className="flex items-center gap-3">
                  <FileText className="w-4 h-4 text-blue-500 opacity-60" />
                  <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{t('global.memberId')}</span>
                </div>
                <span className="font-mono text-xs font-black text-slate-900 tracking-wider">#{memberId}</span>
              </div>
              <div className="flex justify-between items-center group">
                <div className="flex items-center gap-3">
                  <Calendar className="w-4 h-4 text-blue-500 opacity-60" />
                  <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{t('global.status')}</span>
                </div>
                <span className="bg-emerald-500 text-white text-[9px] font-black px-3 py-1 rounded-full uppercase tracking-widest">{t('global.activeCoverage')}</span>
              </div>
            </div>
            
            <div className="p-6 bg-blue-600 rounded-[2rem] shadow-xl shadow-blue-600/20 text-start relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-24 h-24 bg-white/10 blur-2xl rounded-full group-hover:scale-110 transition-transform" />
              <Activity className="w-6 h-6 text-white/40 mb-3" />
              <p className="text-[10px] font-black text-white/60 uppercase tracking-widest mb-1">{t('global.authNote')}</p>
              <p className="text-white text-xs font-bold leading-relaxed">
                {t('shared.authNoteDesc')}
              </p>
            </div>
          </div>

          <div className="pt-6 w-full">
            <Link 
              to="/"
              className="flex items-center justify-center gap-2 text-slate-400 hover:text-blue-600 transition-colors text-xs font-black uppercase tracking-widest"
            >
              <ArrowLeft className="w-4 h-4 rtl:-scale-x-100" /> {t('shared.exitSecureView')}
            </Link>
          </div>
        </div>
      </motion.div>

      <p className="mt-12 text-[10px] font-bold text-slate-400 text-center max-w-[300px] leading-relaxed">
        &copy; 2026 MedAgent AI Health Systems. All rights reserved. 
        {t('shared.poweredBy')}
      </p>
    </div>
  );
}
