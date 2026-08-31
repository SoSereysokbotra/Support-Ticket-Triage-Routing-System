import React, { useState } from 'react';
import { GlassPanel } from '../common/GlassPanel';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { 
  Flame, 
  PlayCircle, 
  Workflow, 
  CheckCircle, 
  AlertOctagon, 
  ShieldCheck 
} from 'lucide-react';

export const RetrainTriggerCard = () => {
  const [status, setStatus] = useState('idle'); // idle | simulating | training | complete
  const [logs, setLogs] = useState([]);

  const handleSimulateAndTrigger = () => {
    setStatus('simulating');
    setLogs(['Injected 100 out-of-distribution synthetic traffic samples into /api/v1/predict...']);

    setTimeout(() => {
      setStatus('training');
      setLogs(prev => [
        ...prev,
        'Drift detector triggered threshold (86.4% drift > 35% limit)',
        'Closed-loop trigger invoked: Prefect 3 DAG launched',
        'Executing Task 1: Ingesting dataset...',
        'Executing Task 2: Validating schema & class balance (PASSED)...',
        'Executing Task 3: Training Candidate DistilBERT Model...',
        'Executing Task 4: Evaluating Quality Gate Floor (Candidate Macro-F1: 0.981 vs Prod: 0.978)...',
        'Executing Task 5: Candidate PASSED Quality Gate. Registered to MLflow!'
      ]);
    }, 2500);

    setTimeout(() => {
      setStatus('complete');
    }, 5500);
  };

  return (
    <GlassPanel className="p-6 space-y-5 bg-gradient-to-br from-slate-900/90 to-slate-950/90 border-slate-800">
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400">
            <Workflow className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-base text-white">Closed-Loop Automated Retraining (Prefect 3)</h3>
            <p className="text-xs text-slate-400">Self-healing pipeline with strict data validation & Macro-F1 quality gate</p>
          </div>
        </div>

        <Badge 
          label={status === 'complete' ? 'Retraining Complete' : status === 'training' ? 'DAG Running' : 'Ready'} 
          variant={status === 'complete' ? 'emerald' : status === 'training' ? 'amber' : 'default'} 
          size="md"
          dot={status === 'training'}
        />
      </div>

      <p className="text-xs text-slate-300 leading-relaxed">
        Click below to simulate out-of-distribution traffic drift in real-time, generate augmented training data, and execute the full automated Prefect 3 retraining DAG.
      </p>

      {/* Action Button */}
      <div>
        <Button
          variant="danger"
          size="md"
          icon={Flame}
          onClick={handleSimulateAndTrigger}
          isLoading={status === 'simulating' || status === 'training'}
          disabled={status === 'training'}
        >
          {status === 'training' ? 'Prefect Retraining DAG in Progress...' : 'Simulate Drift & Trigger Retraining Loop'}
        </Button>
      </div>

      {/* Live Log Feed */}
      {logs.length > 0 && (
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/90 space-y-1.5 font-mono text-[11px] max-h-48 overflow-y-auto">
          {logs.map((log, idx) => (
            <div key={idx} className="flex items-center gap-2 text-cyan-300">
              <span className="text-slate-500">[{new Date().toLocaleTimeString()}]</span>
              <span>{log}</span>
            </div>
          ))}
          {status === 'complete' && (
            <div className="flex items-center gap-2 text-emerald-400 font-bold pt-1">
              <CheckCircle className="w-3.5 h-3.5" />
              <span>Closed-loop retraining cycle successfully finalized.</span>
            </div>
          )}
        </div>
      )}
    </GlassPanel>
  );
};
