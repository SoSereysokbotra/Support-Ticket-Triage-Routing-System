import React from 'react';
import { Masthead } from './Masthead';

export const AppLayout = ({ children, activeTab, onTabChange }) => (
  <div className="flex min-h-screen flex-col">
    <Masthead activeTab={activeTab} onTabChange={onTabChange} />

    <main className="flex-1">
      <div className="mx-auto max-w-page space-y-8 px-5 py-8">{children}</div>
    </main>

    <footer className="border-t border-rule">
      <div className="mx-auto flex max-w-page flex-col gap-1 px-5 py-4 text-xs text-muted sm:flex-row sm:items-center sm:justify-between">
        <span>AutoTriage</span>
        <span>DistilBERT · Feast · MLflow · Evidently · Prefect</span>
      </div>
    </footer>
  </div>
);
