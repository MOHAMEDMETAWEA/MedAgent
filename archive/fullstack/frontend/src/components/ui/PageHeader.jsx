import React from 'react';

export function PageHeader({ 
  title, 
  subtitle, 
  badges, 
  children, 
  className = "", 
  titleClassName = "text-4xl lg:text-5xl",
  align = "left"
}) {
  return (
    <header className={`flex flex-col md:flex-row justify-between items-start md:items-end mb-6 gap-6 ${align === 'center' ? 'text-center lg:text-start items-center lg:items-end' : ''} ${className}`}>
      <div className={`max-w-2xl w-full ${align === 'center' ? 'flex flex-col items-center lg:items-start' : ''}`}>
        {badges && <div className="mb-4">{badges}</div>}
        <h1 className={`${titleClassName} font-extrabold tracking-tight text-on-surface mb-2`}>{title}</h1>
        {subtitle && <p className="text-on-surface-variant text-lg leading-relaxed font-medium">{subtitle}</p>}
      </div>
      {children && (
        <div className="flex gap-4 w-full md:w-auto shrink-0 flex-col sm:flex-row">
          {children}
        </div>
      )}
    </header>
  );
}
