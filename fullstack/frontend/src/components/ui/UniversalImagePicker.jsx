import React, { useState, useRef, useEffect } from 'react';
import { Camera, Image as ImageIcon, Cloud, X, Check, RefreshCw, Loader2, User } from 'lucide-react';
import { useImagePicker } from '../../hooks/useImagePicker';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import maleAvatar from '../../assets/male-avatar.svg';
import femaleAvatar from '../../assets/female-avatar.svg';

/**
 * UniversalImagePicker Component
 * A reusable component that provides a button/trigger and a menu for picking images.
 * Supports: Camera, Gallery, and Google Drive.
 */
export function UniversalImagePicker({ 
  onImageSelect, 
  currentImage = null, 
  shape = 'circle', // 'circle' or 'square'
  label = 'Add Photo',
  className = "",
  showAvatars = false,
  children
}) {
  const { t } = useTranslation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [stream, setStream] = useState(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  
  const { 
    selectedImage, 
    isPickerLoading,
    openGallery, 
    openCamera, 
    openDrive,
    resetImage 
  } = useImagePicker((img) => {
    onImageSelect(img);
    setIsMenuOpen(false);
  });

  const displayImage = selectedImage || currentImage;

  // --- CAMERA LOGIC ---
  const startCamera = async () => {
    const s = await openCamera();
    if (s) {
      setStream(s);
      setIsCameraOpen(true);
      setIsMenuOpen(false);
    }
  };

  const closeCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
    setStream(null);
    setIsCameraOpen(false);
  };

  useEffect(() => {
    if (isCameraOpen && videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [isCameraOpen, stream]);

  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const context = canvasRef.current.getContext('2d');
      canvasRef.current.width = videoRef.current.videoWidth;
      canvasRef.current.height = videoRef.current.videoHeight;
      context.drawImage(videoRef.current, 0, 0);
      const base64 = canvasRef.current.toDataURL('image/png');
      onImageSelect(base64);
      closeCamera();
    }
  };

  const handleDrive = () => {
    openDrive();
  };

  const handleGallery = () => {
    openGallery();
  };

  const handleAvatarSelect = (avatarPath) => {
    onImageSelect(avatarPath);
    setIsMenuOpen(false);
  };

  return (
    <div className={`relative ${className}`}>
      {/* Trigger Button */}
      {children ? (
        <div onClick={() => setIsMenuOpen(true)} className="cursor-pointer">
          {children}
        </div>
      ) : (
        <button 
          type="button" 
          onClick={() => setIsMenuOpen(true)}
          className={`group relative overflow-hidden transition-all duration-300 border-2 border-dashed border-slate-300 hover:border-[var(--color-primary)] hover:bg-slate-50 shadow-sm
            ${shape === 'circle' ? 'rounded-full w-24 h-24' : 'rounded-2xl w-full h-40'}
            ${displayImage ? 'border-solid border-[var(--color-primary)]/30' : ''}
          `}
        >
          {displayImage ? (
            <>
              <img src={displayImage} alt="Preview" className="w-full h-full object-cover" />
              <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                <Camera className="w-6 h-6 text-white" />
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center text-slate-400 group-hover:text-[var(--color-primary)]">
              <ImageIcon className="w-8 h-8 mb-1" />
              <span className="text-[10px] font-bold uppercase tracking-widest">{label}</span>
            </div>
          )}
          
          {isPickerLoading && (
            <div className="absolute inset-0 bg-white/60 backdrop-blur-sm flex items-center justify-center">
              <Loader2 className="w-6 h-6 text-[var(--color-primary)] animate-spin" />
            </div>
          )}
        </button>
      )}

      {/* Selection Menu Backdrop (Centered Floating Island) */}
      <AnimatePresence>
        {isMenuOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 md:p-12">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-slate-900/10 backdrop-blur-sm" 
              onClick={() => setIsMenuOpen(false)} 
            />
            <motion.div 
              initial={{ opacity: 0, scale: 0.9, y: 30 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 30 }}
              transition={{ type: "spring", damping: 25, stiffness: 400 }}
              className="relative z-[110] w-[95%] max-w-sm bg-slate-800/90 backdrop-blur-3xl border border-white/10 rounded-[2.5rem] shadow-[0_40px_80px_rgba(0,0,0,0.4)] overflow-hidden flex flex-col max-h-[85vh]"
            >
              {/* Header */}
              <div className="flex items-center justify-between p-6 pb-2 shrink-0">
                <h3 className="text-sm font-black text-white uppercase tracking-widest opacity-80 pl-2">{t('global.selectSource')}</h3>
                <button type="button" onClick={() => setIsMenuOpen(false)} className="p-2 hover:bg-white/10 rounded-full transition-colors text-white/40">
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              {/* Scrollable Content */}
              <div className="flex-1 overflow-y-auto p-6 pt-2 custom-scrollbar">
                <div className="grid grid-cols-3 gap-3 mb-6">
                  <button type="button" onClick={startCamera} className="flex flex-col items-center gap-3 p-4 rounded-2xl bg-white/5 hover:bg-white/10 transition-all group border border-white/5">
                    <div className="bg-blue-500/20 p-3 rounded-xl group-hover:scale-110 transition-transform"><Camera className="w-5 h-5 text-blue-400" /></div>
                    <span className="text-[10px] font-bold text-white/60">{t('global.camera')}</span>
                  </button>
                  <button type="button" onClick={handleGallery} className="flex flex-col items-center gap-3 p-4 rounded-2xl bg-white/5 hover:bg-white/10 transition-all group border border-white/5">
                    <div className="bg-purple-500/20 p-3 rounded-xl group-hover:scale-110 transition-transform"><ImageIcon className="w-5 h-5 text-purple-400" /></div>
                    <span className="text-[10px] font-bold text-white/60">{t('global.gallery')}</span>
                  </button>
                  <button type="button" onClick={handleDrive} className="flex flex-col items-center gap-3 p-4 rounded-2xl bg-white/5 hover:bg-white/10 transition-all group border border-white/5">
                    <div className="bg-amber-500/20 p-3 rounded-xl group-hover:scale-110 transition-transform"><Cloud className="w-5 h-5 text-amber-400" /></div>
                    <span className="text-[10px] font-bold text-white/60">{t('global.drive')}</span>
                  </button>
                </div>

                {showAvatars && (
                  <div className="pt-6 border-t border-white/5">
                    <p className="text-[10px] font-black text-white/30 uppercase tracking-[0.2em] mb-4 text-center">{t('global.orUseAvatar')}</p>
                    <div className="flex justify-center gap-8">
                      <button 
                        type="button"
                        onClick={() => handleAvatarSelect(maleAvatar)}
                        className="flex flex-col items-center gap-2 group"
                      >
                        <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center group-hover:scale-110 group-hover:bg-white/10 transition-all duration-300 overflow-hidden">
                          <img src={maleAvatar} alt="Male" className="w-12 h-12 object-contain" />
                        </div>
                        <span className="text-[10px] font-bold text-white/40 uppercase tracking-tighter">{t('global.male')}</span>
                      </button>
                      <button 
                        type="button"
                        onClick={() => handleAvatarSelect(femaleAvatar)}
                        className="flex flex-col items-center gap-2 group"
                      >
                        <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center group-hover:scale-110 group-hover:bg-white/10 transition-all duration-300 overflow-hidden">
                          <img src={femaleAvatar} alt="Female" className="w-12 h-12 object-contain" />
                        </div>
                        <span className="text-[10px] font-bold text-white/40 uppercase tracking-tighter">{t('global.female')}</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Camera Modal */}
      <AnimatePresence>
        {isCameraOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/80 backdrop-blur-xl" onClick={closeCamera} />
            <motion.div 
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="relative bg-black rounded-[2.5rem] overflow-hidden w-full max-w-lg aspect-video shadow-2xl border border-white/10"
            >
              <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover" />
              <canvas ref={canvasRef} className="hidden" />
              
              <div className="absolute inset-x-0 bottom-0 p-8 flex items-center justify-center gap-6 bg-gradient-to-t from-black/80 to-transparent">
                <button onClick={closeCamera} className="w-14 h-14 rounded-full bg-white/10 backdrop-blur-lg border border-white/20 flex items-center justify-center hover:bg-white/20 transition-all">
                  <X className="w-6 h-6 text-white" />
                </button>
                <button onClick={capturePhoto} className="w-20 h-20 rounded-full bg-white flex items-center justify-center shadow-2xl active:scale-90 transition-all border-4 border-white/30">
                  <div className="w-16 h-16 rounded-full border-2 border-black/10" />
                </button>
                <button className="w-14 h-14 rounded-full bg-white/10 backdrop-blur-lg border border-white/20 flex items-center justify-center hover:bg-white/20 transition-all opacity-40">
                  <RefreshCw className="w-6 h-6 text-white" />
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <style>{`
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
  );
}
