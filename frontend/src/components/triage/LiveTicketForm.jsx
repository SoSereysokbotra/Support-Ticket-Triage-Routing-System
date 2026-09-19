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
      index="01"
      title="New ticket"
      action={
        isLoading && (
          <span className="flex items-center gap-1.5 text-xs text-muted">
            <Loader2 className="h-3 w-3 animate-spin" />
            Classifying
          </span>
        )
      }
    >
      <div className="space-y-5">
        {/* Examples */}
        <div>
          <span className="label">Examples</span>
          <div className="flex flex-wrap gap-1.5">
            {SAMPLE_TICKETS.map((sample) => (
              <button
                key={sample.title}
                type="button"
                onClick={() => loadSample(sample)}
                className="border border-rule bg-paper px-2.5 py-1 text-[13px] text-ink-2 transition-colors hover:border-ink hover:text-ink"
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
          <div className="mb-1.5 flex items-baseline justify-between">
            <label htmlFor="ticket-text" className="eyebrow">
              Description
            </label>
            <span className="font-mono text-xs tabular-nums text-muted">{text.length} chars</span>
          </div>
          <textarea
            id="ticket-text"
            rows={4}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Symptoms, error messages, affected systems…"
            className="input resize-y"
          />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="ticket-customer" className="label">
              Customer ID
            </label>
            <input
              id="ticket-customer"
              type="text"
              list="customer-presets"
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
              placeholder="e.g. CUST-1001"
              className="input font-mono"
            />
            <datalist id="customer-presets">
              <option value="CUST-1001">CUST-1001 · Enterprise (VIP)</option>
              <option value="CUST-1042">CUST-1042 · Standard</option>
              <option value="CUST-1002">CUST-1002 · Enterprise (VIP)</option>
              <option value="CUST-1005">CUST-1005 · Standard</option>
              <option value="CUST-9999">CUST-9999 · New customer</option>
            </datalist>
          </div>

          <div>
            <label htmlFor="ticket-urgency" className="label">
              Urgency hint <span className="font-normal text-muted">(optional)</span>
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

        <div className="flex items-center justify-between border-t border-rule pt-4">
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
