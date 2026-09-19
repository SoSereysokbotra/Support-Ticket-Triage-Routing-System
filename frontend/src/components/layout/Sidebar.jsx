import React from 'react';
import clsx from 'clsx';
import { NAV_ITEMS } from './navigation';

export const Sidebar = ({ activeTab, onTabChange }) => (
  <aside className="hidden w-56 shrink-0 border-r border-slate-200 bg-white md:block">
    <nav className="sticky top-14 space-y-1 p-3">
      {NAV_ITEMS.map((item) => {
        const Icon = item.icon;
        const isActive = activeTab === item.id;
        return (
          <button
            key={item.id}
            type="button"
            onClick={() => onTabChange(item.id)}
            aria-current={isActive ? 'page' : undefined}
            className={clsx(
              'flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors',
              isActive
                ? 'bg-slate-100 font-medium text-slate-900'
                : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
            )}
          >
            <Icon className={clsx('h-4 w-4', isActive ? 'text-blue-600' : 'text-slate-400')} />
            {item.label}
          </button>
        );
      })}
    </nav>
  </aside>
);
