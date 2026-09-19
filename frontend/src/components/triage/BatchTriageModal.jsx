import React, { useState } from 'react';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Alert } from '../common/Alert';
import { predictBatchTickets } from '../../services/api';
import { X, Play } from 'lucide-react';

const DEFAULT_BATCH_JSON = JSON.stringify(
  [
    {
      title: 'Database slow query execution',
      text: 'PostgreSQL queries timing out on users table during peak hours.',
      customer_id: 'CUST-1001',
      urgency_hint: 'High',
    },
    {
      title: 'Need invoice copy for accountant',
      text: 'Please provide PDF receipt for subscription payment made on Jan 15th.',
      customer_id: 'CUST-1042',
      urgency_hint: 'Low',
    },
    {
      title: 'Office Wi-Fi connection dropping',
      text: 'Access points on the 3rd floor are resetting every 10 minutes.',
      customer_id: 'CUST-1005',
      urgency_hint: 'Medium',
    },
  ],
  null,
  2
);

export const BatchTriageModal = ({ isOpen, onClose, onBatchSuccess }) => {
  const [jsonInput, setJsonInput] = useState(DEFAULT_BATCH_JSON);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);

  if (!isOpen) return null;

  const handleRunBatch = async () => {
    setError(null);
    setIsLoading(true);
    try {
      const parsed = JSON.parse(jsonInput);
      if (!Array.isArray(parsed) || parsed.length === 0) {
        throw new Error('Input must be a non-empty JSON array of tickets');
      }
      const data = await predictBatchTickets(parsed);
      setResults(data);
      if (onBatchSuccess) onBatchSuccess(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="batch-title"
      onClick={onClose}
    >
      <div
        className="flex max-h-[90vh] w-full max-w-3xl flex-col rounded-lg border border-slate-200 bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <div>
            <h3 id="batch-title" className="text-sm font-semibold text-slate-900">
              Batch triage
            </h3>
            <p className="mt-0.5 text-xs text-slate-500">Paste a JSON array of tickets to classify them together.</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </header>

        <div className="flex-1 space-y-4 overflow-y-auto p-5">
          <textarea
            rows={10}
            value={jsonInput}
            onChange={(e) => setJsonInput(e.target.value)}
            className="input font-mono text-xs leading-relaxed"
            spellCheck={false}
            aria-label="Tickets JSON"
          />

          {error && <Alert variant="error">{error}</Alert>}

          {results && (
            <div>
              <div className="mb-2 text-xs font-medium text-slate-700">
                {results.total_processed} tickets processed
              </div>
              <div className="max-h-56 overflow-auto rounded-md border border-slate-200">
                <table className="w-full text-left text-xs">
                  <thead className="sticky top-0 bg-slate-50 text-slate-500">
                    <tr>
                      <th className="px-3 py-2 font-medium">Category</th>
                      <th className="px-3 py-2 font-medium">Confidence</th>
                      <th className="px-3 py-2 font-medium">Priority</th>
                      <th className="px-3 py-2 font-medium">SLA</th>
                      <th className="px-3 py-2 font-medium">Team</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {results.predictions.map((p, idx) => (
                      <tr key={idx}>
                        <td className="px-3 py-2">
                          <Badge label={p.predicted_category} variant={p.predicted_category} size="sm" />
                        </td>
                        <td className="px-3 py-2 font-mono tabular-nums text-slate-700">
                          {Math.round(p.confidence * 100)}%
                        </td>
                        <td className="px-3 py-2">
                          <Badge label={p.priority_level} variant={p.priority_level} size="sm" />
                        </td>
                        <td className="px-3 py-2 font-mono tabular-nums text-slate-700">{p.target_sla_hours}h</td>
                        <td className="px-3 py-2 text-slate-700">{p.assigned_team}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        <footer className="flex items-center justify-between border-t border-slate-200 px-5 py-4">
          <Button variant="ghost" size="sm" onClick={() => setJsonInput(DEFAULT_BATCH_JSON)}>
            Reset example
          </Button>
          <div className="flex items-center gap-2">
            <Button variant="secondary" onClick={onClose}>
              Close
            </Button>
            <Button onClick={handleRunBatch} isLoading={isLoading} icon={Play}>
              Run batch
            </Button>
          </div>
        </footer>
      </div>
    </div>
  );
};
