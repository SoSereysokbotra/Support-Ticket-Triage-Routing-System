import React from 'react';
import { Search, Filter, RotateCcw, Crown, ShieldAlert } from 'lucide-react';

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
  onReset
}) => {
  return (
    <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 p-4 rounded-xl bg-slate-900/80 border border-slate-800">
      {/* Search Input */}
      <div className="relative flex-1">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search by ticket ID, title, summary, or customer..."
          className="w-full pl-10 pr-4 py-2 rounded-xl glass-input text-xs text-white placeholder-slate-500 outline-none"
        />
      </div>

      {/* Select Filters */}
      <div className="flex flex-wrap items-center gap-2.5">
        {/* Category */}
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="px-3 py-2 rounded-xl glass-input text-xs text-slate-200 outline-none bg-slate-900"
        >
          <option value="ALL">All Categories</option>
          <option value="Hardware">Hardware</option>
          <option value="Software">Software</option>
          <option value="Network">Network</option>
          <option value="Access & Security">Access & Security</option>
          <option value="Billing & Admin">Billing & Admin</option>
        </select>

        {/* Priority */}
        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="px-3 py-2 rounded-xl glass-input text-xs text-slate-200 outline-none bg-slate-900"
        >
          <option value="ALL">All Priorities</option>
          <option value="Critical">Critical</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>

        {/* Team */}
        <select
          value={teamFilter}
          onChange={(e) => setTeamFilter(e.target.value)}
          className="px-3 py-2 rounded-xl glass-input text-xs text-slate-200 outline-none bg-slate-900 max-w-[160px]"
        >
          <option value="ALL">All Teams</option>
          <option value="Software">Software Eng</option>
          <option value="Network">Network Ops</option>
          <option value="Security">Security Ops</option>
          <option value="Billing">Billing & Accounts</option>
          <option value="Human Triage">Human Triage</option>
        </select>

        {/* VIP Toggle */}
        <button
          type="button"
          onClick={() => setVipOnly(!vipOnly)}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold transition-all border ${vipOnly ? 'bg-amber-500/20 text-yellow-300 border-yellow-500/50 shadow-sm' : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'}`}
        >
          <Crown className="w-3.5 h-3.5" />
          <span>VIP Only</span>
        </button>

        {/* Reset */}
        <button
          type="button"
          onClick={onReset}
          className="p-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-all border border-transparent hover:border-slate-700"
          title="Reset Filters"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
