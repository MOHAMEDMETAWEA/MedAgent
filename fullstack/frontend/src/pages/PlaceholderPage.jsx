import React from 'react';
import { GlassCard } from '../components/ui/GlassCard';

export function PlaceholderPage({ title, description, icon: Icon }) {
  return (
    <div className="w-full h-[80vh] flex items-center justify-center">
      <GlassCard hoverEffect className="p-12 md:p-20 flex flex-col items-center text-center max-w-2xl bg-glass-heavy shadow-liquid-glass backdrop-blur-3xl">
        <div className="bg-white/40 p-6 rounded-[2rem] border border-[rgba(158,181,200,0.3)] shadow-inner mb-8">
          {Icon && <Icon className="w-16 h-16 text-[var(--color-primary)]" />}
        </div>
        <h1 className="text-4xl md:text-5xl font-manrope font-extrabold text-[var(--color-on-surface)] mb-4 tracking-tight">
          {title}
        </h1>
        <p className="text-lg text-[var(--color-on-surface-variant)] font-inter leading-relaxed max-w-md mx-auto">
          {description}
        </p>
      </GlassCard>
    </div>
  );
}
