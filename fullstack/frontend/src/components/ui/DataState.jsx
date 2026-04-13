import React from 'react';
import { Activity, AlertOctagon } from 'lucide-react';

export function DataState({ loading, error, loadingText = "Loading...", errorText = "Error loading data", children }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh] w-full">
        <div className="flex flex-col items-center gap-4">
          <Activity className="w-10 h-10 text-[var(--color-primary)] animate-pulse" />
          <p className="text-sm font-bold text-[var(--color-on-surface-variant)] animate-pulse">{loadingText}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-[60vh] w-full">
        <div className="flex flex-col items-center gap-4 text-red-500 bg-red-50/50 backdrop-blur-md p-8 rounded-[2rem] border border-red-100 shadow-sm max-w-md mx-auto text-center">
          <AlertOctagon className="w-10 h-10" />
          <p className="font-extrabold text-lg tracking-tight text-red-700">{errorText}</p>
          <p className="text-sm font-medium text-red-600/80">{error.message || String(error)}</p>
        </div>
      </div>
    );
  }

  return children;
}
