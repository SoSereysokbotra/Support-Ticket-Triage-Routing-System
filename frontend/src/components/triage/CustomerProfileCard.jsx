import React from 'react';
import { GlassPanel } from '../common/GlassPanel';
import { Badge } from '../common/Badge';
import { UserCheck, Clock, History, Crown, ShieldAlert } from 'lucide-react';

export const CustomerProfileCard = ({ customerId, features }) => {
  if (!features) {
    return (
      <GlassPanel className="p-4 bg-slate-900/40 border-dashed border-slate-800">
        <div className="flex items-center gap-3 text-slate-500 text-xs">
          <UserCheck className="w-4 h-4" />
          <span>Select or enter a customer ID to fetch Feast online features</span>
        </div>
      </GlassPanel>
    );
  }

  const { customer_tier, is_vip, past_ticket_count, avg_resolution_time_hours } = features;

  return (
    <GlassPanel 
      glowColor={is_vip ? 'purple' : 'none'} 
      className="p-5 bg-gradient-to-br from-slate-900/90 to-slate-950/90 border-slate-800 space-y-4"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${is_vip ? 'bg-amber-500/20 text-yellow-400 border border-yellow-500/40' : 'bg-slate-800 text-slate-300'}`}>
            {is_vip ? <Crown className="w-4 h-4" /> : <UserCheck className="w-4 h-4" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm font-bold text-white">{customerId}</span>
              {is_vip && <Badge label="VIP Account" variant="VIP" size="sm" />}
            </div>
            <span className="text-[11px] text-slate-400 font-medium">Feast Feature Store Entity</span>
          </div>
        </div>

        <Badge label={customer_tier || 'Standard'} variant={customer_tier === 'Enterprise' ? 'purple' : 'cyan'} size="sm" />
      </div>

      {/* Feature Grid */}
      <div className="grid grid-cols-2 gap-3 pt-2 border-t border-white/5">
        <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
          <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <History className="w-3 h-3 text-cyan-400" />
            <span>Past Tickets</span>
          </div>
          <span className="text-sm font-bold text-white font-mono mt-0.5 block">
            {past_ticket_count ?? 0}
          </span>
        </div>

        <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
          <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <Clock className="w-3 h-3 text-purple-400" />
            <span>Avg Resolution</span>
          </div>
          <span className="text-sm font-bold text-white font-mono mt-0.5 block">
            {avg_resolution_time_hours ? `${avg_resolution_time_hours}h` : 'N/A'}
          </span>
        </div>
      </div>

      {is_vip && (
        <div className="flex items-center gap-2 text-[11px] text-amber-300 bg-amber-500/10 p-2.5 rounded-lg border border-amber-500/30">
          <ShieldAlert className="w-3.5 h-3.5 shrink-0" />
          <span>VIP Escalation active: Priority promoted & SLA reduced to 2 hours.</span>
        </div>
      )}
    </GlassPanel>
  );
};
