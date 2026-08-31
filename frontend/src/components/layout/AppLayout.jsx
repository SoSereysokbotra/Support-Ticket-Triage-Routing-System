import React from 'react';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';

export const AppLayout = ({ children, activeTab, onTabChange }) => {
  return (
    <div className="min-h-screen flex flex-col bg-background text-slate-100 selection:bg-cyan-500/20 selection:text-cyan-400">
      <Navbar />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar activeTab={activeTab} onTabChange={onTabChange} />
        <main className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6">
          <div className="max-w-7xl mx-auto space-y-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};
