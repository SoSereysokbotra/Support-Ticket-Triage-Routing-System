import React, { useState, useEffect } from 'react';
import { QueueStatsHeader } from '../components/queue/QueueStatsHeader';
import { QueueFilterBar } from '../components/queue/QueueFilterBar';
import { TicketQueueTable } from '../components/queue/TicketQueueTable';
import { TicketDetailDrawer } from '../components/queue/TicketDetailDrawer';
import { getPredictionLogs } from '../services/api';
import { PageHeader } from '../components/common/PageHeader';
import { Button } from '../components/common/Button';
import { Alert } from '../components/common/Alert';
import { RefreshCw } from 'lucide-react';

const INITIAL_FALLBACK_TICKETS = [
  {
    ticket_id: "8f7e2a1b-9c4d-4e8f-b3a1-123456789abc",
    title: "Database PostgreSQL pool exhaustion on primary replica",
    text: "Production PostgreSQL database connection pool exhausted with timeout errors on primary replica. Queries failing across API gateways.",
    customer_id: "CUST-1001",
    predicted_category: "Software",
    confidence: 0.9842,
    priority_level: "Critical",
    target_sla_hours: 2,
    assigned_team: "Software Engineering L2",
    auto_routed: true,
    routing_reason: "High-confidence Software prediction (98.4%) from VIP customer. Expedited to 2h SLA.",
    model_version: "distilbert-v1",
    customer_features: { customer_tier: "Enterprise", is_vip: true, past_ticket_count: 18, avg_resolution_time_hours: 1.8 }
  },
  {
    ticket_id: "3d2c1b0a-7f6e-5d4c-a2b1-987654321def",
    title: "Request for duplicate invoice receipt PDF",
    text: "Customer was charged twice for their monthly enterprise subscription renewal on invoice #INV-9824. Requesting immediate reversal.",
    customer_id: "CUST-1042",
    predicted_category: "Billing & Admin",
    confidence: 0.9610,
    priority_level: "High",
    target_sla_hours: 4,
    assigned_team: "Billing & Accounts Operations",
    auto_routed: true,
    routing_reason: "High-confidence Billing & Admin prediction (96.1%). Dispatched to Billing Operations.",
    model_version: "distilbert-v1",
    customer_features: { customer_tier: "Standard", is_vip: false, past_ticket_count: 3, avg_resolution_time_hours: 8.5 }
  },
  {
    ticket_id: "5a4b3c2d-1e0f-9a8b-7c6d-543216789fed",
    title: "Regional office VPN handshake timeout",
    text: "Employees in regional branch unable to connect to internal corporate VPN. Okta MFA push notifications are not reaching mobile devices.",
    customer_id: "CUST-1002",
    predicted_category: "Network",
    confidence: 0.9420,
    priority_level: "High",
    target_sla_hours: 2,
    assigned_team: "Network Operations Team",
    auto_routed: true,
    routing_reason: "High-confidence Network prediction (94.2%) from VIP customer. Expedited to 2h SLA.",
    model_version: "distilbert-v1",
    customer_features: { customer_tier: "Enterprise", is_vip: true, past_ticket_count: 24, avg_resolution_time_hours: 2.1 }
  },
  {
    ticket_id: "7b8a9c0d-2e1f-4a3b-6c5d-987123456abc",
    title: "Desk monitor replacement HDMI cable",
    text: "Dual monitor setup on desk 4B is flickering green and losing display signal when bumped. Needs HDMI to DisplayPort replacement cable.",
    customer_id: "CUST-1005",
    predicted_category: "Hardware",
    confidence: 0.8950,
    priority_level: "Low",
    target_sla_hours: 24,
    assigned_team: "IT Hardware Support Desk",
    auto_routed: true,
    routing_reason: "High-confidence Hardware prediction (89.5%). Dispatched to IT Support.",
    model_version: "distilbert-v1",
    customer_features: { customer_tier: "Standard", is_vip: false, past_ticket_count: 1, avg_resolution_time_hours: 14.0 }
  }
];

