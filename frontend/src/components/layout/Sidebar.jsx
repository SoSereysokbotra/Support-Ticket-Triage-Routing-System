import React from 'react';
import { Send, ListFilter, Cpu, BookOpen, Layers } from 'lucide-react';
import clsx from 'clsx';

export const Sidebar = ({ activeTab, onTabChange }) => {
  const navItems = [
    {
      id: 'triage',
      label: 'Live AI Triage',
      icon: Send,
      description: 'Real-time ticket classification & routing',
      badge: 'Interactive',
    },
    {
      id: 'queue',
      label: 'Agent Triage Queue',
      icon: ListFilter,
      description: 'Routed tickets, SLAs & dispatch queue',
    },
    {
      id: 'mlops',
      label: 'MLOps Command',
      icon: Cpu,
      description: 'Drift monitor, model registry & DAG',
      badge: 'Evidently',
    },
  ];

  return (
    <aside className="w-64 border-r border-white/5 bg-surface-sidebar/50 backdrop-blur-xl flex flex-col justify-between p-4 shrink-0 min-h-[calc(100vh-4rem)]">
      {/* Navigation Links */}
      <div className="space-y-6">
        <div>
          <div className="px-3 mb-2 text-[10px] font-bold tracking-wider text-slate-500 uppercase">
            Workspaces
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onTabChange(item.id)}
                  className={clsx(
                    'w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-all group relative',
                    isActive
                      ? 'bg-gradient-to-r from-cyan-500/15 to-blue-500/10 text-cyan-400 border border-cyan-500/30 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                  )}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={clsx('w-4 h-4 transition-colors', isActive ? 'text-cyan-400' : 'text-slate-400 group-hover:text-slate-200')} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-slate-400">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* System Architecture summary block */}
        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            <span>Active MLOps Stack</span>
          </div>
          <div className="text-[11px] text-slate-400 space-y-1 font-mono">
            <div className="flex justify-between">
              <span>Model:</span>
              <span className="text-cyan-400">DistilBERT</span>
            </div>
            <div className="flex justify-between">
              <span>Store:</span>
              <span className="text-purple-400">Feast (0% Skew)</span>
            </div>
            <div className="flex justify-between">
              <span>Orchestrator:</span>
              <span className="text-blue-400">Prefect 3</span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="pt-4 border-t border-white/5 text-[11px] text-slate-500 text-center">
        Hexagonal Architecture • DDD
      </div>
    </aside>
  );
};
