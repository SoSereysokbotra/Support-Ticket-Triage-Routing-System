import React from 'react';
import clsx from 'clsx';

export const EmptyState = ({ icon: Icon, title, description, className = '' }) => (
  <div
    className={clsx(
      'flex flex-col items-center justify-center rounded-lg border border-dashed border-slate-300 px-6 py-10 text-center',
      className
    )}
  >
    {Icon && (
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-400">
        <Icon className="h-5 w-5" />
      </div>
    )}
    <p className="text-sm font-medium text-slate-700">{title}</p>
    {description && <p className="mt-1 max-w-sm text-xs text-slate-500">{description}</p>}
  </div>
);
