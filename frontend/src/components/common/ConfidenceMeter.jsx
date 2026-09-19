import React from 'react';
import clsx from 'clsx';

export const ConfidenceMeter = ({ value = 0, threshold = 0.65, showLabel = true, size = 'md' }) => {
  const percentage = Math.round(value * 100);
  const aboveThreshold = value >= threshold;

  const heights = { sm: 'h-1.5', md: 'h-2', lg: 'h-3' };

  return (
    <div className="w-full">
      {showLabel && (
        <div className="mb-1.5 flex items-center justify-between text-xs">
          <span className="text-slate-500">Confidence</span>
          <span className="font-mono font-medium tabular-nums text-slate-900">{percentage}%</span>
        </div>
      )}
      <div
        className={clsx('w-full overflow-hidden rounded-full bg-slate-100', heights[size])}
        role="progressbar"
        aria-valuenow={percentage}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className={clsx(
            'h-full rounded-full transition-[width] duration-500',
            aboveThreshold ? 'bg-blue-600' : 'bg-amber-500'
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && !aboveThreshold && (
        <p className="mt-1.5 text-xs text-amber-700">
          Below the {Math.round(threshold * 100)}% auto-routing threshold
        </p>
      )}
    </div>
  );
};
