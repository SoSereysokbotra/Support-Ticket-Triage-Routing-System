import React from 'react';
import { Badge } from '../common/Badge';
import { EmptyState } from '../common/EmptyState';
import { Star, Eye, Check, Inbox } from 'lucide-react';

const isVipTicket = (t) =>
  t.customer_features?.is_vip || t.customer_id?.includes('1001') || t.customer_id?.includes('1002');

const RowAction = ({ title, onClick, children }) => (
  <button
    type="button"
    onClick={onClick}
    className="flex h-7 w-7 items-center justify-center border border-transparent text-muted transition-colors hover:border-ink hover:text-ink"
    title={title}
  >
    {children}
  </button>
);

export const TicketQueueTable = ({ tickets = [], onSelectTicket, onResolveTicket }) => {
  if (tickets.length === 0) {
    return (
      <EmptyState
        icon={Inbox}
        title="No tickets match these filters"
        description="Try a different search or reset the filters."
        className="bg-surface"
      />
    );
  }

  return (
    <div className="border border-rule bg-surface">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-ink">
            <tr>
              <th className="th w-10 text-right">#</th>
              <th className="th">Ticket</th>
              <th className="th">Customer</th>
              <th className="th">Category</th>
              <th className="th">Conf.</th>
              <th className="th">Priority</th>
              <th className="th">SLA</th>
              <th className="th">Team</th>
              <th className="th text-right">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-rule">
            {tickets.map((t, idx) => {
              const displayId = t.ticket_id ? t.ticket_id.slice(0, 8) : `TCK-${1000 + idx}`;

              return (
                <tr
                  key={t.ticket_id || idx}
                  className="group cursor-pointer transition-colors hover:bg-paper"
                  onClick={() => onSelectTicket(t)}
                >
                  <td className="px-4 py-3 text-right font-mono text-xs tabular-nums text-muted">
                    {String(idx + 1).padStart(2, '0')}
                  </td>

                  <td className="max-w-[280px] px-4 py-3">
                    <div className="truncate font-medium text-ink">
                      {t.title || `${t.text?.slice(0, 45)}…`}
                    </div>
                    <div className="mt-0.5 font-mono text-xs text-muted">{displayId}</div>
                  </td>

                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1.5 font-mono text-sm text-ink-2">
                      {t.customer_id || 'CUST-1042'}
                      {isVipTicket(t) && (
                        <Star className="h-3.5 w-3.5 fill-accent text-accent" strokeWidth={1.5} aria-label="VIP" />
                      )}
                    </div>
                  </td>

                  <td className="px-4 py-3">
                    <Badge label={t.predicted_category} variant={t.predicted_category} size="sm" />
                  </td>

                  <td className="px-4 py-3 font-mono text-sm tabular-nums text-ink-2">
                    {Math.round((t.confidence || 0.95) * 100)}%
                  </td>

                  <td className="px-4 py-3">
                    <Badge label={t.priority_level} variant={t.priority_level} size="sm" />
                  </td>

                  <td className="px-4 py-3 font-mono text-sm tabular-nums text-ink-2">{t.target_sla_hours}h</td>

                  <td className="max-w-[180px] truncate px-4 py-3 text-sm text-ink-2" title={t.assigned_team}>
                    {t.assigned_team}
                  </td>

                  <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-1 opacity-50 transition-opacity group-hover:opacity-100">
                      <RowAction title="View details" onClick={() => onSelectTicket(t)}>
                        <Eye className="h-4 w-4" strokeWidth={1.75} />
                      </RowAction>
                      <RowAction title="Mark resolved" onClick={() => onResolveTicket(t)}>
                        <Check className="h-4 w-4" strokeWidth={1.75} />
                      </RowAction>
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
