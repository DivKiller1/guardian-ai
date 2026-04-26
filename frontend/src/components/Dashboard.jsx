import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Shield, ShieldAlert, ShieldCheck, Activity, BarChart3, Clock, Zap, AlertTriangle } from 'lucide-react';
import TrafficChart from './TrafficChart';
import AttackAnalysis from './AttackAnalysis';
import MitigationPanel from './MitigationPanel';
import StatCard from './StatCard';

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
      console.error('API Error:', err);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 3000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return (
    <div className="flex h-screen w-full items-center justify-center bg-background">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
    </div>
  );

  return (
    <div className="min-h-screen p-6 md:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-border pb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2 text-white">
            <Shield className="w-6 h-6 text-accent" />
            Guardian AI
          </h1>
          <p className="text-slate-400 text-sm mt-1">Real-time DDoS detection and automated mitigation system.</p>
        </div>
        <div className="flex items-center gap-6">
           <div className="flex flex-col items-end">
              <span className="text-[10px] uppercase text-slate-500 font-bold tracking-widest">Status</span>
              <div className="flex items-center gap-1.5 mt-0.5">
                <div className={`w-2 h-2 rounded-full ${stats.mitigation_active ? 'bg-success' : 'bg-slate-500'}`} />
                <span className="text-sm font-semibold text-white">
                  {stats.mitigation_active ? 'Mitigation Active' : 'Monitoring'}
                </span>
              </div>
           </div>
           <div className="h-10 w-px bg-border" />
           <div className="flex flex-col items-end">
              <span className="text-[10px] uppercase text-slate-500 font-bold tracking-widest">Risk Level</span>
              <span className={`text-sm font-bold mt-0.5 ${stats.current_risk_level === 'HIGH' ? 'text-danger' : stats.current_risk_level === 'MEDIUM' ? 'text-warning' : 'text-success'}`}>
                {stats.current_risk_level}
              </span>
           </div>
        </div>
      </header>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Total Events" 
          value={stats.total_detections} 
          icon={<BarChart3 className="w-5 h-5" />} 
        />
        <StatCard 
          title="Active Threats" 
          value={stats.recent_attacks_count} 
          icon={<Zap className="w-5 h-5" />} 
          variant={stats.recent_attacks_count > 0 ? "warning" : "default"}
        />
        <StatCard 
          title="System Load" 
          value="0.4 ms" 
          icon={<Activity className="w-5 h-5" />} 
        />
        <StatCard 
          title="Blocked IPs" 
          value={stats.mitigation_active ? "Global" : "None"} 
          icon={<Shield className="w-5 h-5" />} 
        />
      </div>

      {/* Traffic and Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 flat-card p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-bold text-slate-200 flex items-center gap-2">
              <Activity className="w-4 h-4 text-accent" />
              Network Traffic
            </h3>
          </div>
          <div className="h-[300px] w-full">
            <TrafficChart history={history} />
          </div>
        </div>
        
        <div className="flat-card p-6">
          <h3 className="font-bold text-slate-200 flex items-center gap-2 mb-6">
            <AlertTriangle className="w-4 h-4 text-danger" />
            Attack Distribution
          </h3>
          <AttackAnalysis distribution={stats.attack_type_distribution} />
        </div>
      </div>

      {/* Controls and Logs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <MitigationPanel active={stats.mitigation_active} onToggle={fetchStats} />
        </div>
        <div className="lg:col-span-2 flat-card p-6">
          <div className="flex items-center gap-2 mb-6 border-b border-border pb-4">
            <Clock className="w-4 h-4 text-slate-500" />
            <h3 className="font-bold text-slate-200">System Activity Logs</h3>
          </div>
          <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
            {history.slice().reverse().map((log, idx) => (
              <div 
                key={log.timestamp + idx}
                className="flex items-center justify-between p-3 rounded border border-border bg-slate-800/30 hover:bg-slate-800/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-1.5 h-1.5 rounded-full ${log.is_attack ? 'bg-danger' : 'bg-success'}`} />
                  <span className="text-sm font-medium text-slate-300 capitalize">{log.attack_type.replace('_', ' ')}</span>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-[10px] font-mono text-accent bg-accent/5 px-2 py-0.5 border border-accent/10 rounded">
                    CONF: {log.confidence.toFixed(1)}%
                  </span>
                  <span className="text-[10px] text-slate-500 font-medium">{new Date(log.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