export const AgentQueue = ({ sessionTickets = [] }) => {
  const [tickets, setTickets] = useState([]);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [toastMsg, setToastMsg] = useState(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [teamFilter, setTeamFilter] = useState('ALL');
  const [vipOnly, setVipOnly] = useState(false);

  const fetchLogs = async () => {
    setIsLoading(true);
    try {
      const data = await getPredictionLogs(50);
      const rawLogs = Array.isArray(data) ? data : (data?.logs || []);

      if (rawLogs.length > 0) {
        // Map real SQLite WAL logs to table shape
        const teamMap = {
          'Hardware': 'Hardware Support Tier-2',
          'Software': 'Software Application Support',
          'Network': 'Network Operations Center (NOC)',
          'Access & Security': 'Identity & Access Management (IAM)',
          'Billing & Admin': 'Billing & Accounts Operations',
          'Other': 'General Customer Support',
        };

        const mappedLogs = rawLogs.map(log => {
          const isVip = log.is_vip === 1 || log.is_vip === true;
          const cat = log.predicted_category || 'Other';
          const conf = typeof log.confidence === 'number' ? log.confidence : 0.85;
          const assignedTeam = conf < 0.65 ? 'Tier-1 Human Triage Queue' : (teamMap[cat] || 'General Customer Support');
          const priority = isVip ? 'High' : (conf < 0.65 ? 'Medium' : 'Low');
          const slaHours = isVip ? 4 : (conf < 0.65 ? 8 : 24);

          return {
            ticket_id: log.ticket_id || `LOG-${log.id}`,
            title: log.text ? (log.text.slice(0, 60) + (log.text.length > 60 ? '...' : '')) : 'Support Ticket',
            text: log.text || '',
            customer_id: log.customer_id || 'CUST-GUEST',
            predicted_category: cat,
            confidence: conf,
            priority_level: priority,
            target_sla_hours: slaHours,
            assigned_team: assignedTeam,
            auto_routed: conf >= 0.65,
            routing_reason: conf < 0.65
              ? `Low confidence (${Math.round(conf * 100)}%). Assigned to human review.`
              : `Auto-routed to ${assignedTeam} based on ${cat} classification.` + (isVip ? ' [VIP Customer]' : ''),
            model_version: log.model_version || 'v1',
            latency_ms: log.latency_ms || 15.0,
            customer_features: {
              customer_tier: log.customer_tier || (isVip ? 'Enterprise' : 'Standard'),
              is_vip: isVip,
            },
          };
        });

        const existingIds = new Set(sessionTickets.map(t => t.ticket_id));
        const uniqueMapped = mappedLogs.filter(t => !existingIds.has(t.ticket_id));
        setTickets([...sessionTickets, ...uniqueMapped]);
      } else if (sessionTickets.length > 0) {
        setTickets(sessionTickets);
      } else {
        setTickets(INITIAL_FALLBACK_TICKETS);
      }
    } catch (err) {
      console.warn("Using fallback queue items:", err);
      setTickets([...sessionTickets, ...INITIAL_FALLBACK_TICKETS]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [sessionTickets]);

  const handleResolve = (ticketToResolve) => {
    setTickets(prev => prev.filter(t => t.ticket_id !== ticketToResolve.ticket_id));
    setToastMsg(`Ticket ${ticketToResolve.ticket_id?.slice(0, 8) || ''} marked as resolved.`);
    setTimeout(() => setToastMsg(null), 3500);
  };

  const handleResetFilters = () => {
    setSearchQuery('');
    setCategoryFilter('ALL');
    setPriorityFilter('ALL');
    setTeamFilter('ALL');
    setVipOnly(false);
  };

  // Filter Pipeline
  const filteredTickets = tickets.filter((t) => {
    // Search
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = (t.title || '').toLowerCase().includes(q);
      const matchText = (t.text || '').toLowerCase().includes(q);
      const matchCust = (t.customer_id || '').toLowerCase().includes(q);
      const matchId = (t.ticket_id || '').toLowerCase().includes(q);
      if (!matchTitle && !matchText && !matchCust && !matchId) return false;
    }
    // Category
    if (categoryFilter !== 'ALL' && t.predicted_category !== categoryFilter) return false;
    // Priority
    if (priorityFilter !== 'ALL' && t.priority_level !== priorityFilter) return false;
    // Team
    if (teamFilter !== 'ALL' && !(t.assigned_team || '').toLowerCase().includes(teamFilter.toLowerCase())) return false;
    // VIP
    if (vipOnly) {
      const isVip = t.customer_features?.is_vip || t.customer_id?.includes('1001') || t.customer_id?.includes('1002');
      if (!isVip) return false;
    }
    return true;
  });

  return (
    <>
      <PageHeader
        title="Queue"
        description="Routed tickets from live inference, with SLA targets and team assignments."
        actions={
          <Button variant="secondary" icon={RefreshCw} onClick={fetchLogs} isLoading={isLoading}>
            Refresh
          </Button>
        }
      />

      <QueueStatsHeader tickets={tickets} />

      {toastMsg && <Alert variant="success">{toastMsg}</Alert>}

      {/* Search & Filter Bar */}
      <QueueFilterBar
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        categoryFilter={categoryFilter}
        setCategoryFilter={setCategoryFilter}
        priorityFilter={priorityFilter}
        setPriorityFilter={setPriorityFilter}
        teamFilter={teamFilter}
        setTeamFilter={setTeamFilter}
        vipOnly={vipOnly}
        setVipOnly={setVipOnly}
        onReset={handleResetFilters}
      />

      {/* Tickets Data Table */}
      <TicketQueueTable
        tickets={filteredTickets}
        onSelectTicket={(t) => setSelectedTicket(t)}
        onResolveTicket={handleResolve}
      />

      {/* Detail Slide-Over Drawer */}
      <TicketDetailDrawer
        ticket={selectedTicket}
        onClose={() => setSelectedTicket(null)}
        onResolve={handleResolve}
      />
    </>
  );
};
