import React from 'react';

export const PageHeader = ({ title, description, actions }) => (
  <div className="flex flex-col gap-4 border-b border-ink pb-5 sm:flex-row sm:items-end sm:justify-between">
    <div>
      <h2 className="font-serif text-[40px] leading-none tracking-tight text-ink">{title}</h2>
      {description && <p className="mt-2.5 max-w-xl text-sm text-muted">{description}</p>}
    </div>
    {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
  </div>
);
