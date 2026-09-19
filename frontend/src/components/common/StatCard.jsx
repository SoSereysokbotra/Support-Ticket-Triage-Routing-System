import React from 'react';
import clsx from 'clsx';

/**
 * Wrap StatCards in a StatGrid so the tiles share hairline borders and read
 * as one instrument panel rather than four floating boxes.
 */
export const StatGrid = ({ children, className = '' }) => (
  <div className={clsx('grid grid-cols-2 gap-px border border-rule bg-rule lg:grid-cols-4', className)}>
    {children}
  </div>
);

export const StatCard = ({ label, value, hint, icon: Icon }) => (
  <div className="bg-surface p-5">
    <div className="flex items-center justify-between">
      <span className="eyebrow">{label}</span>
      {Icon && <Icon className="h-4 w-4 text-muted" strokeWidth={1.5} />}
    </div>
    <div className="mt-4 font-serif text-[40px] leading-none tracking-tight text-ink">{value}</div>
    {hint && <p className="mt-2.5 text-xs text-muted">{hint}</p>}
  </div>
);
