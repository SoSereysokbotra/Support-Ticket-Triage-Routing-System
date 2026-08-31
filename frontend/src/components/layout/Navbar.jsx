import React, { useEffect, useState } from 'react';
import { Shield, Activity, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';
import { checkHealth } from '../../services/api';

export const Navbar = () => {
  const [healthStatus, setHealthStatus] = useState({ ok: false, loading: true, data: null });

  const pollHealth = async () => {
    setHealthStatus(prev => ({ ...prev, loading: true }));
    const result = await checkHealth();
    setHealthStatus({ ok: result.ok, loading: false, data: result.data || null });
  };

  useEffect(() => {
    pollHealth();
    const interval = setInterval(pollHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 border-b border-white/5 bg-surface-sidebar/80 backdrop-blur-xl sticky top-0 z-40 px-6 flex items-center justify-between">
      {/* Brand Title */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-glow-cyan">
          <Shield className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-base tracking-tight text-white flex items-center gap-2">
            AutoTriage <span className="text-cyan-400 text-xs px-2 py-0.5 rounded-md bg-cyan-500/10 border border-cyan-500/30 font-mono">MLOps v2.0</span>
          </h1>
          <p className="text-xs text-slate-400 hidden sm:block">Intelligent Support Ticket Triage & Routing System</p>
        </div>
      </div>

      {/* Backend Status & Quick Stats */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/80 border border-slate-800 text-xs">
          {healthStatus.ok ? (
            <>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-sm" />
              <span className="text-slate-300 font-medium">API Online</span>
              {healthStatus.data?.model_version && (
                <span className="font-mono text-cyan-400 text-[10px] bg-cyan-500/10 px-1.5 py-0.5 rounded border border-cyan-500/20">
                  {healthStatus.data.model_version}
                </span>
              )}
            </>
          ) : (
            <>
              <span className="w-2 h-2 rounded-full bg-rose-500" />
              <span className="text-rose-400 font-medium">API Offline (Port 8000)</span>
            </>
          )}
          <button 
            onClick={pollHealth} 
            className="text-slate-500 hover:text-slate-300 transition-colors ml-1"
            title="Refresh Health"
          >
            <RefreshCw className={`w-3 h-3 ${healthStatus.loading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>
      </div>
    </header>
  );
};
