import React from 'react';
import clsx from 'clsx';

export const EmptyState = ({ icon: Icon, title, description, className = '' }) => (
  <div
    className={clsx(
      'flex flex-col items-center justify-center border border-dashed border-rule-strong px-6 py-10 text-center',
      className
    )}
  >
    {Icon && (
      <div className="mb-3 flex h-10 w-10 items-center justify-center border border-rule bg-surface text-muted">
        <Icon className="h-4 w-4" strokeWidth={1.5} />
      </div>
    )}
    <p className="text-sm font-medium text-ink">{title}</p>
    {description && <p className="mt-1 max-w-sm text-[13px] leading-relaxed text-muted">{description}</p>}
  </div>
);
