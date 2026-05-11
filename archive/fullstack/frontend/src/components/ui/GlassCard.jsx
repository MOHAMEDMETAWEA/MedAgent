import React from 'react';
import { motion } from 'framer-motion';
import { theme } from '../../theme/tokens';

export const GlassCard = ({ children, className = '', hoverEffect = false, variant = 'light', ...props }) => {
  const baseClasses = `relative overflow-hidden ${theme.borderRadius.card} ${theme.glass[variant]} transition-all duration-500`;
  
  if (hoverEffect) {
    return (
      <motion.div
        whileHover={{ y: -8, scale: 1.01 }}
        transition={theme.animations.spring}
        className={`${baseClasses} ${className}`}
        {...props}
      >
        <div className="absolute inset-0 bg-gradient-to-br from-white/40 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
        {children}
      </motion.div>
    );
  }

  return (
    <div className={`${baseClasses} ${className}`} {...props}>
      <div className="absolute inset-0 bg-gradient-to-br from-white/20 via-transparent to-transparent pointer-events-none" />
      {children}
    </div>
  );
};
