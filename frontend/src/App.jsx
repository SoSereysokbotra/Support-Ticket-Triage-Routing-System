import React, { useState } from 'react';
import { AppLayout } from './components/layout/AppLayout';
import { GlassPanel } from './components/common/GlassPanel';
import { Badge } from './components/common/Badge';
import { Sparkles, ArrowRight, Activity, Cpu, ShieldCheck } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState('triage');

  return (
    <AppLayout activeTab={activeTab} onTabChange={setActiveTab}>
      {/* Welcome Hero Banner */}
      <GlassPanel className="p-6 md:p-8 bg-gradient-to-r from-slate-900/90 via-slate-900/60 to-cyan-950/40 border-cyan-500/20">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge label="Production Serving Ready" variant="emerald" dot size="sm" />
              <Badge label="DistilBERT fine-tuned (Macro-F1 0.978)" variant="cyan" size="sm" />
            </div>
            <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white">
              Enterprise Support Ticket Triage Portal
            </h2>
            <p className="text-sm text-slate-300 max-w-2xl">
              AI-driven ticket routing system combining fine-tuned DistilBERT NLP inference with Feast customer metadata and zero-downtime MLflow rollbacks.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="px-4 py-3 rounded-xl bg-slate-950/80 border border-slate-800 text-center">
              <span className="block text-xs text-slate-400">Target SLA Floor</span>
              <span className="text-lg font-bold text-cyan-400 font-mono">2h VIP</span>
            </div>
            <div className="px-4 py-3 rounded-xl bg-slate-950/80 border border-slate-800 text-center">
              <span className="block text-xs text-slate-400">Training-Serving Skew</span>
              <span className="text-lg font-bold text-emerald-400 font-mono">0.000%</span>
            </div>
          </div>
        </div>
      </GlassPanel>

      {/* Placeholder Workspace Container - Ready for Phase F2/F3/F4 views */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <GlassPanel hoverEffect glowColor="cyan" className="p-6 space-y-4" onClick={() => setActiveTab('triage')}>
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-base text-white">Live AI Ticket Triage</h3>
            <p className="text-xs text-slate-400 mt-1">
              Submit tickets and view real-time category, urgency, and SLA escalation as you type.
            </p>
          </div>
          <div className="flex items-center text-xs font-semibold text-cyan-400 gap-1 pt-2">
            <span>Open Triage Workspace</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </div>
        </GlassPanel>

        <GlassPanel hoverEffect glowColor="purple" className="p-6 space-y-4" onClick={() => setActiveTab('queue')}>
          <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-base text-white">Agent Dispatch Queue</h3>
            <p className="text-xs text-slate-400 mt-1">
              Monitor incoming tickets, filter by department, and inspect model confidence.
            </p>
          </div>
          <div className="flex items-center text-xs font-semibold text-purple-400 gap-1 pt-2">
            <span>View Ticket Queue</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </div>
        </GlassPanel>

        <GlassPanel hoverEffect glowColor="rose" className="p-6 space-y-4" onClick={() => setActiveTab('mlops')}>
          <div className="w-10 h-10 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-base text-white">MLOps Command Center</h3>
            <p className="text-xs text-slate-400 mt-1">
              Evidently AI drift detection, MLflow model registry versioning, and auto-retraining.
            </p>
          </div>
          <div className="flex items-center text-xs font-semibold text-rose-400 gap-1 pt-2">
            <span>Launch MLOps Control</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </div>
        </GlassPanel>
      </div>
    </AppLayout>
  );
}

export default App;
