import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { X, Shield, Camera, Share2, Wallet, FileText, QrCode, CheckCircle2, Copy, Download } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';

export function DigitalInsuranceCard({ isOpen, onClose }) {
  const { t, i18n } = useTranslation();
  const isRtl = i18n.dir() === 'rtl';
  const { userData } = useAuth();
  const [isShareOpen, setIsShareOpen] = useState(false);
  const [isAdded, setIsAdded] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  
  const data = userData.insurance || {};
  const hasPhoto = !!data.cardImage;

  const handleAddToWallet = () => {
    setIsAdded(true);
    setTimeout(() => setIsAdded(false), 3000);
  };

  const handleCopy = () => {
    const shareLink = `${window.location.origin}/share/insurance-${userData.firstName.toLowerCase()}-${data.memberId || 'guest'}`;
    navigator.clipboard.writeText(shareLink).then(() => {
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    });
  };

  const handleSaveImage = async () => {
    try {
      const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=500x500&data=MedAgent-Insurance-${userData.firstName}-${data.memberId || 'GUEST'}`;
      
      const response = await fetch(qrUrl);
      const blob = await response.blob();
      
      // Explicitly type the blob and sanitize filename
      const typedBlob = new Blob([blob], { type: 'image/png' });
      const blobUrl = URL.createObjectURL(typedBlob);
      const safeName = (userData.firstName || 'User').replace(/[^a-z0-9]/gi, '_').toLowerCase();
      
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `MedAgent_Insurance_${safeName}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(blobUrl);

      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 2000);
    } catch (err) {
      console.error("Save failed, opening in tab as fallback", err);
      window.open(`https://api.qrserver.com/v1/create-qr-code/?size=500x500&data=MedAgent-Insurance-${userData.firstName}-${data.memberId || 'GUEST'}`, '_blank');
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[120] flex items-center justify-center p-4" onClick={onClose}>
        {/* Backdrop */}
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-slate-900/90 backdrop-blur-xl"
          onClick={onClose}
        />
        
        {/* Modal Container */}
        <div className="relative z-[130] w-full max-w-[500px] max-h-[95vh] flex flex-col isolate" onClick={(e) => e.stopPropagation()}>
          <div className="flex-1 overflow-y-auto pointer-events-auto custom-scrollbar p-6 pt-16">
            {/* Close Button */}
            <button 
              onClick={onClose}
              className={`absolute -top-1 ${isRtl ? 'left-6' : 'right-6'} p-3 bg-white/10 hover:bg-white/20 rounded-full text-white transition-all border border-white/10 z-50 shadow-2xl`}
            >
              <X className="w-6 h-6" />
            </button>

            {/* Content Logic: Photo First, No Toggles if photo exists */}
            <AnimatePresence mode="wait">
              {hasPhoto ? (
                <motion.div 
                  key="photo-only-view"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="w-full aspect-video rounded-[2.5rem] overflow-hidden shadow-[0_40px_80px_rgba(0,0,0,0.5)] border border-white/10 bg-slate-800 relative"
                >
                  <img src={data.cardImage} alt="Insurance Card Photo" className="w-full h-full object-cover" />
                  <div className={`absolute top-6 ${isRtl ? 'right-6' : 'left-6'} bg-emerald-500/90 backdrop-blur-md px-4 py-2 rounded-2xl border border-white/20 flex items-center gap-2 shadow-lg`}>
                    <div className="w-2 h-2 rounded-full bg-white animate-pulse" />
                    <span className="text-[10px] font-black text-white uppercase tracking-widest">{t('medicalId.verifiedDocument')}</span>
                  </div>
                </motion.div>
              ) : (
                <motion.div 
                  key="digital-fallback-view"
                  initial={{ opacity: 0, scale: 0.95, rotateX: 20 }}
                  animate={{ opacity: 1, scale: 1, rotateX: 0 }}
                  exit={{ opacity: 0, scale: 0.95, rotateX: 20 }}
                  className="w-full aspect-[1.6/1] bg-gradient-to-br from-blue-700 via-blue-600 to-indigo-800 rounded-[2.5rem] p-8 shadow-[0_40px_80px_rgba(0,0,0,0.5)] relative overflow-hidden text-white border border-white/20"
                >
                    {/* Holographic Overlays */}
                    <div className="absolute inset-0 bg-gradient-to-tr from-white/10 via-transparent to-transparent opacity-50" />
                    <div className="absolute -top-24 -right-24 w-64 h-64 bg-blue-400 blur-3xl opacity-30 rounded-full" />
                    
                    {/* Header */}
                    <div className="flex justify-between items-start relative z-10">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-white/20 backdrop-blur-md flex items-center justify-center border border-white/20">
                          <Shield className="w-6 h-6 text-white" />
                        </div>
                        <div>
                          <h3 className="text-sm font-black tracking-[0.2em] uppercase opacity-60">MedAgent</h3>
                          <h2 className="text-xl font-extrabold tracking-tight">{t('medicalId.insuranceId')}</h2>
                        </div>
                      </div>
                      <div className="text-end">
                        <span className="text-[10px] font-black uppercase tracking-widest bg-emerald-500/80 px-3 py-1.5 rounded-lg border border-white/10">{t('medicalId.activeCard')}</span>
                      </div>
                    </div>

                    {/* Provider Info */}
                    <div className="mt-12 space-y-1 relative z-10">
                      <p className="text-[10px] font-black text-white/50 uppercase tracking-widest">{data.providerName || t('medicalId.noData')}</p>
                      <h1 className="text-2xl font-bold tracking-tight">{userData.firstName} {userData.lastName}</h1>
                    </div>

                    {/* Bottom Info Bar */}
                    <div className="absolute bottom-0 inset-x-0 p-8 pt-0 flex justify-between items-end relative z-10">
                      <div className="flex gap-10">
                         <div>
                           <p className="text-[9px] font-black text-white/40 uppercase tracking-widest mb-1">{t('medicalId.memberId')}</p>
                           <p className="font-mono text-sm font-bold tracking-wider">{data.memberId || '---- ---- ----'}</p>
                         </div>
                         <div>
                           <p className="text-[9px] font-black text-white/40 uppercase tracking-widest mb-1">{t('medicalId.groupNumber')}</p>
                           <p className="font-mono text-sm font-bold tracking-wider">{data.groupNumber || '----'}</p>
                         </div>
                      </div>
                    </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Actions Section - Only Wallet and Share, No Toggles if has Photo */}
            <div className="mt-10 grid grid-cols-2 gap-4">
                <button 
                  onClick={handleAddToWallet}
                  disabled={isAdded}
                  className={`p-5 rounded-3xl flex items-center justify-center gap-3 active:scale-95 transition-all shadow-xl group border-2 ${isAdded ? 'bg-emerald-500 border-white text-white' : 'bg-white border-transparent text-[#191c1e]'}`}
                >
                  {isAdded ? <CheckCircle2 className="w-6 h-6 animate-bounce" /> : <Wallet className="w-6 h-6" />}
                  <span className="text-sm font-black uppercase tracking-widest text-[9px]">{isAdded ? t('medicalId.added') : t('medicalId.addWallet')}</span>
                </button>
                <button 
                  onClick={() => setIsShareOpen(true)}
                  className="bg-white p-5 rounded-3xl flex items-center justify-center gap-3 active:scale-95 transition-all shadow-xl group hover:bg-slate-50 border-2 border-transparent"
                >
                  <Share2 className="w-6 h-6 text-[#191c1e]" />
                  <span className="text-sm font-black text-[#191c1e] uppercase tracking-widest text-[9px]">{t('chat.translate')}</span>
                </button>
            </div>
          </div>
        </div>

        {/* Share Popup Overlay */}
        <AnimatePresence>
          {isShareOpen && (
            <div className="fixed inset-0 z-[200] flex items-center justify-center p-6" onClick={() => setIsShareOpen(false)}>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setIsShareOpen(false)}
                className="absolute inset-0 bg-black/60 backdrop-blur-md"
              />
              <motion.div
                initial={{ scale: 0.9, opacity: 0, y: 20 }}
                animate={{ scale: 1, opacity: 1, y: 0 }}
                exit={{ scale: 0.9, opacity: 0, y: 20 }}
                onClick={(e) => e.stopPropagation()}
                className="relative z-[210] w-full max-w-[400px] bg-white rounded-[3rem] p-8 shadow-[0_50px_100px_rgba(0,0,0,0.5)] overflow-hidden"
              >
                {/* Close */}
                <button 
                  onClick={() => setIsShareOpen(false)}
                  className={`absolute top-6 ${isRtl ? 'left-6' : 'right-6'} p-2 rounded-full hover:bg-slate-100 transition-colors`}
                >
                  <X className="w-5 h-5 text-slate-400" />
                </button>

                <div className="text-center space-y-6">
                  <div className="space-y-1">
                    <h2 className="text-xl font-black text-slate-900 tracking-tight">{t('medicalId.shareInsurance')}</h2>
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">{t('medicalId.digitalAccessToken')}</p>
                  </div>

                  {/* QR Code Section */}
                  <div className="mx-auto w-48 h-48 bg-white p-4 rounded-[2.5rem] border-2 border-slate-100 flex items-center justify-center relative group shadow-inner">
                    <div className="absolute inset-0 bg-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity rounded-[2.5rem]" />
                    <img 
                      src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=MedAgent-Insurance-${userData.firstName}-${data.memberId || 'GUEST'}`} 
                      alt={t('medicalId.scannableQr')}
                      className="w-full h-full object-contain rounded-xl"
                    />
                  </div>

                  {/* Info Card Preview */}
                  <div className="bg-slate-900 rounded-[2rem] p-6 text-start border border-white/10 shadow-lg relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-24 h-24 bg-blue-400/20 blur-3xl rounded-full" />
                    <div className="flex items-center gap-3 mb-4">
                      <Shield className="w-5 h-5 text-blue-400" />
                      <span className="text-[10px] font-black text-white/40 uppercase tracking-widest">{t('medicalId.medicalIdVerified')}</span>
                    </div>
                    <h3 className="text-white font-bold tracking-tight mb-1">{userData.firstName} {userData.lastName}</h3>
                    <p className="text-[9px] font-black text-white/50 uppercase tracking-tighter">{data.memberId || 'XXXX XXXX XXXX'}</p>
                  </div>

                  {/* Quick Actions */}
                  <div className="grid grid-cols-2 gap-3 pt-2">
                    <button 
                      onClick={handleCopy}
                      className={`flex items-center justify-center gap-2 py-4 rounded-2xl text-xs font-black uppercase tracking-widest transition-all ${isCopied ? 'bg-emerald-500 text-white shadow-lg' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
                    >
                      {isCopied ? <CheckCircle2 className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                      {isCopied ? t('global.copied') : t('global.copyLink')}
                    </button>
                    <button 
                      onClick={handleSaveImage}
                      className={`flex items-center justify-center gap-2 py-4 rounded-2xl text-xs font-black uppercase tracking-widest transition-all shadow-lg ${isSaved ? 'bg-emerald-500 text-white shadow-emerald-500/20' : 'bg-blue-600 text-white hover:bg-blue-700 shadow-blue-600/20'}`}
                    >
                      {isSaved ? <CheckCircle2 className="w-4 h-4" /> : <Download className="w-4 h-4" />}
                      {isSaved ? t('global.saved') : t('global.saveSession')}
                    </button>
                  </div>

                  <p className="text-[10px] text-slate-400 font-bold px-4 leading-relaxed">
                    {t('medicalId.expiryNote')}
                  </p>
                </div>
              </motion.div>
            </div>
          )}
        </AnimatePresence>

        <style jsx>{`
          .custom-scrollbar::-webkit-scrollbar {
            width: 4px;
          }
          .custom-scrollbar::-webkit-scrollbar-track {
            background: transparent;
          }
          .custom-scrollbar::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
          }
          .custom-scrollbar::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.2);
          }
        `}</style>
      </div>
    </AnimatePresence>
  );
}
