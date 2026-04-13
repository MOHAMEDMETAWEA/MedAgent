import React from 'react';
import { GlassCard } from '../ui/GlassCard';

export function ScanHistoryCard({ scan, isFirst }) {
  return (
    <GlassCard 
      hoverEffect 
      className={`p-4 cursor-pointer ${isFirst ? 'border-[var(--color-primary)] bg-glass-heavy shadow-liquid-glass' : 'bg-glass border-ghost'}`}
    >
      <p className="text-xs text-[var(--color-primary)] font-bold">{scan.date}</p>
      <h4 className="font-bold text-[var(--color-on-surface)] mt-1">{scan.type}</h4>
      <p className="text-xs text-[var(--color-on-surface-variant)] mt-2">{scan.status}</p>
    </GlassCard>
  );
}
