import React from 'react';
import { GlassPanel } from '../common/GlassPanel';
import { BarChart3 } from 'lucide-react';
import clsx from 'clsx';

export const ProbabilityBreakdown = ({ probabilities = {}, predictedCategory }) => {
  const entries = Object.entries(probabilities).sort((a, b) => b[1] - a[1]);

  if (entries.length === 0) {
    return (
      <GlassPanel className="p-4 text-center text-xs text-slate-500">
        Enter ticket details above to view DistilBERT category probability distribution.
      </GlassPanel>
    );
  }

  const categoryColorMap = {
    Hardware: 'from-amber-500 to-orange-500 text-amber-400',
    Software: 'from-blue-500 to-cyan-500 text-blue-400',
    Network: 'from-purple-500 to-indigo-500 text-purple-400',
    'Access & Security': 'from-rose-500 to-pink-500 text-rose-400',
    'Billing & Admin': 'from-emerald-500 to-teal-500 text-emerald-400',
  };

  return (
    <GlassPanel className="p-5 space-y-4 bg-slate-900/80 border-slate-800">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-cyan-400" />
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Softmax Class Distribution
          </h4>
        </div>
        <span className="text-[11px] font-mono text-slate-400">5 Categories</span>
      </div>

      <div className="space-y-3">
        {entries.map(([category, prob]) => {
          const percent = Math.round(prob * 100);
          const isTop = category === predictedCategory;
          const gradient = categoryColorMap[category] || 'from-cyan-500 to-blue-500 text-cyan-400';

          return (
            <div key={category} className="space-y-1">
              <div className="flex justify-between items-center text-xs">
                <span className={clsx('font-medium', isTop ? 'text-white font-semibold' : 'text-slate-400')}>
                  {category} {isTop && <span className="text-[10px] text-cyan-400 font-mono ml-1">(Winner)</span>}
                </span>
                <span className={clsx('font-mono font-bold', isTop ? gradient.split(' ')[2] : 'text-slate-400')}>
                  {percent}%
                </span>
              </div>
              <div className="w-full bg-slate-950/80 h-2 rounded-full overflow-hidden p-0.5 border border-slate-800">
                <div
                  className={clsx('h-full rounded-full bg-gradient-to-r transition-all duration-500', gradient.split(' ').slice(0, 2).join(' '))}
                  style={{ width: `${Math.max(percent, 2)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </GlassPanel>
  );
};
