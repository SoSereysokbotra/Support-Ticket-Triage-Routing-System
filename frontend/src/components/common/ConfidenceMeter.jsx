import React from 'react';
import clsx from 'clsx';

export const ConfidenceMeter = ({ 
  value = 0, 
  threshold = 0.65,
  showLabel = true,
  size = 'md' 
}) => {
  const percentage = Math.round(value * 100);
  const isHigh = value >= threshold;

  const colorClasses = isHigh
    ? 'from-cyan-500 to-emerald-400 text-emerald-400'
    : 'from-amber-500 to-rose-500 text-amber-400';

  const heightClasses = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-3.5',
  };

  return (
    <div className="w-full space-y-1.5">
      {showLabel && (
        <div className="flex justify-between items-center text-xs">
          <span className="text-slate-400 font-medium">Confidence Score</span>
          <span className={clsx('font-mono font-bold', colorClasses.split(' ')[2])}>
            {percentage}%
          </span>
        </div>
      )}
      <div className={clsx('w-full bg-slate-800/80 rounded-full overflow-hidden p-0.5 border border-slate-700/50', heightClasses[size])}>
        <div
          className={clsx(
            'h-full rounded-full bg-gradient-to-r transition-all duration-500 shadow-sm',
            colorClasses.split(' ').slice(0, 2).join(' ')
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
