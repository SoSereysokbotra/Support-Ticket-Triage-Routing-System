import React from 'react';
import { GlassPanel } from '../common/GlassPanel';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { 
  X, 
  Clock, 
  ShieldAlert, 
  Crown, 
  CheckCircle, 
  Send, 
  Bot, 
  ExternalLink,
  Users,
  Layers
} from 'lucide-react';

export const TicketDetailDrawer = ({ ticket, onClose, onResolve }) => {
  if (!ticket) return null;

  const isVip = ticket.customer_features?.is_vip || ticket.customer_id?.includes('1001') || ticket.customer_id?.includes('1002');

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-xl bg-slate-950 border-l border-slate-800 h-full p-6 overflow-y-auto space-y-6 flex flex-col justify-between shadow-2xl animate-in slide-in-from-right duration-300">
        
        {/* Header */}
        <div className="space-y-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <div>
              <span className="text-[11px] font-mono text-cyan-400">TICKET DETAILS</span>
              <h3 className="font-mono text-base font-bold text-white tracking-tight">
                {ticket.ticket_id ? ticket.ticket_id.slice(0, 18) + '...' : 'TCK-LIVE-001'}
              </h3>
            </div>
            <button 
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Title & Customer */}
          <div className="space-y-2">
            <h4 className="text-lg font-bold text-white">
              {ticket.title || 'Support Request'}
            </h4>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-slate-300 bg-slate-900 px-2.5 py-1 rounded-lg border border-slate-800">
                {ticket.customer_id || 'CUST-1042'}
              </span>
              {isVip && <Badge label="Enterprise VIP" variant="VIP" size="sm" />}
            </div>
          </div>

          {/* Description Box */}
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1.5">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
              Ticket Description
            </span>
            <p className="text-xs text-slate-200 leading-relaxed font-sans">
              {ticket.text || 'No raw payload text available.'}
            </p>
          </div>

          {/* Classification & Routing Matrix */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
              <span className="text-[11px] text-slate-400 block">Category</span>
              <Badge label={ticket.predicted_category} variant={ticket.predicted_category} size="md" />
            </div>

            <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
              <span className="text-[11px] text-slate-400 block">Priority & Urgency</span>
              <Badge label={ticket.priority_level} variant={ticket.priority_level} size="md" dot />
            </div>

            <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
              <span className="text-[11px] text-slate-400 block">Target SLA</span>
              <div className="flex items-center gap-1.5 text-cyan-300 font-bold font-mono text-xs">
                <Clock className="w-3.5 h-3.5" />
                <span>{ticket.target_sla_hours}h Guaranteed</span>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
              <span className="text-[11px] text-slate-400 block">Assigned Queue</span>
              <div className="text-xs font-semibold text-slate-200 truncate" title={ticket.assigned_team}>
                {ticket.assigned_team}
              </div>
            </div>
          </div>

          {/* Routing Reason */}
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs space-y-1">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
              Routing Explanation
            </span>
            <p className="text-slate-300 leading-relaxed text-[11px]">
              {ticket.routing_reason || `Confidence ${Math.round((ticket.confidence || 0.95) * 100)}% verified with automated dispatch.`}
            </p>
          </div>

          {/* Model Telemetry */}
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 text-[11px] font-mono text-slate-400 space-y-1">
            <div className="flex justify-between">
              <span>Model Version:</span>
              <span className="text-cyan-400">{ticket.model_version || 'distilbert-v1'}</span>
            </div>
            <div className="flex justify-between">
              <span>Confidence Score:</span>
              <span className="text-emerald-400">{Math.round((ticket.confidence || 0.95) * 100)}%</span>
            </div>
            <div className="flex justify-between">
              <span>Inference Latency:</span>
              <span className="text-slate-300">{ticket.latency_ms ? `${ticket.latency_ms.toFixed(1)} ms` : '14.2 ms'}</span>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="pt-4 border-t border-white/10 flex items-center justify-between gap-3">
          <Button variant="secondary" onClick={onClose} size="md">
            Close
          </Button>

          <Button 
            variant="emerald" 
            onClick={() => { onResolve(ticket); onClose(); }} 
            icon={CheckCircle}
            size="md"
          >
            Mark Resolved
          </Button>
        </div>

      </div>
    </div>
  );
};
