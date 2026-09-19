import React from 'react';
import clsx from 'clsx';

/**
 * Labelled value tile. Used for the small "Priority / SLA / Team" readouts
 * inside cards and drawers. `size="lg"` sets the value in the display serif
 * for headline numbers.
 */
export const Field = ({ label, children, size = 'md', className = '' }) => (
  <div className={clsx('min-w-0 border border-rule bg-paper px-3 py-2.5', className)}>
    <div className="text-xs font-semibold text-muted">{label}</div>
    <div
      className={clsx(
        'mt-1 text-ink',
        size === 'lg' ? 'font-serif text-[28px] leading-none' : 'text-sm font-medium'
      )}
    >
      {children}
    </div>
  </div>
);
