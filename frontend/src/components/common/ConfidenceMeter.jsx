import React from 'react';
import clsx from 'clsx';

const SEGMENTS = 25;

/**
 * Segmented meter, like a level indicator on a mixing desk. Filled segments
 * are ink when the value clears the auto-routing threshold and amber when it
 * does not; a signal-orange tick marks where the threshold sits.
 */
export const ConfidenceMeter = ({ value = 0, threshold = 0.65, showLabel = true, size = 'md' }) => {
  const percentage = Math.round(value * 100);
  const aboveThreshold = value >= threshold;
  const filled = Math.round(value * SEGMENTS);

  const heights = { sm: 'h-1.5', md: 'h-3', lg: 'h-4' };

  return (
    <div className="w-full">
      {showLabel && (
        <div className="mb-2 flex items-baseline justify-between">
          <span className="eyebrow">Confidence</span>
          <span className="font-mono text-sm font-medium tabular-nums text-ink">{percentage}%</span>
        </div>
      )}

      <div className="relative">
        <div
          className={clsx('flex w-full gap-[3px]', heights[size])}
          role="progressbar"
          aria-label="Confidence"
          aria-valuenow={percentage}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          {Array.from({ length: SEGMENTS }, (_, i) => (
            <span
              key={i}
              className={clsx(
                'h-full flex-1 transition-colors duration-300',
                i < filled ? (aboveThreshold ? 'bg-ink' : 'bg-warn') : 'bg-rule'
              )}
            />
          ))}
        </div>
        {/* Threshold tick */}
        <span
          className="absolute top-full h-1.5 w-px bg-accent"
          style={{ left: `${threshold * 100}%` }}
          aria-hidden="true"
        />
      </div>

      {showLabel && (
        <div className="mt-3 flex items-center justify-between text-xs">
          <span className="text-muted">0</span>
          <span className={aboveThreshold ? 'text-muted' : 'text-warn'}>
            {aboveThreshold
              ? `Auto-route threshold ${Math.round(threshold * 100)}%`
              : `Below ${Math.round(threshold * 100)}% threshold — human review`}
          </span>
          <span className="text-muted">100</span>
        </div>
      )}
    </div>
  );
};
