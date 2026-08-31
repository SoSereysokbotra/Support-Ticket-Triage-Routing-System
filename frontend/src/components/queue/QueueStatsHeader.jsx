import React from 'react';
import { GlassPanel } from '../common/GlassPanel';
import { ListOrdered, CheckCircle2, AlertTriangle, Crown, Clock } from 'lucide-react';

export const QueueStatsHeader = ({ tickets = [] }) => {
  const total = tickets.length;
  const autoRoutedCount = tickets.filter(t => t.auto_routed).length;
  const autoRoutedPercent = total > 0 ? Math.round((autoRoutedCount / total) * 100) : 100;
  const criticalCount = tickets.filter(t => t.priority_level === 'Critical' || t.priority_level === 'High').length;
  const vipCount = tickets.filter(t => t.customer_features?.is_vip || t.customer_id?.includes('1001') || t.customer_id?.includes('1002')).length;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Total Tickets */}
      <GlassPanel className="p-4 bg-slate-900/70 border-slate-800 space-y-1">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-semibold uppercase tracking-wider">Queue Total</span>
          <ListOrdered className="w-4 h-4 text-cyan-400" />
        </div>
        <div className="text-2xl font-extrabold text-white font-mono">{total}</div>
        <span className="text-[11px] text-slate-500">Live Ingested Tickets</span>
      </GlassPanel>

      {/* Auto Routed % */}
      <GlassPanel className="p-4 bg-slate-900/70 border-slate-800 space-y-1">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-semibold uppercase tracking-wider">Auto-Routed</span>
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
        </div>
        <div className="text-2xl font-extrabold text-emerald-400 font-mono">{autoRoutedPercent}%</div>
        <span className="text-[11px] text-slate-500">{autoRoutedCount} automated dispatches</span>
      </GlassPanel>

      {/* High / Critical */}
      <GlassPanel className="p-4 bg-slate-900/70 border-slate-800 space-y-1">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-semibold uppercase tracking-wider">High / Critical</span>
          <AlertTriangle className="w-4 h-4 text-amber-400" />
        </div>
        <div className="text-2xl font-extrabold text-amber-400 font-mono">{criticalCount}</div>
        <span className="text-[11px] text-slate-500">Expedited SLA Queue</span>
      </GlassPanel>

      {/* VIP Accounts */}
      <GlassPanel className="p-4 bg-slate-900/70 border-slate-800 space-y-1">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-semibold uppercase tracking-wider">VIP Accounts</span>
          <Crown className="w-4 h-4 text-yellow-400" />
        </div>
        <div className="text-2xl font-extrabold text-yellow-400 font-mono">{vipCount}</div>
        <span className="text-[11px] text-slate-500">2h Guaranteed SLA</span>
      </GlassPanel>
    </div>
  );
};
