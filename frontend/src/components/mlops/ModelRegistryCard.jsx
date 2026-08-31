import React, { useState } from 'react';
import { GlassPanel } from '../common/GlassPanel';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { promoteModelVersion, rollbackModelVersion } from '../../services/api';
import { GitBranch, RotateCcw, ArrowUpCircle, CheckCircle2, ShieldCheck, Cpu } from 'lucide-react';

export const ModelRegistryCard = ({ onActionSuccess }) => {
  const [targetVersion, setTargetVersion] = useState("1");
  const [isLoading, setIsLoading] = useState(false);
  const [toast, setToast] = useState(null);

  const handlePromote = async () => {
    setIsLoading(true);
    try {
      const data = await promoteModelVersion(targetVersion, 'production');
      setToast(`Version ${targetVersion} successfully promoted to @production.`);
      if (onActionSuccess) onActionSuccess();
    } catch (err) {
      setToast(`Promotion error: ${err.message}`);
    } finally {
      setIsLoading(false);
      setTimeout(() => setToast(null), 4000);
    }
  };

  const handleRollback = async () => {
    setIsLoading(true);
    try {
      const data = await rollbackModelVersion(targetVersion);
      setToast(`Hot-reload rollback completed to version ${targetVersion}.`);
      if (onActionSuccess) onActionSuccess();
    } catch (err) {
      setToast(`Rollback error: ${err.message}`);
    } finally {
      setIsLoading(false);
      setTimeout(() => setToast(null), 4000);
    }
  };

  return (
    <GlassPanel className="p-6 space-y-5 bg-slate-900/80 border-slate-800">
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <GitBranch className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-base text-white">MLflow Model Registry & Hot-Reload</h3>
            <p className="text-xs text-slate-400">Zero-downtime metadata aliases & atomic rollback</p>
          </div>
        </div>

        <Badge label="Zero-Downtime Hot-Reload" variant="purple" size="md" />
      </div>

      {toast && (
        <div className="p-3 rounded-xl bg-purple-500/15 border border-purple-500/30 text-purple-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-purple-400" />
          <span>{toast}</span>
        </div>
      )}

      {/* Model Versions Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-300">Active Production Model</span>
            <Badge label="@production" variant="emerald" size="sm" dot />
          </div>
          <div className="text-sm font-mono font-bold text-white">DistilBERT-Classifier-v1</div>
          <div className="text-[11px] text-slate-400 space-y-0.5 font-mono">
            <div>Macro-F1: <strong className="text-emerald-400">0.9787</strong></div>
            <div>Dataset SHA: <strong className="text-slate-300">a3f9...d812</strong></div>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-300">Candidate / Staging Model</span>
            <Badge label="@candidate" variant="amber" size="sm" dot />
          </div>
          <div className="text-sm font-mono font-bold text-white">DistilBERT-Classifier-v2</div>
          <div className="text-[11px] text-slate-400 space-y-0.5 font-mono">
            <div>Quality Gate: <strong className="text-cyan-400">PASSED (&gt; 0.75 floor)</strong></div>
            <div>Eval Status: <strong className="text-slate-300">Ready for Promotion</strong></div>
          </div>
        </div>
      </div>

      {/* Action Controls */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-3 border-t border-white/5">
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <label className="text-xs font-semibold text-slate-300">
            Target Version:
          </label>
          <select
            value={targetVersion}
            onChange={(e) => setTargetVersion(e.target.value)}
            className="px-3 py-1.5 rounded-xl glass-input text-xs text-white bg-slate-900 outline-none"
          >
            <option value="1">Version 1 (Production)</option>
            <option value="2">Version 2 (Candidate)</option>
            <option value="0">Version 0 (TF-IDF Baseline)</option>
          </select>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
          <Button
            variant="secondary"
            size="md"
            icon={RotateCcw}
            onClick={handleRollback}
            isLoading={isLoading}
          >
            Rollback to Version
          </Button>

          <Button
            variant="primary"
            size="md"
            icon={ArrowUpCircle}
            onClick={handlePromote}
            isLoading={isLoading}
          >
            Promote to @production
          </Button>
        </div>
      </div>
    </GlassPanel>
  );
};
