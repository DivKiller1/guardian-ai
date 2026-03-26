import React, { useState } from 'react';
import axios from 'axios';
import { Shield, ShieldAlert, ShieldCheck, Zap, Lock, Unlock, Server } from 'lucide-react';
import { motion } from 'framer-motion';

const AI_URL = 'http://localhost:5500';

export default function MitigationPanel({ active, onToggle }) {
  const [loading, setLoading] = useState(false);

  const toggleMitigation = async () => {
    setLoading(true);
    try {
      await axios.post(`${AI_URL}/mitigation/toggle`, { active: !active });
      onToggle();
    } catch (err) {
      console.error('Failed to toggle mitigation:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass rounded-2xl p-6 border-white/5 space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-lg flex items-center gap-2 text-slate-200">
          <Shield className="w-5 h-5 text-accent" />
          Mitigation Center
        </h3>
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${active ? 'bg-success/20 text-success' : 'bg-slate-800 text-slate-500'}`}>
          {active ? 'AI-ARMED' : 'STANDBY'}
        </span>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${active ? 'bg-success/10 text-success' : 'bg-slate-800 text-slate-500'}`}>
               <Lock className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm font-bold text-slate-300">Auto-Mitigation</p>
              <p className="text-[10px] text-slate-500 text-balance">Enable AI-driven traffic filtering and rate limiting.</p>
            </div>
          </div>
          <button 
            onClick={toggleMitigation}
            disabled={loading}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 focus:ring-offset-slate-900 ${active ? 'bg-accent' : 'bg-slate-700'}`}
          >
            <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${active ? 'translate-x-6' : 'translate-x-1'}`} />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <StrategyCard icon={<Server className="w-4 h-4" />} label="Rate Limit" active={active} />
          <StrategyCard icon={<Zap className="w-4 h-4" />} label="Challenge" active={active} />
        </div>
      </div>
      
      <div className="p-3 rounded-lg bg-accent/5 border border-accent/10">
        <p className="text-[10px] text-accent/80 leading-relaxed italic">
          "Guardian AI is currently processing 15 traffic features per second and analyzing temporal patterns for anomalies."
        </p>
      </div>
    </div>
  );
}

function StrategyCard({ icon, label, active }) {
  return (
    <div className={`flex items-center gap-2 p-2.5 rounded-lg border transition-all ${active ? 'bg-accent/5 border-accent/20 text-accent' : 'bg-slate-800/50 border-white/5 text-slate-500 opacity-50'}`}>
      {icon}
      <span className="text-xs font-medium">{label}</span>
    </div>
  );
}
