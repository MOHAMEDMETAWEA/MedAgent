import React from 'react';
import { useTranslation } from 'react-i18next';
import { GlassCard } from '../ui/GlassCard';
import { Button } from '../ui/Button';
import { AlertCircle, RefreshCw, Info } from 'lucide-react';

export function PrescriptionCard({ med }) {
  const { t } = useTranslation();
  return (
    <GlassCard hoverEffect className="p-6 flex flex-col justify-between min-h-[220px] bg-glass border-ghost backdrop-blur-xl">
      <div>
        <div className="flex justify-between items-start mb-4">
          <div className="bg-primary-gradient p-3 rounded-2xl shadow-liquid-glass">
            <div className="w-6 h-6 text-white font-bold flex items-center justify-center font-manrope">Rx</div>
          </div>
          {med.warning && (
            <span className="flex items-center text-xs font-bold text-orange-600 bg-orange-100/50 px-3 py-1 rounded-full border border-orange-200">
              <AlertCircle className="w-3 h-3 me-1" /> {med.warning}
            </span>
          )}
        </div>
        <h2 className="text-xl font-bold font-manrope text-[var(--color-on-surface)]">{med.name}</h2>
        <p className="text-[var(--color-primary)] font-semibold mt-1">
          {med.dose} <span className="text-[var(--color-on-surface-variant)] font-normal ms-2">{med.freq}</span>
        </p>
      </div>
      
      <div className="mt-6 flex items-center justify-between border-t border-[rgba(158,181,200,0.15)] pt-4">
        <div className="flex flex-col">
          <span className="text-xs text-[var(--color-on-surface-variant)] uppercase tracking-wider font-bold">{t('medicines.remaining')}</span>
          <span className="text-lg font-semibold">{med.remaining} {t('medicines.pills')}</span>
        </div>
        {med.refill ? (
          <Button variant="secondary" className="px-4 py-2 text-sm">
            <RefreshCw className="w-4 h-4 me-2" /> {t('medicines.refill')}
          </Button>
        ) : (
          <span className="text-sm text-[var(--color-on-surface-variant)] flex items-center">
            <Info className="w-4 h-4 me-1"/> {t('medicines.upToDate')}
          </span>
        )}
      </div>
    </GlassCard>
  );
}
