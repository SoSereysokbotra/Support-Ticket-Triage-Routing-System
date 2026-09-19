import React from 'react';
import { Search, RotateCcw, Star } from 'lucide-react';
import clsx from 'clsx';

export const QueueFilterBar = ({
  searchQuery,
  setSearchQuery,
  categoryFilter,
  setCategoryFilter,
  priorityFilter,
  setPriorityFilter,
  teamFilter,
  setTeamFilter,
  vipOnly,
  setVipOnly,
  onReset,
}) => {
  const hasActiveFilters =
    searchQuery || categoryFilter !== 'ALL' || priorityFilter !== 'ALL' || teamFilter !== 'ALL' || vipOnly;

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-3 shadow-sm md:flex-row md:items-center">
      <div className="relative flex-1">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input
          type="search"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search tickets, customers, IDs…"
          className="input pl-9"
          aria-label="Search tickets"
        />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="input w-auto"
          aria-label="Category"
        >
          <option value="ALL">All categories</option>
          <option value="Hardware">Hardware</option>
          <option value="Software">Software</option>
          <option value="Network">Network</option>
          <option value="Access & Security">Access &amp; Security</option>
          <option value="Billing & Admin">Billing &amp; Admin</option>
        </select>

        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="input w-auto"
          aria-label="Priority"
        >
          <option value="ALL">All priorities</option>
          <option value="Critical">Critical</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>

        <select
          value={teamFilter}
          onChange={(e) => setTeamFilter(e.target.value)}
          className="input w-auto"
          aria-label="Team"
        >
          <option value="ALL">All teams</option>
          <option value="Software">Software Engineering</option>
          <option value="Network">Network Operations</option>
          <option value="Security">Security Operations</option>
          <option value="Billing">Billing &amp; Accounts</option>
          <option value="Human Triage">Human Triage</option>
        </select>

        <button
          type="button"
          onClick={() => setVipOnly(!vipOnly)}
          aria-pressed={vipOnly}
          className={clsx(
            'inline-flex h-9 items-center gap-1.5 rounded-md border px-3 text-sm font-medium transition-colors',
            vipOnly
              ? 'border-amber-300 bg-amber-50 text-amber-800'
              : 'border-slate-300 bg-white text-slate-600 hover:bg-slate-50'
          )}
        >
          <Star className="h-3.5 w-3.5" />
          VIP
        </button>

        {hasActiveFilters && (
          <button
            type="button"
            onClick={onReset}
            className="inline-flex h-9 items-center gap-1.5 rounded-md px-2.5 text-sm text-slate-500 hover:bg-slate-100 hover:text-slate-900"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Reset
          </button>
        )}
      </div>
    </div>
  );
};
