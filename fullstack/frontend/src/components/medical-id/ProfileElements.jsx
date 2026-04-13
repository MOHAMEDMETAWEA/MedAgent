import React from 'react';

export function Metric({ icon: Icon, label, value, color }) {
  return (
    <div className="flex flex-col gap-2">
      <div className={`p-2 rounded-xl bg-white/50 w-max shadow-sm border border-white ${color}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <p className="text-xs text-[var(--color-on-surface-variant)] uppercase tracking-wider font-bold">{label}</p>
        <p className="font-bold text-[var(--color-on-surface)] mt-0.5">{value}</p>
      </div>
    </div>
  );
}

export const UserSilhouette = () => (
  <svg viewBox="0 0 24 24" fill="none" className="w-12 h-12 text-blue-200" stroke="currentColor" strokeWidth="1.5">
    <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
  </svg>
);

export const PhoneIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
    <path fillRule="evenodd" d="M1.5 4.5a3 3 0 0 1 3-3h1.372c.86 0 1.61.586 1.819 1.42l1.105 4.423a1.875 1.875 0 0 1-.694 1.955l-1.293.97c-.135.101-.164.249-.126.352a11.285 11.285 0 0 0 6.697 6.697c.103.038.25.009.352-.126l.97-1.293a1.875 1.875 0 0 1 1.955-.694l4.423 1.105c.834.209 1.42.959 1.42 1.82V19.5a3 3 0 0 1-3 3h-2.25C8.552 22.5 1.5 15.448 1.5 6.75V4.5Z" clipRule="evenodd" />
  </svg>
);
