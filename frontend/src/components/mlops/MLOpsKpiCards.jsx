import React from 'react';
import { StatCard, StatGrid } from '../common/StatCard';
import { Activity, Zap, Target, UserCheck } from 'lucide-react';

export const MLOpsKpiCards = ({ metrics }) => {
  const total = metrics?.total_inferences ?? 0;
  const avgLatency = metrics?.avg_latency_ms ? metrics.avg_latency_ms.toFixed(1) : '—';
  const meanConf = metrics?.mean_confidence ? Math.round(metrics.mean_confidence * 100) : '—';
  const lowConf = metrics?.low_confidence_count ?? 0;
  const lowConfPercent = total > 0 ? ((lowConf / total) * 100).toFixed(1) : '0.0';

  return (
    <StatGrid>
      <StatCard label="Inferences" value={total} hint="Logged predictions" icon={Activity} />
      <StatCard label="Avg. latency" value={`${avgLatency} ms`} hint="Per prediction" icon={Zap} />
      <StatCard label="Mean confidence" value={`${meanConf}%`} hint="Routing threshold 65%" icon={Target} />
      <StatCard
        label="Human review"
        value={`${lowConfPercent}%`}
        hint={`${lowConf} below threshold`}
        icon={UserCheck}
      />
    </StatGrid>
  );
};
