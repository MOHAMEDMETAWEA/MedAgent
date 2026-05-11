import React from 'react';
import { Navigation2 } from 'lucide-react';

export function FacilityCard({ facility }) {
  return (
    <div className="bg-white/50 p-4 border border-[rgba(158,181,200,0.15)] rounded-2xl flex justify-between items-center shadow-sm">
      <div>
        <h4 className="font-bold text-[var(--color-on-surface)]">{facility.name}</h4>
        <p className="text-sm text-[var(--color-on-surface-variant)]">{facility.distance} • Wait time: {facility.waitTime}</p>
      </div>
      <button className="bg-[var(--color-primary-container)] text-[var(--color-primary)] p-3 rounded-full hover:bg-[var(--color-primary)] hover:text-white transition-all">
        <Navigation2 className="w-5 h-5" />
      </button>
    </div>
  );
}
