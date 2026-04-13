import React from 'react';
import { motion } from 'framer-motion';

export const Textarea = React.forwardRef(({ label, id, className = '', ...props }, ref) => {
  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      {label && (
        <label htmlFor={id} className="text-sm font-inter text-[var(--color-on-surface-variant)] ms-2 uppercase font-black tracking-widest text-[10px]">
          {label}
        </label>
      )}
      <motion.div
        whileTap={{ scale: 0.995 }}
        className="relative"
      >
        <textarea
          id={id}
          ref={ref}
          rows={3}
          className="w-full bg-[var(--color-surface-container-low)] text-[var(--color-on-surface)] rounded-[1.5rem] px-5 py-3.5 outline-none transition-all duration-300 focus:border-ghost-focus border border-transparent shadow-inner focus:bg-white/50 focus:backdrop-blur-xl resize-none font-bold text-sm"
          {...props}
        />
      </motion.div>
    </div>
  );
});

Textarea.displayName = 'Textarea';
