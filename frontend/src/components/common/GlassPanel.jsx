import React from 'react';
import clsx from 'clsx';

export const GlassPanel = ({ 
  children, 
  className = '', 
  hoverEffect = false,
  glowColor = 'none',
  padding = 'p-6',
  ...props 
}) => {
  const glowStyles = {
    none: '',
    cyan: 'hover:border-cyan-500/40 hover:shadow-glow-cyan',
    purple: 'hover:border-purple-500/40 hover:shadow-glow-purple',
    emerald: 'hover:border-emerald-500/40 hover:shadow-glow-cyan',
    rose: 'hover:border-rose-500/40 hover:shadow-glow-rose',
  };

  return (
    <div 
      className={clsx(
        'glass-card rounded-2xl transition-all duration-300 relative overflow-hidden',
        padding,
        hoverEffect && 'glass-card-hover cursor-pointer',
        glowStyles[glowColor],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};
