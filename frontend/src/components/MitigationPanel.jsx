import React, { useState } from 'react';
import axios from 'axios';
import { Shield, Lock, Server, Activity } from 'lucide-react';

const AI_URL = 'http://localhost:5500';

export default function MitigationPanel({ active, onToggle }) {
  const [loading, setLoading] = useState(false);

  const toggleMitigation = async () => {
    setLoading(true);
    try {
      await axios.post(`${AI_URL}/mitigation/toggle`, { active: !active });
      onToggle();
    } catch (err) {
      console.error('Mitigation Error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flat-card p-6 space-y-6">
      <div className="flex items-center justify-between border-b border-border pb-4">
        <h3 className="font-bold text-slate-200 flex items-center gap-2">
          <Shield className="w-4 h-4 text-accent" />
          Mitigation Controls
        </h3>
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${active ? 'bg-success/10 border-success/20 text-success' : 'bg-slate-800 border-border text-slate-500'}`}>
          {active ? 'PROTECTION ON' : 'MONITORING ONLY'}
        </span>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between p-4 rounded bg-slate-800/30 border border-border">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded ${active ? 'bg-success/10 text-success' : 'bg-slate-800 text-slate-500'}`}>
               <Lock className="w-4 h-4" />
            </div>
            <div>
              <p className="text-sm font-bold text-slate-300">Automated Mitigation</p>
              <p className="text-[10px] text-slate-500">Apply rate-limiting rules via HAProxy when attacks are detected.</p>
            </div>
          </div>
          <button 
            onClick={toggleMitigation}
            disabled={loading}
            className={`relative inline-flex h-5 w-10 items-center rounded-full transition-colors focus:outline-none ${active ? 'bg-accent' : 'bg-slate-700'}`}
          >
            <span className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${active ? 'translate-x-6' : 'translate-x-1'}`} />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <StrategyCard icon={<Server className="w-3.5 h-3.5" />} label="Rate Limiting" active={active} />
          <StrategyCard icon={<Activity className="w-3.5 h-3.5" />} label="IP Filtering" active={active} />
        </div>
      </div>
    </div>
  );
}

function StrategyCard({ icon, label, active }) {
  return (
    <div className={`flex items-center gap-2 p-2.5 rounded border ${active ? 'bg-accent/5 border-accent/20 text-accent' : 'bg-slate-800/20 border-border text-slate-500'}`}>
      {icon}
      <span className="text-xs font-semibold">{label}</span>
    </div>
  );
}
