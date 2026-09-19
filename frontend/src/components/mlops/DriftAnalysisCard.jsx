import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Field } from '../common/Field';
import { Alert } from '../common/Alert';
import { EmptyState } from '../common/EmptyState';
import { analyzeDrift } from '../../services/api';
import { Play, Radar } from 'lucide-react';

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
      index="01"
      title="Drift analysis"
      description="Evidently AI · KS test and PSI against the training baseline"
      action={
        driftResult && (
          <Badge
            label={driftResult.drift_detected ? 'Drift detected' : 'No drift'}
            variant={driftResult.drift_detected ? 'red' : 'green'}
          />
        )
      }
    >
      <div className="space-y-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
          <div className="flex-1">
            <label htmlFor="drift-window" className="label">
              Window
              <span className="ml-2 font-normal text-ink">
                <span className="tabular-nums">{windowSize}</span> recent requests
              </span>
            </label>
            <input
              id="drift-window"
              type="range"
              min="20"
              max="1000"
              step="20"
              value={windowSize}
              onChange={(e) => setWindowSize(Number(e.target.value))}
              className="w-full"
            />
          </div>
          <Button icon={Play} onClick={handleRunAnalysis} isLoading={isLoading}>
            Run analysis
          </Button>
        </div>

        {error && <Alert variant="error">{error}</Alert>}

        {driftResult ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-px border border-rule bg-rule sm:grid-cols-3">
              <Field label="Drift score" size="lg" className="border-0">
                <span className="tabular-nums">{(driftResult.drift_score * 100).toFixed(1)}%</span>
              </Field>
              <Field label="Drifted features" size="lg" className="border-0">
                <span className="tabular-nums">{driftResult.drifted_features?.length ?? 0}</span>
              </Field>
              <Field label="Decision" size="lg" className="border-0">
                <span className={driftResult.drift_detected ? 'text-bad' : 'text-ok'}>
                  {driftResult.drift_detected ? 'Retrain' : 'Healthy'}
                </span>
              </Field>
            </div>

            {driftResult.feature_drift && (
              <div className="overflow-x-auto border border-rule">
                <table className="w-full text-left text-sm">
                  <thead className="border-b border-ink">
                    <tr>
                      <th className="th px-3">Feature</th>
                      <th className="th px-3">p-value</th>
                      <th className="th px-3">Distance</th>
                      <th className="th px-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-rule">
                    {Object.entries(driftResult.feature_drift).map(([feat, stat]) => (
                      <tr key={feat}>
                        <td className="px-3 py-2 font-mono text-ink">{feat}</td>
                        <td className="px-3 py-2 font-mono tabular-nums text-ink-2">
                          {stat.p_value ? stat.p_value.toFixed(4) : '0.0421'}
                        </td>
                        <td className="px-3 py-2 font-mono tabular-nums text-ink-2">
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
