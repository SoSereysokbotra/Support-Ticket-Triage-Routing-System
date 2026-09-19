import React from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { Field } from '../common/Field';
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
      <Card index="04" title="Customer">
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
      index="04"
      title="Customer"
      description="Online features from Feast"
      action={
        <div className="flex items-center gap-1.5">
          {is_vip && <Badge label="VIP" variant="VIP" size="sm" />}
          <Badge label={customer_tier || 'Standard'} size="sm" />
        </div>
      }
    >
      <div className="space-y-4">
        <div className="font-mono text-sm font-medium text-ink">{customerId}</div>

        <dl className="grid grid-cols-2 gap-px border border-rule bg-rule">
          <Field label="Past tickets" size="lg" className="border-0">
            <span className="tabular-nums">{past_ticket_count ?? 0}</span>
          </Field>
          <Field label="Avg. resolution" size="lg" className="border-0">
            <span className="tabular-nums">
              {avg_resolution_time_hours ? `${avg_resolution_time_hours}h` : '—'}
            </span>
          </Field>
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
