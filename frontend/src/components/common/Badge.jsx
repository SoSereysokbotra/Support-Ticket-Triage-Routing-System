import React from 'react';
import clsx from 'clsx';

const TONES = {
  neutral: 'bg-slate-100 text-slate-700 ring-slate-200',
  blue: 'bg-blue-50 text-blue-700 ring-blue-200',
  green: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  amber: 'bg-amber-50 text-amber-800 ring-amber-200',
  red: 'bg-red-50 text-red-700 ring-red-200',
  purple: 'bg-violet-50 text-violet-700 ring-violet-200',
};

// Domain values map onto the six tones above so callers can pass
// a category / priority string straight through as `variant`.
const ALIASES = {
  Hardware: 'amber',
  Software: 'blue',
  Network: 'purple',
  'Access & Security': 'red',
  'Billing & Admin': 'green',
  Low: 'neutral',
  Medium: 'blue',
  High: 'amber',
  Critical: 'red',
  VIP: 'amber',
};

const SIZES = {
  sm: 'px-1.5 py-0.5 text-[11px]',
  md: 'px-2 py-0.5 text-xs',
  lg: 'px-2.5 py-1 text-sm',
};

export const Badge = ({ label, variant = 'neutral', size = 'md', dot = false, className = '' }) => {
  const tone = TONES[variant] ? variant : ALIASES[variant] || 'neutral';

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 whitespace-nowrap rounded-md font-medium ring-1 ring-inset',
        TONES[tone],
        SIZES[size],
        className
      )}
    >
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
      {label}
    </span>
  );
};
