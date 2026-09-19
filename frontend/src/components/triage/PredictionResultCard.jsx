import React from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { ConfidenceMeter } from '../common/ConfidenceMeter';
import { EmptyState } from '../common/EmptyState';
import { Alert } from '../common/Alert';
import { Bot, Loader2 } from 'lucide-react';

const Field = ({ label, children }) => (
  <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2.5">
    <div className="text-[11px] text-slate-500">{label}</div>
    <div className="mt-1 text-sm font-medium text-slate-900">{children}</div>
  </div>
);

export const PredictionResultCard = ({ result, isLoading }) => {
  if (isLoading) {
    return (
      <Card title="Prediction">
        <EmptyState icon={Loader2} title="Classifying…" description="Running the model and looking up customer features." />
      </Card>
    );
  }

  if (!result) {
    return (
      <Card title="Prediction">
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
      title="Prediction"
      action={
        <span className="font-mono text-xs tabular-nums text-slate-500">
          {latency_ms ? `${latency_ms.toFixed(1)} ms` : '< 15 ms'}
        </span>
      }
    >
      <div className="space-y-5">
        <div>
          <div className="text-xs text-slate-500">Category</div>
          <div className="mt-1 flex items-center gap-3">
            <span className="text-2xl font-semibold tracking-tight text-slate-900">{predicted_category}</span>
            <Badge label={predicted_category} variant={predicted_category} />
          </div>
        </div>

        <ConfidenceMeter value={confidence} threshold={0.65} />

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <Field label="Priority">
            <Badge label={priority_level} variant={priority_level} dot />
          </Field>
          <Field label="Target SLA">
            <span className="font-mono tabular-nums">
              {target_sla_hours} {target_sla_hours === 1 ? 'hour' : 'hours'}
            </span>
          </Field>
          <Field label="Assigned team">
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

        <div className="border-t border-slate-200 pt-3 text-xs text-slate-500">
          Model <span className="font-mono text-slate-700">{model_version}</span>
        </div>
      </div>
    </Card>
  );
};
