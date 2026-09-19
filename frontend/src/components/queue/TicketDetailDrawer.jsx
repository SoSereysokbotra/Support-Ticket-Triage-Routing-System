import React, { useEffect } from 'react';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { Field } from '../common/Field';
import { X, Check } from 'lucide-react';

const Row = ({ label, children }) => (
  <div className="flex items-center justify-between py-2 text-xs">
    <dt className="text-xs text-muted">{label}</dt>
    <dd className="font-mono text-ink">{children}</dd>
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
    <div className="fixed inset-0 z-50 flex justify-end bg-ink/60" onClick={onClose}>
      <aside
        className="flex h-full w-full max-w-lg flex-col border-l border-ink bg-surface"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ticket-drawer-title"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-start justify-between gap-4 border-b border-rule px-5 py-4">
          <div className="min-w-0">
            <div className="text-xs text-muted">
              {ticket.ticket_id || 'TCK-LIVE-001'}
            </div>
            <h3 id="ticket-drawer-title" className="mt-1.5 font-serif text-2xl leading-tight text-ink">
              {ticket.title || 'Support request'}
            </h3>
            <div className="mt-2.5 flex items-center gap-2">
              <span className="font-mono text-xs text-ink-2">{ticket.customer_id || 'CUST-1042'}</span>
              {isVip && <Badge label="VIP" variant="VIP" size="sm" />}
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex h-7 w-7 shrink-0 items-center justify-center border border-transparent text-muted transition-colors hover:border-ink hover:text-ink"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </header>

        <div className="flex-1 space-y-6 overflow-y-auto p-5">
          <section>
            <h4 className="eyebrow mb-2">Description</h4>
            <p className="text-sm leading-relaxed text-ink">{ticket.text || 'No description available.'}</p>
          </section>

          <div className="grid grid-cols-2 gap-px border border-rule bg-rule">
            <Field label="Category" className="border-0">
              <Badge label={ticket.predicted_category} variant={ticket.predicted_category} />
            </Field>
            <Field label="Priority" className="border-0">
              <Badge label={ticket.priority_level} variant={ticket.priority_level} />
            </Field>
            <Field label="Target SLA" className="border-0">
              <span className="font-mono tabular-nums">{ticket.target_sla_hours}h</span>
            </Field>
            <Field label="Assigned team" className="border-0">
              <span className="block truncate" title={ticket.assigned_team}>
                {ticket.assigned_team}
              </span>
            </Field>
          </div>

          <section>
            <h4 className="eyebrow mb-2">Routing reason</h4>
            <p className="text-sm leading-relaxed text-ink">
              {ticket.routing_reason || `Confidence ${confidencePct}%, dispatched automatically.`}
            </p>
          </section>

          <section>
            <h4 className="eyebrow mb-2">Inference</h4>
            <dl className="divide-y divide-rule border border-rule px-3">
              <Row label="Model">{ticket.model_version || 'distilbert-v1'}</Row>
              <Row label="Confidence">{confidencePct}%</Row>
              <Row label="Latency">{ticket.latency_ms ? `${ticket.latency_ms.toFixed(1)} ms` : '—'}</Row>
            </dl>
          </section>
        </div>

        <footer className="flex items-center justify-end gap-2 border-t border-rule px-5 py-4">
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
