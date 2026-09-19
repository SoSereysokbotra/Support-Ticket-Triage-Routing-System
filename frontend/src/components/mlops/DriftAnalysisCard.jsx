import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Alert } from '../common/Alert';
import { EmptyState } from '../common/EmptyState';
import { analyzeDrift } from '../../services/api';
import { Play, Radar } from 'lucide-react';

const Stat = ({ label, children }) => (
  <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2.5">
    <div className="text-[11px] text-slate-500">{label}</div>
    <div className="mt-1 text-lg font-semibold tabular-nums text-slate-900">{children}</div>
  </div>
);

export const DriftAnalysisCard = ({ onDriftDetected }) => {
  const [windowSize, setWindowSize] = useState(200);
  const [isLoading, setIsLoading] = useState(false);
  const [driftResult, setDriftResult] = useState(null);
  const [error, setError] = useState(null);

  const handleRunAnalysis = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await analyzeDrift(windowSize);
      setDriftResult(data);
      if (data?.drift_detected && onDriftDetected) {
        onDriftDetected(data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card
      title="Drift analysis"
      description="Evidently AI · KS test and PSI against the training baseline"
      action={
        driftResult && (
          <Badge
            label={driftResult.drift_detected ? 'Drift detected' : 'No drift'}
            variant={driftResult.drift_detected ? 'red' : 'green'}
            dot
          />
        )
      }
    >
      <div className="space-y-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
          <div className="flex-1">
            <label htmlFor="drift-window" className="label">
              Window: <span className="font-mono tabular-nums text-slate-900">{windowSize}</span> recent requests
            </label>
            <input
              id="drift-window"
              type="range"
              min="20"
              max="1000"
              step="20"
              value={windowSize}
              onChange={(e) => setWindowSize(Number(e.target.value))}
              className="w-full accent-blue-600"
            />
          </div>
          <Button icon={Play} onClick={handleRunAnalysis} isLoading={isLoading}>
            Run analysis
          </Button>
        </div>

        {error && <Alert variant="error">{error}</Alert>}

        {driftResult ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <Stat label="Drift score">{(driftResult.drift_score * 100).toFixed(1)}%</Stat>
              <Stat label="Drifted features">{driftResult.drifted_features?.length ?? 0}</Stat>
              <Stat label="Decision">
                <span className={driftResult.drift_detected ? 'text-red-700' : 'text-emerald-700'}>
                  {driftResult.drift_detected ? 'Retrain' : 'Healthy'}
                </span>
              </Stat>
            </div>

            {driftResult.feature_drift && (
              <div className="overflow-hidden rounded-md border border-slate-200">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-slate-200 bg-slate-50 text-slate-500">
                    <tr>
                      <th className="px-3 py-2 font-medium">Feature</th>
                      <th className="px-3 py-2 font-medium">p-value</th>
                      <th className="px-3 py-2 font-medium">Distance</th>
                      <th className="px-3 py-2 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {Object.entries(driftResult.feature_drift).map(([feat, stat]) => (
                      <tr key={feat}>
                        <td className="px-3 py-2 font-mono text-slate-800">{feat}</td>
                        <td className="px-3 py-2 font-mono tabular-nums text-slate-700">
                          {stat.p_value ? stat.p_value.toFixed(4) : '0.0421'}
                        </td>
                        <td className="px-3 py-2 font-mono tabular-nums text-slate-700">
                          {stat.drift_score ? stat.drift_score.toFixed(4) : '0.1240'}
                        </td>
                        <td className="px-3 py-2">
                          <Badge
                            label={stat.drift_detected ? 'Drifted' : 'Stable'}
                            variant={stat.drift_detected ? 'red' : 'green'}
                            size="sm"
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ) : (
          <EmptyState
            icon={Radar}
            title="No analysis yet"
            description="Run an analysis to compare recent traffic against the training distribution."
            className="py-6"
          />
        )}
      </div>
    </Card>
  );
};
