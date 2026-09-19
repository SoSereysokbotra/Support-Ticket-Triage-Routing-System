import React, { useEffect, useState } from 'react';
import { Shield, RefreshCw } from 'lucide-react';
import clsx from 'clsx';
import { checkHealth } from '../../services/api';

export const Navbar = () => {
  const [health, setHealth] = useState({ ok: false, loading: true, data: null });

  const pollHealth = async () => {
    setHealth((prev) => ({ ...prev, loading: true }));
    const result = await checkHealth();
    setHealth({ ok: result.ok, loading: false, data: result.data || null });
  };

  useEffect(() => {
    pollHealth();
    const interval = setInterval(pollHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-40 flex h-14 items-center justify-between border-b border-slate-200 bg-white px-4 sm:px-6">
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-blue-600 text-white">
          <Shield className="h-4 w-4" />
        </div>
        <div className="leading-tight">
          <div className="text-sm font-semibold text-slate-900">AutoTriage</div>
          <div className="hidden text-xs text-slate-500 sm:block">Support ticket triage &amp; routing</div>
        </div>
      </div>

      <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 py-1 pl-3 pr-1.5 text-xs">
        <span
          className={clsx('h-2 w-2 rounded-full', health.ok ? 'bg-emerald-500' : 'bg-red-500')}
          aria-hidden="true"
        />
        <span className="font-medium text-slate-700">{health.ok ? 'API connected' : 'API unreachable'}</span>
        {health.ok && health.data?.model_version && (
          <span className="hidden font-mono text-slate-500 sm:inline">{health.data.model_version}</span>
        )}
        <button
          type="button"
          onClick={pollHealth}
          className="rounded-full p-1 text-slate-400 hover:bg-slate-200 hover:text-slate-700"
          title="Check again"
          aria-label="Check API status"
        >
          <RefreshCw className={clsx('h-3 w-3', health.loading && 'animate-spin')} />
        </button>
      </div>
    </header>
  );
};
