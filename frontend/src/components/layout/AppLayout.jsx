import React from 'react';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';
import { NAV_ITEMS } from './navigation';
import clsx from 'clsx';

export const AppLayout = ({ children, activeTab, onTabChange }) => (
  <div className="flex min-h-screen flex-col">
    <Navbar />

    <div className="flex flex-1">
      <Sidebar activeTab={activeTab} onTabChange={onTabChange} />

      <main className="min-w-0 flex-1">
        {/* Small screens: tabs across the top instead of the sidebar */}
        <nav className="flex gap-1 overflow-x-auto border-b border-slate-200 bg-white px-4 md:hidden">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => onTabChange(item.id)}
              className={clsx(
                '-mb-px whitespace-nowrap border-b-2 px-3 py-3 text-sm font-medium',
                activeTab === item.id
                  ? 'border-blue-600 text-blue-700'
                  : 'border-transparent text-slate-500 hover:text-slate-900'
              )}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="mx-auto max-w-7xl space-y-6 p-4 sm:p-6 lg:p-8">{children}</div>
      </main>
    </div>
  </div>
);
