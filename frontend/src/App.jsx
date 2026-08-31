import React, { useState } from 'react';
import { AppLayout } from './components/layout/AppLayout';
import { TriagePortal } from './views/TriagePortal';
import { GlassPanel } from './components/common/GlassPanel';
import { Badge } from './components/common/Badge';
import { Sparkles, ArrowRight, Activity, Cpu, ShieldCheck } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState('triage');
  const [ticketHistory, setTicketHistory] = useState([]);

  const handleTicketSubmitted = (newTicket) => {
    setTicketHistory(prev => [newTicket, ...prev]);
  };

  return (
    <AppLayout activeTab={activeTab} onTabChange={setActiveTab}>
      {activeTab === 'triage' && (
        <TriagePortal onTicketSubmitted={handleTicketSubmitted} />
      )}

      {activeTab !== 'triage' && (
        <GlassPanel className="p-8 text-center space-y-3 border-dashed border-slate-800">
          <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 mx-auto flex items-center justify-center text-cyan-400">
            {activeTab === 'queue' ? <Activity className="w-6 h-6" /> : <Cpu className="w-6 h-6" />}
          </div>
          <h3 className="text-lg font-bold text-white capitalize">
            {activeTab === 'queue' ? 'Agent Dispatch Queue' : 'MLOps Command Center'}
          </h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            {activeTab === 'queue' 
              ? 'Ready for Phase F3: Filter and inspect routed tickets, view VIP priority queues, and inspect model telemetry.' 
              : 'Ready for Phase F4: Real-time Evidently AI drift analysis, MLflow zero-downtime rollbacks, and closed-loop retraining.'}
          </p>
        </GlassPanel>
      )}
    </AppLayout>
  );
}

export default App;
