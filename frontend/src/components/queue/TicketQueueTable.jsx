import React from 'react';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { 
  Clock, 
  Crown, 
  Eye, 
  CheckCircle, 
  Bot, 
  AlertTriangle 
} from 'lucide-react';

export const TicketQueueTable = ({ tickets = [], onSelectTicket, onResolveTicket }) => {
  if (tickets.length === 0) {
    return (
      <div className="p-12 text-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/40 space-y-3">
        <Bot className="w-8 h-8 text-slate-500 mx-auto" />
        <h4 className="text-sm font-semibold text-slate-300">No Tickets Match Active Filters</h4>
        <p className="text-xs text-slate-500 max-w-sm mx-auto">
          Try adjusting your search keywords or clearing filters to view all active dispatch tickets.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-800/80 overflow-hidden bg-slate-900/60 shadow-xl backdrop-blur-md">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 font-mono">
            <tr>
              <th className="py-3.5 px-4">Ticket</th>
              <th className="py-3.5 px-4">Customer</th>
              <th className="py-3.5 px-4">Category</th>
              <th className="py-3.5 px-4">Confidence</th>
              <th className="py-3.5 px-4">Priority</th>
              <th className="py-3.5 px-4">SLA Target</th>
              <th className="py-3.5 px-4">Assigned Team</th>
              <th className="py-3.5 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50 text-slate-300">
            {tickets.map((t, idx) => {
              const isVip = t.customer_features?.is_vip || t.customer_id?.includes('1001') || t.customer_id?.includes('1002');
              const displayId = t.ticket_id ? t.ticket_id.slice(0, 8) + '...' : `TCK-${1000 + idx}`;

              return (
                <tr 
                  key={t.ticket_id || idx}
                  className="hover:bg-slate-800/40 transition-colors group cursor-pointer"
                  onClick={() => onSelectTicket(t)}
                >
                  {/* Ticket Summary */}
                  <td className="py-3.5 px-4">
                    <div className="space-y-0.5">
                      <span className="font-mono text-[11px] text-cyan-400 font-semibold">{displayId}</span>
                      <p className="font-medium text-slate-100 max-w-[220px] truncate text-xs">
                        {t.title || t.text?.slice(0, 45) + '...'}
                      </p>
                    </div>
                  </td>

                  {/* Customer */}
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-1.5 font-mono">
                      <span className="text-slate-300">{t.customer_id || 'CUST-1042'}</span>
                      {isVip && <Crown className="w-3.5 h-3.5 text-yellow-400 shrink-0" title="VIP Account" />}
                    </div>
                  </td>

                  {/* Category */}
                  <td className="py-3.5 px-4">
                    <Badge label={t.predicted_category} variant={t.predicted_category} size="sm" />
                  </td>

                  {/* Confidence */}
                  <td className="py-3.5 px-4 font-mono">
                    <span className="text-emerald-400 font-bold">
                      {Math.round((t.confidence || 0.95) * 100)}%
                    </span>
                  </td>

                  {/* Priority */}
                  <td className="py-3.5 px-4">
                    <Badge label={t.priority_level} variant={t.priority_level} size="sm" dot />
                  </td>

                  {/* SLA */}
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-1 font-mono text-cyan-300 font-bold">
                      <Clock className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                      <span>{t.target_sla_hours}h</span>
                    </div>
                  </td>

                  {/* Team */}
                  <td className="py-3.5 px-4">
                    <span className="font-medium text-slate-200 truncate block max-w-[150px]">
                      {t.assigned_team}
                    </span>
                  </td>

                  {/* Actions */}
                  <td className="py-3.5 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => onSelectTicket(t)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-400 hover:bg-slate-800 transition-all"
                        title="View Details"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => onResolveTicket(t)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-emerald-400 hover:bg-slate-800 transition-all"
                        title="Mark Resolved"
                      >
                        <CheckCircle className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
