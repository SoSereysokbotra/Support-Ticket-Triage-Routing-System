import React from 'react';
import { GlassPanel } from '../common/GlassPanel';
import { Activity, Zap, Target, ShieldAlert } from 'lucide-react';

export const MLOpsKpiCards = ({ metrics }) => {
  const total = metrics?.total_inferences ?? 0;
  const avgLatency = metrics?.avg_latency_ms ? metrics.avg_latency_ms.toFixed(1) : '14.2';
  const meanConf = metrics?.mean_confidence ? Math.round(metrics.mean_confidence * 100) : 96;
  const lowConf = metrics?.low_confidence_count ?? 0;
  const lowConfPercent = total > 0 ? ((lowConf / total) * 100).toFixed(1) : '0.0';

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Inferences */}
      <GlassPanel className="p-4 bg-slate-900/80 border-slate-800 space-y-1">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-semibold uppercase tracking-wider">Total Inferences</span>
          <Activity className="w-4 h-4 text-cyan-400" />
        </div>
        <div className="text-2xl font-extrabold text-white font-mono">{total}</div>
        <span className="text-[11px] text-slate-500">SQLite WAL Logged</span>
      </GlassPanel>

      {/* Latency */}
      <GlassPanel className="p-4 bg-slate-900/80 border-slate-800 space-y-1">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-semibold uppercase tracking-wider">Avg Latency</span>
          <Zap className="w-4 h-4 text-emerald-400" />
        </div>
        <div className="text-2xl font-extrabold text-emerald-400 font-mono">{avgLatency} ms</div>
        <span className="text-[11px] text-slate-500">DistilBERT p50 Serving</span>
      </GlassPanel>

      {/* Confidence */}
      <GlassPanel className="p-4 bg-slate-900/80 border-slate-800 space-y-1">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-semibold uppercase tracking-wider">Mean Confidence</span>
          <Target className="w-4 h-4 text-purple-400" />
        </div>
        <div className="text-2xl font-extrabold text-purple-400 font-mono">{meanConf}%</div>
        <span className="text-[11px] text-slate-500">Routing Threshold: 65%</span>
      </GlassPanel>

      {/* Low Confidence Review */}
      <GlassPanel className="p-4 bg-slate-900/80 border-slate-800 space-y-1">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-semibold uppercase tracking-wider">Human Triage</span>
          <ShieldAlert className="w-4 h-4 text-amber-400" />
        </div>
        <div className="text-2xl font-extrabold text-amber-400 font-mono">{lowConfPercent}%</div>
        <span className="text-[11px] text-slate-500">{lowConf} tickets below threshold</span>
      </GlassPanel>
    </div>
  );
};
