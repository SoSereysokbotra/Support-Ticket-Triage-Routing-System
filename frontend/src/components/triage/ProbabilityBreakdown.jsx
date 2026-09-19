import React from 'react';
import { Card } from '../common/Card';
import clsx from 'clsx';

export const ProbabilityBreakdown = ({ probabilities = {}, predictedCategory }) => {
  const entries = Object.entries(probabilities).sort((a, b) => b[1] - a[1]);

  if (entries.length === 0) {
    return null;
  }

  return (
    <Card title="Category probabilities" description={`${entries.length} classes`}>
      <ul className="space-y-3">
        {entries.map(([category, prob]) => {
          const percent = Math.round(prob * 100);
          const isTop = category === predictedCategory;

          return (
            <li key={category}>
              <div className="mb-1 flex items-center justify-between text-xs">
                <span className={clsx(isTop ? 'font-medium text-slate-900' : 'text-slate-600')}>{category}</span>
                <span
                  className={clsx(
                    'font-mono tabular-nums',
                    isTop ? 'font-medium text-slate-900' : 'text-slate-500'
                  )}
                >
                  {percent}%
                </span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className={clsx(
                    'h-full rounded-full transition-[width] duration-500',
                    isTop ? 'bg-blue-600' : 'bg-slate-300'
                  )}
                  style={{ width: `${Math.max(percent, 1)}%` }}
                />
              </div>
            </li>
          );
        })}
      </ul>
    </Card>
  );
};
