import React from 'react';
import { Badge } from '../common/Badge';
import { EmptyState } from '../common/EmptyState';
import { Star, Eye, Check, Inbox } from 'lucide-react';

const isVipTicket = (t) =>
  t.customer_features?.is_vip || t.customer_id?.includes('1001') || t.customer_id?.includes('1002');

export const TicketQueueTable = ({ tickets = [], onSelectTicket, onResolveTicket }) => {
  if (tickets.length === 0) {
    return (
      <EmptyState
        icon={Inbox}
        title="No tickets match these filters"
        description="Try a different search or reset the filters."
        className="bg-white"
      />
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs text-slate-500">
            <tr>
              <th className="px-4 py-2.5 font-medium">Ticket</th>
              <th className="px-4 py-2.5 font-medium">Customer</th>
              <th className="px-4 py-2.5 font-medium">Category</th>
              <th className="px-4 py-2.5 font-medium">Confidence</th>
              <th className="px-4 py-2.5 font-medium">Priority</th>
              <th className="px-4 py-2.5 font-medium">SLA</th>
              <th className="px-4 py-2.5 font-medium">Team</th>
              <th className="px-4 py-2.5 text-right font-medium">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {tickets.map((t, idx) => {
              const displayId = t.ticket_id ? t.ticket_id.slice(0, 8) : `TCK-${1000 + idx}`;

              return (
                <tr
                  key={t.ticket_id || idx}
                  className="group cursor-pointer transition-colors hover:bg-slate-50"
                  onClick={() => onSelectTicket(t)}
                >
                  <td className="max-w-[260px] px-4 py-3">
                    <div className="truncate font-medium text-slate-900">
                      {t.title || `${t.text?.slice(0, 45)}…`}
                    </div>
                    <div className="mt-0.5 font-mono text-[11px] text-slate-400">{displayId}</div>
                  </td>

                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1.5 font-mono text-xs text-slate-700">
                      {t.customer_id || 'CUST-1042'}
                      {isVipTicket(t) && <Star className="h-3.5 w-3.5 text-amber-500" aria-label="VIP" />}
                    </div>
                  </td>

                  <td className="px-4 py-3">
                    <Badge label={t.predicted_category} variant={t.predicted_category} size="sm" />
                  </td>

                  <td className="px-4 py-3 font-mono text-xs tabular-nums text-slate-700">
                    {Math.round((t.confidence || 0.95) * 100)}%
                  </td>

                  <td className="px-4 py-3">
                    <Badge label={t.priority_level} variant={t.priority_level} size="sm" dot />
                  </td>

                  <td className="px-4 py-3 font-mono text-xs tabular-nums text-slate-700">{t.target_sla_hours}h</td>

                  <td className="max-w-[180px] truncate px-4 py-3 text-xs text-slate-700" title={t.assigned_team}>
                    {t.assigned_team}
                  </td>

                  <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-1 opacity-60 transition-opacity group-hover:opacity-100">
                      <button
                        type="button"
                        onClick={() => onSelectTicket(t)}
                        className="rounded-md p-1.5 text-slate-500 hover:bg-slate-200 hover:text-slate-900"
                        title="View details"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => onResolveTicket(t)}
                        className="rounded-md p-1.5 text-slate-500 hover:bg-emerald-100 hover:text-emerald-700"
                        title="Mark resolved"
                      >
                        <Check className="h-4 w-4" />
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
