import React from 'react';
import { GlassPanel } from '../common/GlassPanel';
import { Badge } from '../common/Badge';
import { ConfidenceMeter } from '../common/ConfidenceMeter';
import { 
  Bot, 
  Users, 
  Clock, 
  Zap, 
  AlertTriangle, 
  CheckCircle2, 
  Gauge,
  Sparkles 
} from 'lucide-react';

export const PredictionResultCard = ({ result, isLoading }) => {
  if (isLoading) {
    return (
      <GlassPanel className="p-8 text-center space-y-3 animate-pulse border-cyan-500/30">
        <div className="w-12 h-12 rounded-full bg-cyan-500/20 mx-auto flex items-center justify-center text-cyan-400">
          <Sparkles className="w-6 h-6 animate-spin" />
        </div>
        <h4 className="text-sm font-semibold text-white">Running DistilBERT Multi-Model Inference...</h4>
        <p className="text-xs text-slate-400">Evaluating text semantic tokens & querying Feast feature store...</p>
      </GlassPanel>
    );
  }

  if (!result) {
    return (
      <GlassPanel className="p-8 text-center space-y-3 bg-slate-900/40 border-dashed border-slate-800">
        <div className="w-12 h-12 rounded-2xl bg-slate-800/80 mx-auto flex items-center justify-center text-slate-500">
          <Bot className="w-6 h-6" />
        </div>
        <h4 className="text-sm font-semibold text-slate-300">Awaiting Ticket Input</h4>
        <p className="text-xs text-slate-500 max-w-sm mx-auto">
          Start typing a support ticket description to receive instant AI categorization, urgency scoring, and team assignment.
        </p>
      </GlassPanel>
    );
  }

  const {
    predicted_category,
    confidence,
    priority_level,
    target_sla_hours,
    assigned_team,
    auto_routed,
    routing_reason,
    latency_ms,
    model_version
  } = result;

  return (
    <GlassPanel 
      glowColor="cyan" 
      className="p-6 space-y-6 bg-gradient-to-b from-slate-900/95 via-slate-900/90 to-slate-950/95 border-cyan-500/30 shadow-glow-cyan"
    >
      {/* Top Banner: Category & Confidence */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <span className="text-[11px] font-bold text-cyan-400 tracking-wider uppercase">
            Predicted Category
          </span>
          <div className="flex items-center gap-3 mt-1">
            <h3 className="text-2xl font-extrabold text-white tracking-tight">
              {predicted_category}
            </h3>
            <Badge label={predicted_category} variant={predicted_category} size="md" />
          </div>
        </div>

        <div className="text-right">
          <span className="text-[11px] text-slate-400 block font-mono">Inference Latency</span>
          <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
            {latency_ms ? `${latency_ms.toFixed(1)} ms` : '< 15 ms'}
          </span>
        </div>
      </div>

      {/* Confidence Bar */}
      <ConfidenceMeter value={confidence} threshold={0.65} size="md" />

      {/* Decision Matrix Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Priority */}
        <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
          <span className="text-[11px] text-slate-400 block">Priority Level</span>
          <div className="flex items-center gap-1.5 mt-0.5">
            <Badge label={priority_level} variant={priority_level} size="md" dot />
          </div>
        </div>

        {/* SLA Hours */}
        <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
          <span className="text-[11px] text-slate-400 block">Target Resolution SLA</span>
          <div className="flex items-center gap-1.5 text-white font-bold text-sm mt-0.5">
            <Clock className="w-4 h-4 text-cyan-400" />
            <span className="font-mono text-cyan-300">{target_sla_hours} {target_sla_hours === 1 ? 'Hour' : 'Hours'}</span>
          </div>
        </div>

        {/* Dispatch Team */}
        <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
          <span className="text-[11px] text-slate-400 block">Assigned Support Queue</span>
          <div className="flex items-center gap-1.5 text-white font-bold text-sm mt-0.5 truncate">
            <Users className="w-4 h-4 text-purple-400 shrink-0" />
            <span className="truncate text-xs text-slate-200" title={assigned_team}>{assigned_team}</span>
          </div>
        </div>
      </div>

      {/* Routing Logic Invariant Reason */}
      <div className={`p-3.5 rounded-xl border text-xs flex items-start gap-2.5 ${auto_routed ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' : 'bg-amber-500/10 border-amber-500/30 text-amber-300'}`}>
        {auto_routed ? (
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
        ) : (
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        )}
        <div>
          <div className="font-semibold">
            {auto_routed ? 'Automated Dispatch Approved' : 'Escalated to Human Review'}
          </div>
          <div className="text-slate-300 mt-0.5 leading-relaxed">
            {routing_reason}
          </div>
        </div>
      </div>

      {/* Footer Model Lineage Tag */}
      <div className="flex items-center justify-between text-[11px] text-slate-500 border-t border-white/5 pt-3 font-mono">
        <span>Model Version: <strong className="text-slate-400">{model_version}</strong></span>
        <span>Feast Feature Store: <strong className="text-purple-400">Attached</strong></span>
      </div>
    </GlassPanel>
  );
};
