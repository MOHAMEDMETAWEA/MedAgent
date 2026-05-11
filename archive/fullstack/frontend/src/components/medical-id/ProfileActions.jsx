import React from 'react';
import { UniversalImagePicker } from '../ui/UniversalImagePicker';
import { useTranslation } from 'react-i18next';

export function ProfileActions({ onUpdateHealth, onImageSelect, className = '' }) {
  const { t } = useTranslation();
  return (
    <div className={`flex items-center gap-3 w-full ${className}`}>
      {/* Weight 2: Update Health Data (On the left) */}
      <button 
        onClick={onUpdateHealth}
        className="flex-[2] py-4 px-2 lg:px-6 rounded-[1.25rem] bg-blue-600 text-white text-[clamp(9px,2.2vw,14px)] font-bold tracking-tight hover:shadow-lg hover:shadow-blue-600/20 transition-all active:scale-[0.98] shadow-md shadow-blue-500/10 whitespace-nowrap overflow-hidden"
      >
        {t('medicalId.updateHealth', 'Update Health Data')}
      </button>

      {/* Weight 1: Change Photo (On the right) */}
      <div className="flex-1 min-w-0">
        <UniversalImagePicker onImageSelect={onImageSelect} showAvatars={true} className="w-full">
          <button 
            type="button"
            className="w-full py-4 px-2 lg:px-6 rounded-[1.25rem] bg-amber-50 text-amber-600 flex items-center justify-center hover:bg-amber-100/80 hover:shadow-xl hover:shadow-amber-500/10 transition-all shadow-md shadow-amber-500/5 group border border-amber-200/40 relative overflow-hidden" 
            title={t('medicalId.changePhoto', 'Change Photo')}
          >
            <span className="text-[clamp(9px,2.2vw,14px)] font-bold tracking-tighter whitespace-nowrap mx-1 lg:mx-4">{t('medicalId.changePhoto', 'Change Photo')}</span>
          </button>
        </UniversalImagePicker>
      </div>
    </div>
  );
}
