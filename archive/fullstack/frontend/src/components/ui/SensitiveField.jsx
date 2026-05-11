import React, { useState, useEffect } from 'react';

// Basic scramble/unscramble to prevent purely static scraping of JS bundles 
// looking for exact strings if they are hardcoded.
const scrambleToken = (str) => btoa(encodeURIComponent(str || ''));
const unscrambleToken = (token) => {
  try {
    return decodeURIComponent(atob(token));
  } catch (e) {
    return '';
  }
};

/**
 * SensitiveField - Anti-Scraping Component
 * Prevents basic web scrapers from pulling sensitive info directly from the HTML source.
 * Injects the content dynamically via JavaScript after a slight delay, and uses 
 * CSS obfuscation techniques to make automated extraction harder.
 */
export const SensitiveField = ({ value, fallback = '-', className = '' }) => {
  const [displayedValue, setDisplayedValue] = useState(null);
  
  // Obfuscate initially to avoid raw string in DOM representation
  const [obfuscatedToken, setObfuscatedToken] = useState('');

  useEffect(() => {
    // Only proceed if value exists
    if (!value) return;

    const token = scrambleToken(value);
    setObfuscatedToken(token);

    // Minor delay to defeat curl-like scrapers that don't wait for React effects
    const timer = setTimeout(() => {
      setDisplayedValue(unscrambleToken(token));
    }, 150);

    return () => clearTimeout(timer);
  }, [value]);

  if (!value) return <span className={className}>{fallback}</span>;

  // Render using a combination of random zero-width spaces and span fragmentation 
  // to confuse simplistic DOM parsers, while keeping copy-paste functional for users.
  const renderFragmented = (text) => {
    if (!text) return null;
    return text.split('').map((char, index) => (
      <span key={index} className="inline-block">
        {char}
        {/* Inject zero-width space randomly to break text matches for bots */}
        {index % 2 === 0 && <span className="opacity-0 w-0 h-0 inline-block overflow-hidden absolute select-none">&#8203;</span>}
      </span>
    ));
  };

  return (
    <span className={`sensitive-data-wrapper ${className}`} data-protected="true">
      {displayedValue === null ? (
        <span className="animate-pulse bg-slate-200/50 rounded inline-block w-20 h-4"></span>
      ) : (
        <span 
          style={{ unicodeBidi: 'inherit' }}
        >
          {renderFragmented(displayedValue)}
        </span>
      )}
    </span>
  );
};
