import React, { useEffect } from 'react';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { X, Check } from 'lucide-react';

const Field = ({ label, children }) => (
  <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2.5">
    <div className="text-[11px] text-slate-500">{label}</div>
    <div className="mt-1 text-sm font-medium text-slate-900">{children}</div>
  </div>
);

const Row = ({ label, children }) => (
  <div className="flex items-center justify-between py-1.5 text-xs">
    <dt className="text-slate-500">{label}</dt>
    <dd className="font-mono text-slate-800">{children}</dd>
  </div>
);

export const TicketDetailDrawer = ({ ticket, onClose, onResolve }) => {
  useEffect(() => {
    if (!ticket) return;
    const onKey = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [ticket, onClose]);

  if (!ticket) return null;

  const isVip =
    ticket.customer_features?.is_vip || ticket.customer_id?.includes('1001') || ticket.customer_id?.includes('1002');
  const confidencePct = Math.round((ticket.confidence || 0.95) * 100);

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40" onClick={onClose}>
      <aside
        className="flex h-full w-full max-w-lg flex-col border-l border-slate-200 bg-white shadow-xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ticket-drawer-title"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-start justify-between gap-4 border-b border-slate-200 px-5 py-4">
          <div className="min-w-0">
            <div className="font-mono text-[11px] text-slate-400">{ticket.ticket_id || 'TCK-LIVE-001'}</div>
            <h3 id="ticket-drawer-title" className="mt-0.5 text-base font-semibold text-slate-900">
              {ticket.title || 'Support request'}
            </h3>
            <div className="mt-2 flex items-center gap-2">
              <span className="font-mono text-xs text-slate-700">{ticket.customer_id || 'CUST-1042'}</span>
              {isVip && <Badge label="VIP" variant="VIP" size="sm" />}
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </header>

        <div className="flex-1 space-y-5 overflow-y-auto p-5">
          <section>
            <h4 className="mb-1.5 text-xs font-medium text-slate-500">Description</h4>
            <p className="text-sm leading-relaxed text-slate-800">{ticket.text || 'No description available.'}</p>
          </section>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Category">
              <Badge label={ticket.predicted_category} variant={ticket.predicted_category} />
            </Field>
            <Field label="Priority">
              <Badge label={ticket.priority_level} variant={ticket.priority_level} dot />
            </Field>
            <Field label="Target SLA">
              <span className="font-mono tabular-nums">{ticket.target_sla_hours}h</span>
            </Field>
            <Field label="Assigned team">
              <span className="block truncate" title={ticket.assigned_team}>
                {ticket.assigned_team}
              </span>
            </Field>
          </div>

          <section>
            <h4 className="mb-1.5 text-xs font-medium text-slate-500">Routing reason</h4>
            <p className="text-sm leading-relaxed text-slate-800">
              {ticket.routing_reason || `Confidence ${confidencePct}%, dispatched automatically.`}
            </p>
          </section>

          <section>
            <h4 className="mb-1 text-xs font-medium text-slate-500">Inference</h4>
            <dl className="divide-y divide-slate-100 rounded-md border border-slate-200 px-3">
              <Row label="Model">{ticket.model_version || 'distilbert-v1'}</Row>
              <Row label="Confidence">{confidencePct}%</Row>
              <Row label="Latency">{ticket.latency_ms ? `${ticket.latency_ms.toFixed(1)} ms` : '—'}</Row>
            </dl>
          </section>
        </div>

        <footer className="flex items-center justify-end gap-2 border-t border-slate-200 px-5 py-4">
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
          <Button
            icon={Check}
            onClick={() => {
              onResolve(ticket);
              onClose();
            }}
          >
            Mark resolved
          </Button>
        </footer>
      </aside>
    </div>
  );
};
