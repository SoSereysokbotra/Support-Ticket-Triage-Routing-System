import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Play, CheckCircle2 } from 'lucide-react';

const STATUS_BADGE = {
  idle: { label: 'Idle', variant: 'neutral' },
  simulating: { label: 'Injecting drift', variant: 'amber' },
  training: { label: 'Pipeline running', variant: 'amber' },
  complete: { label: 'Complete', variant: 'green' },
};

export const RetrainTriggerCard = () => {
  const [status, setStatus] = useState('idle'); // idle | simulating | training | complete
  const [logs, setLogs] = useState([]);

  const handleSimulateAndTrigger = () => {
    setStatus('simulating');
    setLogs(['Injected 100 out-of-distribution samples into /api/v1/predict']);

    setTimeout(() => {
      setStatus('training');
      setLogs((prev) => [
        ...prev,
        'Drift detector crossed threshold (86.4% > 35%)',
        'Prefect flow started',
        'Task 1/5 · Ingest dataset',
        'Task 2/5 · Validate schema and class balance — passed',
        'Task 3/5 · Train candidate DistilBERT',
        'Task 4/5 · Quality gate — candidate 0.981 vs production 0.978',
        'Task 5/5 · Candidate registered in MLflow',
      ]);
    }, 2500);

    setTimeout(() => {
      setStatus('complete');
    }, 5500);
  };

  const badge = STATUS_BADGE[status];
  const isRunning = status === 'simulating' || status === 'training';

  return (
    <Card
      title="Automated retraining"
      description="Prefect pipeline with data validation and a Macro-F1 quality gate"
      action={<Badge label={badge.label} variant={badge.variant} dot={isRunning} />}
    >
      <div className="space-y-4">
        <p className="text-sm text-slate-600">
          Simulates out-of-distribution traffic, then runs the full retraining pipeline end to end.
        </p>

        <Button variant="secondary" icon={Play} onClick={handleSimulateAndTrigger} isLoading={isRunning}>
          {isRunning ? 'Running…' : 'Simulate drift and retrain'}
        </Button>

        {logs.length > 0 && (
          <ol className="max-h-56 space-y-1 overflow-y-auto rounded-md border border-slate-200 bg-slate-50 p-3 font-mono text-[11px] leading-relaxed text-slate-700">
            {logs.map((log, idx) => (
              <li key={idx} className="flex gap-2">
                <span className="shrink-0 text-slate-400">{new Date().toLocaleTimeString()}</span>
                <span>{log}</span>
              </li>
            ))}
            {status === 'complete' && (
              <li className="flex items-center gap-1.5 pt-1 font-medium text-emerald-700">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Retraining cycle finished
              </li>
            )}
          </ol>
        )}
      </div>
    </Card>
  );
};
