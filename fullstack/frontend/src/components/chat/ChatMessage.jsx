import React from 'react';
import { motion } from 'framer-motion';
import { User, Activity } from 'lucide-react';

export function ChatMessage({ msg }) {
  const isUser = msg.sender === 'user';
  
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: 30 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 350, damping: 25 }}
      className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div className={`flex gap-4 md:gap-6 max-w-[90%] md:max-w-[75%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        <div className="flex-shrink-0 mt-2">
          {isUser ? (
            <div className="w-10 h-10 md:w-12 md:h-12 rounded-full bg-primary-gradient flex items-center justify-center shadow-liquid-glass">
              <User className="w-5 h-5 md:w-6 md:h-6 text-white" />
            </div>
          ) : (
            <div className="w-10 h-10 md:w-12 md:h-12 rounded-full bg-white flex items-center justify-center shadow-[var(--shadow-liquid-hover)] border border-[rgba(158,181,200,0.3)]">
               <Activity className="w-6 h-6 md:w-7 md:h-7 text-[var(--color-primary)]" />
            </div>
          )}
        </div>
        
        <div className={
          `p-6 md:p-8 rounded-[2rem] shadow-sm relative overflow-hidden ` + 
          (isUser
            ? `bg-primary-gradient text-white rounded-tr-none shadow-[var(--shadow-liquid-glow)]` 
            : `bg-white border-ghost text-[var(--color-on-surface)] rounded-tl-none shadow-[0_10px_40px_rgba(0,91,192,0.05)]`)
        }>
          {isUser && (
            <span className="absolute inset-0 bg-gradient-to-tr from-white/0 via-white/10 to-white/0 pointer-events-none" />
          )}
          <p className="font-inter leading-relaxed text-[1rem] opacity-95 relative z-10 tracking-wide">
            {msg.text}
          </p>
        </div>
      </div>
    </motion.div>
  );
}
