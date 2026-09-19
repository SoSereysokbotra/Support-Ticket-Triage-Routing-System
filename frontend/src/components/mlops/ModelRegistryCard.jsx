import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Alert } from '../common/Alert';
import { promoteModelVersion, rollbackModelVersion } from '../../services/api';
import { RotateCcw, ArrowUpCircle } from 'lucide-react';

const VersionTile = ({ name, alias, aliasTone, rows }) => (
  <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
    <div className="flex items-center justify-between gap-2">
      <span className="font-mono text-sm font-medium text-slate-900">{name}</span>
      <Badge label={alias} variant={aliasTone} size="sm" dot />
    </div>
    <dl className="mt-3 space-y-1 text-xs">
      {rows.map(([k, v]) => (
        <div key={k} className="flex items-center justify-between">
          <dt className="text-slate-500">{k}</dt>
          <dd className="font-mono text-slate-800">{v}</dd>
        </div>
      ))}
    </dl>
  </div>
);

export const ModelRegistryCard = ({ onActionSuccess }) => {
  const [targetVersion, setTargetVersion] = useState('1');
  const [isLoading, setIsLoading] = useState(false);
  const [toast, setToast] = useState(null);

  const notify = (variant, message) => {
    setToast({ variant, message });
    setTimeout(() => setToast(null), 4000);
  };

  const handlePromote = async () => {
    setIsLoading(true);
    try {
      await promoteModelVersion(targetVersion, 'production');
      notify('success', `Version ${targetVersion} promoted to @production.`);
      if (onActionSuccess) onActionSuccess();
    } catch (err) {
      notify('error', `Promotion failed: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRollback = async () => {
    setIsLoading(true);
    try {
      await rollbackModelVersion(targetVersion);
      notify('success', `Rolled back to version ${targetVersion}.`);
      if (onActionSuccess) onActionSuccess();
    } catch (err) {
      notify('error', `Rollback failed: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card title="Model registry" description="MLflow aliases · changes hot-reload without downtime">
      <div className="space-y-5">
        {toast && <Alert variant={toast.variant}>{toast.message}</Alert>}

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <VersionTile
            name="distilbert-classifier v1"
            alias="production"
            aliasTone="green"
            rows={[
              ['Macro-F1', '0.9787'],
              ['Dataset', 'a3f9…d812'],
            ]}
          />
          <VersionTile
            name="distilbert-classifier v2"
            alias="candidate"
            aliasTone="amber"
            rows={[
              ['Quality gate', 'Passed (≥ 0.75)'],
              ['Status', 'Ready to promote'],
            ]}
          />
        </div>

        <div className="flex flex-col gap-3 border-t border-slate-200 pt-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="sm:w-56">
            <label htmlFor="registry-version" className="label">
              Target version
            </label>
            <select
              id="registry-version"
              value={targetVersion}
              onChange={(e) => setTargetVersion(e.target.value)}
              className="input"
            >
              <option value="1">v1 · production</option>
              <option value="2">v2 · candidate</option>
              <option value="0">v0 · TF-IDF baseline</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="secondary" icon={RotateCcw} onClick={handleRollback} isLoading={isLoading}>
              Roll back
            </Button>
            <Button icon={ArrowUpCircle} onClick={handlePromote} isLoading={isLoading}>
              Promote
            </Button>
          </div>
        </div>
      </div>
    </Card>
  );
};
