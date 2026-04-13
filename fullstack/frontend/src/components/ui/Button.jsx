import React from 'react';
import { motion } from 'framer-motion';

export const Button = ({ children, variant = 'primary', className = '', ...props }) => {
  const baseStyles = "relative inline-flex items-center justify-center font-inter font-medium transition-all duration-300 overflow-hidden";
  
  const variants = {
    primary: "bg-primary-gradient text-[var(--color-on-primary)] rounded-full px-8 py-3.5 shadow-liquid-glass hover:shadow-[var(--shadow-liquid-glow)]",
    secondary: "bg-glass border-ghost text-[var(--color-primary)] rounded-[2rem] px-8 py-3.5 shadow-liquid-glass hover:bg-[var(--color-surface-container)]",
    tertiary: "text-[var(--color-on-primary-fixed-variant)] px-6 py-3 rounded-[1.5rem] hover:bg-[var(--color-surface-container)]"
  };

  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`${baseStyles} ${variants[variant]} ${className}`}
      {...props}
    >
      {/* Shine effect for primary button */}
      {variant === 'primary' && (
        <span className="absolute inset-0 bg-gradient-to-tr from-white/0 via-white/20 to-white/0 opacity-0 hover:opacity-100 transition-opacity duration-500" />
      )}
      <span className="relative z-10">{children}</span>
    </motion.button>
  );
};
