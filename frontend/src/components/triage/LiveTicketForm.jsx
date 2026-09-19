import React from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Send, Loader2 } from 'lucide-react';

const SAMPLE_TICKETS = [
  {
    title: 'Database connection pool timeout',
    text: 'Production PostgreSQL database connection pool exhausted with timeout errors on primary replica. Queries failing across API gateways.',
    customerId: 'CUST-1001',
    urgency: 'Critical',
  },
  {
    title: 'Billing invoice refund dispute',
    text: 'Customer was charged twice for their monthly enterprise subscription renewal on invoice #INV-9824. Requesting immediate reversal.',
    customerId: 'CUST-1042',
    urgency: 'High',
  },
  {
    title: 'VPN handshake and MFA token rejection',
    text: 'Employees in regional branch unable to connect to internal corporate VPN. Okta MFA push notifications are not reaching mobile devices.',
    customerId: 'CUST-1002',
    urgency: 'High',
  },
  {
    title: 'Monitor flickering and cable replacement',
    text: 'Dual monitor setup on desk 4B is flickering green and losing display signal when bumped. Needs HDMI to DisplayPort replacement cable.',
    customerId: 'CUST-1005',
    urgency: 'Low',
  },
];

export const LiveTicketForm = ({
  title,
  setTitle,
  text,
  setText,
  customerId,
  setCustomerId,
  urgencyHint,
  setUrgencyHint,
  onSubmit,
  onReset,
  isLoading,
}) => {
  const loadSample = (sample) => {
    setTitle(sample.title);
    setText(sample.text);
    setCustomerId(sample.customerId);
    setUrgencyHint(sample.urgency);
  };

  return (
    <Card
      title="New ticket"
      action={
        isLoading && (
          <span className="flex items-center gap-1.5 text-xs text-slate-500">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Classifying
          </span>
        )
      }
    >
      <div className="space-y-5">
        {/* Examples */}
        <div>
          <span className="label">Examples</span>
          <div className="flex flex-wrap gap-2">
            {SAMPLE_TICKETS.map((sample) => (
              <button
                key={sample.title}
                type="button"
                onClick={() => loadSample(sample)}
                className="rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs text-slate-600 transition-colors hover:border-slate-300 hover:bg-white hover:text-slate-900"
              >
                {sample.title}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label htmlFor="ticket-title" className="label">
            Title
          </label>
          <input
            id="ticket-title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Short summary of the issue"
            className="input"
          />
        </div>

        <div>
          <div className="mb-1.5 flex items-center justify-between">
            <label htmlFor="ticket-text" className="text-xs font-medium text-slate-700">
              Description
            </label>
            <span className="font-mono text-[11px] tabular-nums text-slate-400">{text.length} chars</span>
          </div>
          <textarea
            id="ticket-text"
            rows={4}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Symptoms, error messages, affected systems…"
            className="input resize-y leading-relaxed"
          />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="ticket-customer" className="label">
              Customer
            </label>
            <select
              id="ticket-customer"
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
              className="input"
            >
              <option value="CUST-1001">CUST-1001 · Enterprise (VIP)</option>
              <option value="CUST-1042">CUST-1042 · Standard</option>
              <option value="CUST-1002">CUST-1002 · Enterprise (VIP)</option>
              <option value="CUST-1005">CUST-1005 · Standard</option>
              <option value="CUST-9999">CUST-9999 · New customer</option>
            </select>
          </div>

          <div>
            <label htmlFor="ticket-urgency" className="label">
              Urgency hint <span className="font-normal text-slate-400">(optional)</span>
            </label>
            <select
              id="ticket-urgency"
              value={urgencyHint}
              onChange={(e) => setUrgencyHint(e.target.value)}
              className="input"
            >
              <option value="">Auto-detect</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Critical">Critical</option>
            </select>
          </div>
        </div>

        <div className="flex items-center justify-between border-t border-slate-200 pt-4">
          <Button variant="ghost" size="sm" onClick={onReset}>
            Clear
          </Button>
          <Button onClick={onSubmit} isLoading={isLoading} disabled={!text.trim()} icon={Send}>
            Submit &amp; route
          </Button>
        </div>
      </div>
    </Card>
  );
};
