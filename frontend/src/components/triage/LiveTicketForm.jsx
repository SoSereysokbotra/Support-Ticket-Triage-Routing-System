import React from 'react';
import { GlassPanel } from '../common/GlassPanel';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { 
  Sparkles, 
  Send, 
  RotateCcw, 
  SlidersHorizontal,
  BookmarkPlus 
} from 'lucide-react';

const SAMPLE_TICKETS = [
  {
    title: "Database connection pool timeout",
    text: "Production PostgreSQL database connection pool exhausted with timeout errors on primary replica. Queries failing across API gateways.",
    customerId: "CUST-1001",
    urgency: "Critical"
  },
  {
    title: "Billing invoice refund dispute",
    text: "Customer was charged twice for their monthly enterprise subscription renewal on invoice #INV-9824. Requesting immediate reversal.",
    customerId: "CUST-1042",
    urgency: "High"
  },
  {
    title: "VPN handshake and MFA token rejection",
    text: "Employees in regional branch unable to connect to internal corporate VPN. Okta MFA push notifications are not reaching mobile devices.",
    customerId: "CUST-1002",
    urgency: "High"
  },
  {
    title: "Monitor flickering and cable replacement",
    text: "Dual monitor setup on desk 4B is flickering green and losing display signal when bumped. Needs HDMI to DisplayPort replacement cable.",
    customerId: "CUST-1005",
    urgency: "Low"
  }
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
  isLoading
}) => {
  return (
    <GlassPanel className="p-6 space-y-5 bg-surface-card/60 border-slate-800">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-cyan-400" />
          <h3 className="font-bold text-base text-white">Create Support Ticket</h3>
        </div>
        <span className="text-xs text-cyan-400/80 bg-cyan-500/10 px-2.5 py-1 rounded-full border border-cyan-500/20 font-medium">
          ⚡ Live AI Inference Enabled
        </span>
      </div>

      {/* Preset Buttons */}
      <div className="space-y-1.5">
        <span className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
          <BookmarkPlus className="w-3.5 h-3.5 text-slate-400" />
          Load Real-World Scenarios:
        </span>
        <div className="flex flex-wrap gap-2">
          {SAMPLE_TICKETS.map((sample, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setTitle(sample.title);
                setText(sample.text);
                setCustomerId(sample.customerId);
                setUrgencyHint(sample.urgency);
              }}
              className="text-xs px-2.5 py-1.5 rounded-lg bg-slate-900/90 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/40 text-slate-300 hover:text-cyan-300 transition-all text-left"
            >
              {sample.title}
            </button>
          ))}
        </div>
      </div>

      {/* Inputs */}
      <div className="space-y-4">
        {/* Title */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-300">
            Ticket Title / Summary
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Database connection pool timeout error"
            className="w-full px-4 py-2.5 rounded-xl glass-input text-sm text-white placeholder-slate-500 outline-none"
          />
        </div>

        {/* Text Description */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-300 flex justify-between">
            <span>Issue Description</span>
            <span className="text-slate-500 font-mono text-[11px]">{text.length} characters</span>
          </label>
          <textarea
            rows={4}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Describe the issue in detail (e.g. symptoms, error codes, affected systems)..."
            className="w-full px-4 py-2.5 rounded-xl glass-input text-sm text-white placeholder-slate-500 outline-none resize-y leading-relaxed"
          />
        </div>

        {/* Customer ID & Urgency Hint */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">
              Customer ID (Feast Store lookup)
            </label>
            <select
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
              className="w-full px-3.5 py-2 rounded-xl glass-input text-sm text-slate-200 outline-none bg-slate-900"
            >
              <option value="CUST-1001">CUST-1001 (VIP • Enterprise Tier)</option>
              <option value="CUST-1042">CUST-1042 (Standard Tier)</option>
              <option value="CUST-1002">CUST-1002 (VIP • Enterprise Tier)</option>
              <option value="CUST-1005">CUST-1005 (Standard Tier)</option>
              <option value="CUST-9999">CUST-9999 (New Customer)</option>
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">
              Urgency Hint (Optional)
            </label>
            <select
              value={urgencyHint}
              onChange={(e) => setUrgencyHint(e.target.value)}
              className="w-full px-3.5 py-2 rounded-xl glass-input text-sm text-slate-200 outline-none bg-slate-900"
            >
              <option value="">AI Auto-Detect Urgency</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Critical">Critical</option>
            </select>
          </div>
        </div>
      </div>

      {/* Buttons */}
      <div className="flex items-center justify-between pt-3 border-t border-white/5">
        <button
          type="button"
          onClick={onReset}
          className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1.5 px-3 py-2 rounded-lg hover:bg-white/5 transition-all"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Clear Form</span>
        </button>

        <Button
          onClick={onSubmit}
          isLoading={isLoading}
          disabled={!text.trim()}
          icon={Send}
          variant="primary"
          size="md"
        >
          Submit & Route Ticket
        </Button>
      </div>
    </GlassPanel>
  );
};
