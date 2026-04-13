import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { createPortal } from 'react-dom';
import { useTranslation } from 'react-i18next';

export function Select({ label, options, value, onChange, onOpenChange, placeholder, shiftY = 0, className = '' }) {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef(null);
  const [coords, setCoords] = useState({ top: 0, left: 0, width: 0 });
  const displayPlaceholder = placeholder || t('global.selectOption', 'Select option');

  useEffect(() => {
    if (onOpenChange) {
      onOpenChange(isOpen);
    }
  }, [isOpen, onOpenChange]);

  const updateCoords = () => {
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const scrollY = window.scrollY;
      const scrollX = window.scrollX;
      
      setCoords({
        top: rect.bottom + scrollY + 8,
        left: rect.left + scrollX,
        width: rect.width
      });
    }
  };

  const toggleDropdown = () => {
    if (!isOpen) updateCoords();
    setIsOpen(!isOpen);
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        if (!event.target.closest('.select-portal-container')) {
          setIsOpen(false);
        }
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      window.addEventListener('resize', updateCoords);
      window.addEventListener('scroll', updateCoords, true);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      window.removeEventListener('resize', updateCoords);
      window.removeEventListener('scroll', updateCoords, true);
    };
  }, [isOpen]);

  const selectedOption = options.find(opt => 
    (typeof opt === 'string' ? opt : opt.value) === value
  );

  const handleSelect = (option) => {
    const val = typeof option === 'string' ? option : option.value;
    onChange({ target: { value: val } });
    setIsOpen(false);
  };

  return (
    <div className={`relative ${className}`} ref={containerRef}>
      {label && (
        <label className="block text-[10px] font-black text-slate-400 uppercase tracking-[0.15em] mb-2.5 px-1 text-start">
          {label}
        </label>
      )}
      <button
        type="button"
        onClick={toggleDropdown}
        className={`w-full flex items-center justify-between px-5 py-3.5 bg-slate-50 border border-slate-200/60 rounded-2xl transition-all duration-300 hover:border-blue-400/50 hover:bg-white hover:shadow-sm group ${
          isOpen ? 'ring-2 ring-blue-500/20 border-blue-500 bg-white shadow-md' : ''
        }`}
      >
        <span className={`text-sm font-bold ${!selectedOption ? 'opacity-40' : 'text-slate-700'}`}>
          {selectedOption ? (typeof selectedOption === 'string' ? selectedOption : selectedOption.label) : displayPlaceholder}
        </span>
        <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform duration-300 ${isOpen ? 'rotate-180 text-blue-500' : 'group-hover:text-slate-600'}`} />
      </button>

      {createPortal(
        <div className="select-portal-container" style={{ position: 'absolute', top: 0, left: 0, width: '100%', pointerEvents: 'none', zIndex: 9999999 }}>
          <AnimatePresence>
            {isOpen && (
              <motion.div
                initial={{ opacity: 0, y: -10, scale: 0.95 }}
                animate={{ 
                  opacity: 1, 
                  y: shiftY, 
                  scale: 1 
                }}
                exit={{ opacity: 0, y: -10, scale: 0.95 }}
                transition={{ duration: 0.25, ease: "easeOut" }}
                style={{
                  position: 'absolute',
                  top: coords.top,
                  left: coords.left,
                  width: coords.width,
                  pointerEvents: 'auto'
                }}
                className="bg-white border border-slate-200 shadow-[0_12px_40px_rgba(0,0,0,0.12)] rounded-3xl overflow-hidden"
              >
                <div className="p-1.5 max-h-[280px] overflow-y-auto no-scrollbar">
                  {options.map((option, idx) => {
                    const labelStr = typeof option === 'string' ? option : option.label;
                    const valStr = typeof option === 'string' ? option : option.value;
                    const isSelected = valStr === value;

                    return (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => handleSelect(option)}
                        className={`w-full flex items-center justify-between px-4 py-3 rounded-2xl text-sm font-bold transition-all duration-200 mb-0.5 last:mb-0 ${
                          isSelected 
                            ? 'bg-blue-600 text-white' 
                            : 'text-slate-600 hover:bg-blue-50 hover:text-blue-600'
                        }`}
                      >
                        <span>{labelStr}</span>
                        {isSelected && <Check className="w-4 h-4 text-white" />}
                      </button>
                    );
                  })}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>,
        document.body
      )}
    </div>
  );
}
