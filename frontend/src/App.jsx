import React, { useState } from 'react';
import { AppLayout } from './components/layout/AppLayout';
import { TriagePortal } from './views/TriagePortal';
import { AgentQueue } from './views/AgentQueue';
import { MLOpsControl } from './views/MLOpsControl';

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
        <MLOpsControl />
      )}
    </AppLayout>
  );
}

export default App;
