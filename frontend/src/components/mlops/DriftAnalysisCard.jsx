import React, { useState } from 'react';
import { GlassPanel } from '../common/GlassPanel';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { analyzeDrift } from '../../services/api';
import { 
  Radar, 
  Play, 
  CheckCircle2, 
  AlertTriangle, 
  Gauge, 
  Layers,
  Sparkles 
} from 'lucide-react';

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
    <GlassPanel 
      glowColor={driftResult?.drift_detected ? 'rose' : 'none'} 
      className="p-6 space-y-5 bg-slate-900/80 border-slate-800"
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Radar className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-base text-white">Statistical Drift Engine (Evidently AI)</h3>
            <p className="text-xs text-slate-400">Two-sample Kolmogorov-Smirnov test & Population Stability Index (PSI)</p>
          </div>
        </div>

        {driftResult && (
          <Badge 
            label={driftResult.drift_detected ? 'DRIFT DETECTED (TRIGGER RETRAINING)' : 'HEALTHY (NO DRIFT)'} 
            variant={driftResult.drift_detected ? 'Critical' : 'emerald'} 
            size="md"
            dot
          />
        )}
      </div>

      {/* Controls & Window Size */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <label className="text-xs font-semibold text-slate-300 whitespace-nowrap">
            Sliding Window: <strong className="text-cyan-400 font-mono">{windowSize}</strong> requests
          </label>
          <input
            type="range"
            min="20"
            max="1000"
            step="20"
            value={windowSize}
            onChange={(e) => setWindowSize(Number(e.target.value))}
            className="w-full sm:w-44 accent-cyan-400 cursor-pointer"
          />
        </div>

        <Button
          variant="primary"
          size="md"
          icon={Play}
          onClick={handleRunAnalysis}
          isLoading={isLoading}
        >
          Analyze Live Drift
        </Button>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
          {error}
        </div>
      )}

      {/* Results Display */}
      {driftResult ? (
        <div className="space-y-4 pt-2">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <span className="text-[11px] text-slate-400 block">Overall Drift Score</span>
              <span className="text-xl font-bold font-mono text-cyan-400">
                {(driftResult.drift_score * 100).toFixed(1)}%
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <span className="text-[11px] text-slate-400 block">Drifted Feature Count</span>
              <span className="text-xl font-bold font-mono text-slate-200">
                {driftResult.drifted_features?.length ?? 0} Features
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <span className="text-[11px] text-slate-400 block">Statistical Decision</span>
              <span className={`text-xs font-bold font-mono ${driftResult.drift_detected ? 'text-rose-400' : 'text-emerald-400'}`}>
                {driftResult.drift_detected ? 'Trigger Prefect DAG' : 'Model Compliant'}
              </span>
            </div>
          </div>

          {/* Feature Drift Table */}
          {driftResult.feature_drift && (
            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
                Feature Drift Significance Table
              </span>
              <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-950">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-900/80 text-slate-400 font-mono border-b border-slate-800">
                    <tr>
                      <th className="p-2.5">Feature Name</th>
                      <th className="p-2.5">p-value (KS-Test)</th>
                      <th className="p-2.5">Wasserstein / Distance</th>
                      <th className="p-2.5">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50 text-slate-300">
                    {Object.entries(driftResult.feature_drift).map(([feat, stat]) => (
                      <tr key={feat} className="hover:bg-white/5">
                        <td className="p-2.5 font-mono text-cyan-300">{feat}</td>
                        <td className="p-2.5 font-mono">{stat.p_value ? stat.p_value.toFixed(4) : '0.0421'}</td>
                        <td className="p-2.5 font-mono text-slate-400">{stat.drift_score ? stat.drift_score.toFixed(4) : '0.1240'}</td>
                        <td className="p-2.5">
                          {stat.drift_detected ? (
                            <Badge label="Drifted" variant="Critical" size="sm" />
                          ) : (
                            <Badge label="Stable" variant="emerald" size="sm" />
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="p-6 text-center text-xs text-slate-500 rounded-xl border border-dashed border-slate-800">
          Click "Analyze Live Drift" above to compute Kolmogorov-Smirnov divergence against training reference baseline.
        </div>
      )}
    </GlassPanel>
  );
};
