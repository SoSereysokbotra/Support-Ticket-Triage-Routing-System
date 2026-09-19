import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Alert } from '../common/Alert';
import { promoteModelVersion, rollbackModelVersion } from '../../services/api';
import { RotateCcw, ArrowUpCircle } from 'lucide-react';

const VersionTile = ({ name, alias, aliasTone, rows }) => (
  <div className="bg-paper p-4">
    <div className="flex items-center justify-between gap-2">
      <span className="font-mono text-sm font-medium text-ink">{name}</span>
      <Badge label={alias} variant={aliasTone} size="sm" />
    </div>
    <dl className="mt-3 divide-y divide-rule">
      {rows.map(([k, v]) => (
        <div key={k} className="flex items-center justify-between py-1.5 text-xs">
          <dt className="text-xs text-muted">{k}</dt>
          <dd className="font-mono text-ink">{v}</dd>
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
    <Card index="03" title="Model registry" description="MLflow aliases · changes hot-reload without downtime">
      <div className="space-y-5">
        {toast && <Alert variant={toast.variant}>{toast.message}</Alert>}

        <div className="grid grid-cols-1 gap-px border border-rule bg-rule sm:grid-cols-2">
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

        <div className="flex flex-col gap-3 border-t border-rule pt-4 sm:flex-row sm:items-end sm:justify-between">
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
