import React from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { Alert } from '../common/Alert';
import { EmptyState } from '../common/EmptyState';
import { User } from 'lucide-react';

export const CustomerProfileCard = ({
  customerId,
  features,
  targetSlaHours,
  priorityLevel,
  routingReason,
}) => {
  if (!features) {
    return (
      <Card title="Customer">
        <EmptyState
          icon={User}
          title="No customer features"
          description="Select a customer to load their profile from the feature store."
          className="py-6"
        />
      </Card>
    );
  }

  const { customer_tier, is_vip, past_ticket_count, avg_resolution_time_hours } = features;

  return (
    <Card
      title="Customer"
      description="Online features from Feast"
      action={
        <div className="flex items-center gap-2">
          {is_vip && <Badge label="VIP" variant="VIP" size="sm" />}
          <Badge label={customer_tier || 'Standard'} size="sm" />
        </div>
      }
    >
      <div className="space-y-4">
        <div className="font-mono text-sm font-medium text-slate-900">{customerId}</div>

        <dl className="grid grid-cols-2 gap-3">
          <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2.5">
            <dt className="text-[11px] text-slate-500">Past tickets</dt>
            <dd className="mt-1 font-mono text-sm font-medium tabular-nums text-slate-900">
              {past_ticket_count ?? 0}
            </dd>
          </div>
          <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2.5">
            <dt className="text-[11px] text-slate-500">Avg. resolution</dt>
            <dd className="mt-1 font-mono text-sm font-medium tabular-nums text-slate-900">
              {avg_resolution_time_hours ? `${avg_resolution_time_hours}h` : '—'}
            </dd>
          </div>
        </dl>

        {is_vip && (
          <Alert variant="warning">
            {routingReason ||
              `VIP escalation active: priority ${priorityLevel ? `set to ${priorityLevel}` : 'escalated'} with target SLA ${
                targetSlaHours ? `of ${targetSlaHours}h` : 'expedited'
              }.`}
          </Alert>
        )}
      </div>
    </Card>
  );
};

