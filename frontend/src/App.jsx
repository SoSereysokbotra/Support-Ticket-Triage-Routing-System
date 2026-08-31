import React, { useState } from 'react';
import { AppLayout } from './components/layout/AppLayout';
import { TriagePortal } from './views/TriagePortal';
import { AgentQueue } from './views/AgentQueue';
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

      {activeTab === 'queue' && (
        <AgentQueue sessionTickets={ticketHistory} />
      )}

      {activeTab === 'mlops' && (
        <GlassPanel className="p-8 text-center space-y-3 border-dashed border-slate-800">
          <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/30 mx-auto flex items-center justify-center text-rose-400">
            <Cpu className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-white capitalize">
            MLOps Command Center
          </h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Ready for Phase F4: Real-time Evidently AI drift analysis, MLflow zero-downtime rollbacks, and closed-loop retraining.
          </p>
        </GlassPanel>
      )}
    </AppLayout>
  );
}

export default App;
