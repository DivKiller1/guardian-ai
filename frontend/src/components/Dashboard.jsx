import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Shield, ShieldAlert, ShieldCheck, Activity, BarChart3, Clock, Zap, Settings } from 'lucide-react';
import TrafficChart from './TrafficChart';
import AttackAnalysis from './AttackAnalysis';
import MitigationPanel from './MitigationPanel';
import StatCard from './StatCard';
import { motion, AnimatePresence } from 'framer-motion';

const AI_URL = 'http://localhost:5500';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    try {
      const [statsRes, historyRes] = await Promise.all([
        axios.get(`${AI_URL}/stats`),
        axios.get(`${AI_URL}/history`)
      ]);
      setStats(statsRes.data);
      setHistory(historyRes.data);
      setLoading(false);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 3000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return (
    <div className="flex h-screen w-full items-center justify-center bg-background">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-accent border-t-transparent" />
    </div>
  );

  return (
    <div className="min-h-screen p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold gradient-text flex items-center gap-2">
            <Shield className="w-8 h-8 text-accent" />
            Guardian AI
          </h1>
          <p className="text-slate-400 mt-1">Autonomous DDoS Protection Engine</p>
        </div>
        <div className="flex items-center gap-4 bg-card/50 p-2 rounded-xl border border-white/5">
           <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${stats.mitigation_active ? 'bg-success/10 text-success' : 'bg-slate-800 text-slate-400'}`}>
              {stats.mitigation_active ? <ShieldCheck className="w-4 h-4" /> : <ShieldAlert className="w-4 h-4" />}
              <span className="text-sm font-medium">{stats.mitigation_active ? 'Mitigation Active' : 'Monitoring Only'}</span>
           </div>
           <div className="w-px h-6 bg-white/10" />
           <div className="flex flex-col">
              <span className="text-[10px] uppercase text-slate-500 font-bold">Risk Level</span>
              <span className={`text-sm font-bold ${stats.current_risk_level === 'HIGH' ? 'text-danger' : stats.current_risk_level === 'MEDIUM' ? 'text-warning' : 'text-success'}`}>
                {stats.current_risk_level}
              </span>
           </div>
        </div>
      </header>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Total Detections" 
          value={stats.total_detections} 
          icon={<BarChart3 className="w-5 h-5 text-accent" />} 
          trend={+12}
        />
        <StatCard 
          title="Recent Attacks" 
          value={stats.recent_attacks_count} 
          icon={<Zap className="w-5 h-5 text-warning" />} 
          variant={stats.recent_attacks_count > 0 ? "warning" : "default"}
        />
        <StatCard 
          title="System Health" 
          value="99.9%" 
          icon={<Activity className="w-5 h-5 text-success" />} 
        />
        <StatCard 
          title="Active Filters" 
          value={stats.mitigation_active ? 14 : 0} 
          icon={<Shield className="w-5 h-5 text-purple-400" />} 
        />
      </div>

      {/* Main Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass rounded-2xl p-6 neon-border min-h-[450px]">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-bold text-lg flex items-center gap-2 text-slate-200">
              <Activity className="w-5 h-5 text-accent" />
              Real-time Traffic Monitor
            </h3>
          </div>
          <div className="h-[350px] w-full">
            <TrafficChart history={history} />
          </div>
        </div>
        
        <div className="glass rounded-2xl p-6 border-white/5 space-y-6">
          <h3 className="font-bold text-lg flex items-center gap-2 text-slate-200">
            <ShieldAlert className="w-5 h-5 text-danger" />
            Attack Fingerprinting
          </h3>
          <AttackAnalysis distribution={stats.attack_type_distribution} />
        </div>
      </div>

      {/* Bottom Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <MitigationPanel active={stats.mitigation_active} onToggle={fetchStats} />
        </div>
        <div className="lg:col-span-2 glass rounded-2xl p-6 border-white/5">
          <div className="flex items-center gap-2 mb-4 text-slate-200">
            <Clock className="w-5 h-5 text-slate-400" />
            <h3 className="font-bold">Live Detection Logs</h3>
          </div>
          <div className="space-y-3 max-h-[250px] overflow-y-auto pr-2 custom-scrollbar">
            <AnimatePresence mode="popLayout">
              {history.slice().reverse().map((log, idx) => (
                <motion.div 
                  layout
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  key={log.timestamp + idx}
                  className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${log.is_attack ? 'bg-danger animate-pulse' : 'bg-success'}`} />
                    <span className="text-sm font-medium text-slate-300 capitalize">{log.attack_type.replace('_', ' ')}</span>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-slate-500">
                    <span className="bg-slate-800 px-2 py-0.5 rounded text-accent font-mono">
                      CONF: {log.confidence.toFixed(1)}%
                    </span>
                    <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}
