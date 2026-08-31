import React from 'react';
import clsx from 'clsx';

export const Badge = ({ 
  label, 
  variant = 'default', 
  size = 'md',
  dot = false,
  className = '' 
}) => {
  const variantStyles = {
    default: 'bg-slate-800/80 text-slate-300 border-slate-700/60',
    cyan: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30 shadow-sm',
    purple: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
    emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    amber: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    rose: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    // Domain Mappings
    Hardware: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    Software: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
    Network: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
    'Access & Security': 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    'Billing & Admin': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    // Urgency
    Low: 'bg-slate-500/10 text-slate-400 border-slate-500/30',
    Medium: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
    High: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    Critical: 'bg-rose-500/15 text-rose-400 border-rose-500/40 animate-pulse',
    VIP: 'bg-gradient-to-r from-amber-500/20 to-yellow-500/20 text-yellow-300 border-yellow-500/50 font-bold',
  };

  const sizeStyles = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs font-medium px-2.5 py-1',
    lg: 'text-sm font-semibold px-3.5 py-1.5',
  };

  return (
    <span 
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-full border backdrop-blur-md',
        variantStyles[variant] || variantStyles.default,
        sizeStyles[size],
        className
      )}
    >
      {dot && (
        <span className="w-1.5 h-1.5 rounded-full bg-current opacity-80" />
      )}
      {label}
    </span>
  );
};
