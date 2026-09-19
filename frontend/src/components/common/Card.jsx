import React from 'react';
import clsx from 'clsx';

/**
 * Basic surface. Pass `title` (and optionally `index`, `description`,
 * `action`) to get a consistent header; omit them for a plain padded box.
 * `index` is a short ordinal like "01" printed before the title.
 */
export const Card = ({
  index,
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
    <section className={clsx('border border-rule bg-surface', className)}>
      {hasHeader && (
        <header className="flex items-start justify-between gap-4 border-b border-rule px-5 py-3.5">
          <div className="min-w-0">
            {title && (
              <h3 className="text-[15px] font-semibold text-ink">
                {index && <span className="mr-2 text-muted">{index}</span>}
                {title}
              </h3>
            )}
            {description && <p className="mt-1 text-[13px] text-muted">{description}</p>}
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </header>
      )}
      <div className={clsx(padded && 'p-5', bodyClassName)}>{children}</div>
    </section>
  );
};
