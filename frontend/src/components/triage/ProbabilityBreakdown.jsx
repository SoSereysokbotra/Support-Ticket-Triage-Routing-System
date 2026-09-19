import React from 'react';
import { Card } from '../common/Card';
import clsx from 'clsx';

export const ProbabilityBreakdown = ({ probabilities = {}, predictedCategory }) => {
  const entries = Object.entries(probabilities).sort((a, b) => b[1] - a[1]);

  if (entries.length === 0) {
    return null;
  }

  return (
    <Card index="03" title="Category probabilities" description={`${entries.length} classes, ranked`}>
      <ol className="space-y-3.5">
        {entries.map(([category, prob], i) => {
          const percent = Math.round(prob * 100);
          const isTop = category === predictedCategory;

          return (
            <li key={category}>
              <div className="mb-1.5 flex items-baseline justify-between gap-3">
                <div className="flex min-w-0 items-baseline gap-2.5">
                  <span className="font-mono text-xs tabular-nums text-muted">{String(i + 1).padStart(2, '0')}</span>
                  <span className={clsx('truncate text-sm', isTop ? 'font-medium text-ink' : 'text-ink-2')}>
                    {category}
                  </span>
                </div>
                <span
                  className={clsx(
                    'font-mono text-xs tabular-nums',
                    isTop ? 'font-medium text-ink' : 'text-muted'
                  )}
                >
                  {percent}%
                </span>
              </div>
              <div className="h-1 w-full bg-rule">
                <div
                  className={clsx('h-full transition-[width] duration-500', isTop ? 'bg-ink' : 'bg-rule-strong')}
                  style={{ width: `${Math.max(percent, 1)}%` }}
                />
              </div>
            </li>
          );
        })}
      </ol>
    </Card>
  );
};
