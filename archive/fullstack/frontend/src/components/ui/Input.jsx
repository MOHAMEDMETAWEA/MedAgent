import React from 'react';
import { motion } from 'framer-motion';

export const Input = React.forwardRef(({ label, id, error, required, className = '', ...props }, ref) => {
  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      {label && (
        <label htmlFor={id} className="text-sm font-inter text-[var(--color-on-surface-variant)] ms-2 flex items-center gap-1">
          {label}
          {required && <span className="text-red-500 font-bold" title="Required">*</span>}
        </label>
      )}
      <motion.div
        whileTap={{ scale: 0.995 }}
        className="relative"
      >
        <input
          id={id}
          ref={ref}
          className={`w-full bg-[var(--color-surface-container-low)] text-[var(--color-on-surface)] rounded-[1.5rem] px-5 py-3.5 outline-none transition-all duration-300 border border-transparent shadow-inner focus:bg-white/50 focus:backdrop-blur-xl
            ${error ? 'border-red-400 focus:border-red-500 bg-red-50/10' : 'focus:border-ghost-focus'}`}
          {...props}
        />
      </motion.div>
      {error && (
        <motion.p 
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-[10px] font-bold text-red-500 uppercase tracking-widest ms-3 mt-1"
        >
          {error}
        </motion.p>
      )}
    </div>
  );
});

Input.displayName = 'Input';
