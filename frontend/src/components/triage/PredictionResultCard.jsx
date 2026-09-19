import React from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { Field } from '../common/Field';
import { ConfidenceMeter } from '../common/ConfidenceMeter';
import { EmptyState } from '../common/EmptyState';
import { Alert } from '../common/Alert';
import { Bot, Loader2 } from 'lucide-react';

export const PredictionResultCard = ({ result, isLoading }) => {
  if (isLoading) {
    return (
      <Card index="02" title="Prediction">
        <EmptyState icon={Loader2} title="Classifying…" description="Running the model and looking up customer features." />
      </Card>
    );
  }

  if (!result) {
    return (
      <Card index="02" title="Prediction">
        <EmptyState
          icon={Bot}
          title="No ticket yet"
          description="Start typing a description to get a category, priority, and team assignment."
        />
      </Card>
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
    model_version,
  } = result;

  return (
    <Card
      index="02"
      title="Prediction"
      action={
        <span className="text-xs text-muted">
          {latency_ms ? `${latency_ms.toFixed(1)} ms` : '< 15 ms'}
        </span>
      }
    >
      <div className="space-y-6">
        <div>
          <div className="eyebrow">Category</div>
          <div className="mt-2 flex flex-wrap items-baseline gap-x-4 gap-y-2">
            <span className="font-serif text-[40px] leading-none tracking-tight text-ink">{predicted_category}</span>
            <Badge label={predicted_category} variant={predicted_category} />
          </div>
        </div>

        <ConfidenceMeter value={confidence} threshold={0.65} />

        <div className="grid grid-cols-1 gap-px border border-rule bg-rule sm:grid-cols-3">
          <Field label="Priority" className="border-0">
            <Badge label={priority_level} variant={priority_level} />
          </Field>
          <Field label="Target SLA" className="border-0">
            <span className="font-mono tabular-nums">
              {target_sla_hours} {target_sla_hours === 1 ? 'hour' : 'hours'}
            </span>
          </Field>
          <Field label="Assigned team" className="border-0">
            <span className="block truncate" title={assigned_team}>
              {assigned_team}
            </span>
          </Field>
        </div>

        <Alert
          variant={auto_routed ? 'success' : 'warning'}
          title={auto_routed ? 'Auto-routed' : 'Sent for human review'}
        >
          {routing_reason}
        </Alert>

        <div className="flex items-center justify-between border-t border-rule pt-3 text-xs text-muted">
          <span>Model</span>
          <span className="text-ink">{model_version}</span>
        </div>
      </div>
    </Card>
  );
};
