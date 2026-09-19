import React from 'react';
import clsx from 'clsx';

/**
 * Basic surface. Pass `title` (and optionally `description` / `action`)
 * to get a consistent header; omit them for a plain padded box.
 */
export const Card = ({
  title,
  description,
  action,
  children,
  className = '',
  bodyClassName = '',
  padded = true,
}) => {
  const hasHeader = title || action;

  return (
    <section className={clsx('rounded-lg border border-slate-200 bg-white shadow-sm', className)}>
      {hasHeader && (
        <header className="flex items-start justify-between gap-4 border-b border-slate-200 px-5 py-4">
          <div className="min-w-0">
            {title && <h3 className="text-sm font-semibold text-slate-900">{title}</h3>}
            {description && <p className="mt-0.5 text-xs text-slate-500">{description}</p>}
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </header>
      )}
      <div className={clsx(padded && 'p-5', bodyClassName)}>{children}</div>
    </section>
  );
};
