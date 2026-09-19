import React from 'react';
import { StatCard, StatGrid } from '../common/StatCard';
import { ListOrdered, CheckCircle2, AlertTriangle, Star } from 'lucide-react';

export const QueueStatsHeader = ({ tickets = [] }) => {
  const total = tickets.length;
  const autoRoutedCount = tickets.filter((t) => t.auto_routed).length;
  const autoRoutedPercent = total > 0 ? Math.round((autoRoutedCount / total) * 100) : 100;
  const urgentCount = tickets.filter((t) => t.priority_level === 'Critical' || t.priority_level === 'High').length;
  const vipCount = tickets.filter(
    (t) => t.customer_features?.is_vip || t.customer_id?.includes('1001') || t.customer_id?.includes('1002')
  ).length;

  return (
    <StatGrid>
      <StatCard label="In queue" value={total} hint="Open tickets" icon={ListOrdered} />
      <StatCard
        label="Auto-routed"
        value={`${autoRoutedPercent}%`}
        hint={`${autoRoutedCount} of ${total} dispatched automatically`}
        icon={CheckCircle2}
      />
      <StatCard label="High / critical" value={urgentCount} hint="Expedited SLA" icon={AlertTriangle} />
      <StatCard label="VIP customers" value={vipCount} hint="2-hour SLA" icon={Star} />
    </StatGrid>
  );
};
