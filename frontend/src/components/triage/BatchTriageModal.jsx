import React, { useState } from 'react';
import { GlassPanel } from '../common/GlassPanel';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { predictBatchTickets } from '../../services/api';
import { X, UploadCloud, Layers, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

const DEFAULT_BATCH_JSON = JSON.stringify([
  {
    "title": "Database slow query execution",
    "text": "PostgreSQL queries timing out on users table during peak hours.",
    "customer_id": "CUST-1001",
    "urgency_hint": "High"
  },
  {
    "title": "Need invoice copy for accountant",
    "text": "Please provide PDF receipt for subscription payment made on Jan 15th.",
    "customer_id": "CUST-1042",
    "urgency_hint": "Low"
  },
  {
    "title": "Office Wi-Fi connection dropping",
    "text": "Access points on the 3rd floor are resetting every 10 minutes.",
    "customer_id": "CUST-1005",
    "urgency_hint": "Medium"
  }
], null, 2);

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
        throw new Error("Input must be a non-empty JSON array of tickets");
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
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <GlassPanel className="w-full max-w-3xl bg-slate-900 border-slate-700 shadow-2xl p-6 space-y-5 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-cyan-400" />
            <h3 className="font-bold text-lg text-white">Batch Ticket Triage Inference</h3>
          </div>
          <button 
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-white/10"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* JSON Editor */}
        <div className="space-y-2 flex-1 overflow-y-auto">
          <label className="text-xs font-semibold text-slate-300">
            Paste Ticket Payloads (JSON Array):
          </label>
          <textarea
            rows={8}
            value={jsonInput}
            onChange={(e) => setJsonInput(e.target.value)}
            className="w-full p-3 rounded-xl bg-slate-950 font-mono text-xs text-cyan-300 border border-slate-800 outline-none focus:border-cyan-500"
          />

          {error && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Results Table */}
          {results && (
            <div className="space-y-2 mt-4">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Batch Inference Results ({results.total_processed} Tickets)
              </h4>
              <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-950/60 max-h-48 overflow-y-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-900 text-slate-400 border-b border-slate-800 font-mono">
                    <tr>
                      <th className="p-2.5">Category</th>
                      <th className="p-2.5">Confidence</th>
                      <th className="p-2.5">Priority</th>
                      <th className="p-2.5">SLA</th>
                      <th className="p-2.5">Assigned Team</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {results.predictions.map((p, idx) => (
                      <tr key={idx} className="hover:bg-white/5">
                        <td className="p-2.5">
                          <Badge label={p.predicted_category} variant={p.predicted_category} size="sm" />
                        </td>
                        <td className="p-2.5 font-mono text-cyan-400">
                          {Math.round(p.confidence * 100)}%
                        </td>
                        <td className="p-2.5">
                          <Badge label={p.priority_level} variant={p.priority_level} size="sm" />
                        </td>
                        <td className="p-2.5 font-mono text-slate-400">
                          {p.target_sla_hours}h
                        </td>
                        <td className="p-2.5 text-slate-300 font-medium">
                          {p.assigned_team}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-white/10 pt-4">
          <button
            onClick={() => setJsonInput(DEFAULT_BATCH_JSON)}
            className="text-xs text-slate-400 hover:text-slate-200"
          >
            Reset Default Payload
          </button>
          <div className="flex items-center gap-3">
            <Button variant="secondary" onClick={onClose} size="md">
              Close
            </Button>
            <Button 
              variant="primary" 
              onClick={handleRunBatch} 
              isLoading={isLoading}
              icon={UploadCloud}
              size="md"
            >
              Run Batch Inference
            </Button>
          </div>
        </div>
      </GlassPanel>
    </div>
  );
};
