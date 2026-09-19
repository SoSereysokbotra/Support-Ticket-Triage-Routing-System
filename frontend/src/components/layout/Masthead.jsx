import React, { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import clsx from 'clsx';
import { checkHealth } from '../../services/api';
import { NAV_ITEMS } from './navigation';

const Mark = () => (
  <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true">
    <rect width="22" height="22" fill="#0F1720" />
    <rect x="3" y="3" width="7" height="7" fill="#F2F4F5" />
    <rect x="12" y="3" width="7" height="7" fill="#0E7C86" />
    <rect x="3" y="12" width="7" height="7" fill="#F2F4F5" />
    <rect x="12" y="12" width="7" height="7" fill="#F2F4F5" />
  </svg>
);

const formatClock = (date) =>
  date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

/**
 * Two-row header: an ink status strip (API health, model version, clock)
 * over a masthead with the wordmark and numbered section tabs.
 */
export const Masthead = ({ activeTab, onTabChange }) => {
  const [health, setHealth] = useState({ ok: false, loading: true, data: null });
  const [clock, setClock] = useState(() => formatClock(new Date()));

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

  useEffect(() => {
    const tick = setInterval(() => setClock(formatClock(new Date())), 1000);
    return () => clearInterval(tick);
  }, []);

  return (
    <header className="sticky top-0 z-40">
      {/* Status strip */}
      <div className="bg-ink text-paper">
        <div className="mx-auto flex h-8 max-w-page items-center justify-between px-5 text-[13px]">
          <div className="flex min-w-0 items-center gap-2.5">
            <span
              className={clsx('h-2 w-2 shrink-0', health.ok ? 'bg-live' : 'bg-bad')}
              aria-hidden="true"
            />
            <span className="truncate">{health.ok ? 'API connected' : 'API unreachable'}</span>
            {health.ok && health.data?.model_version && (
              <>
                <span className="text-paper/30">/</span>
                <span className="hidden truncate text-paper/70 sm:inline">{health.data.model_version}</span>
              </>
            )}
          </div>
          <div className="flex items-center gap-3">
            <span className="tabular-nums text-paper/70">{clock}</span>
            <button
              type="button"
              onClick={pollHealth}
              className="flex h-5 w-5 items-center justify-center text-paper/60 transition-colors hover:text-paper"
              title="Check again"
              aria-label="Check API status"
            >
              <RefreshCw className={clsx('h-3 w-3', health.loading && 'animate-spin')} />
            </button>
          </div>
        </div>
      </div>

      {/* Masthead */}
      <div className="border-b border-ink bg-surface">
        <div className="mx-auto flex h-14 max-w-page items-stretch justify-between gap-6 px-5">
          <div className="flex shrink-0 items-center gap-3">
            <Mark />
            <span className="font-serif text-[22px] leading-none text-ink">AutoTriage</span>
            <span className="hidden border-l border-rule pl-3 text-xs text-muted lg:inline">
              Support ticket triage &amp; routing
            </span>
          </div>

          <nav className="flex items-stretch gap-6 overflow-x-auto" aria-label="Sections">
            {NAV_ITEMS.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onTabChange(item.id)}
                  aria-current={isActive ? 'page' : undefined}
                  className={clsx(
                    'relative flex items-center gap-2 whitespace-nowrap text-[15px] font-semibold transition-colors',
                    isActive ? 'text-ink' : 'text-muted hover:text-ink'
                  )}
                >
                  <span className={clsx('text-xs', isActive ? 'text-accent' : 'text-rule-strong')}>
                    {item.index}
                  </span>
                  {item.label}
                  {isActive && <span className="absolute inset-x-0 -bottom-px h-0.5 bg-ink" aria-hidden="true" />}
                </button>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
};
