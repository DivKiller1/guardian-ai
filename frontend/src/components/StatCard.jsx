import React from 'react';

export default function StatCard({ title, value, icon, variant = 'default' }) {
  const isWarning = variant === 'warning';
  
  return (
    <div className="flat-card p-6">
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-lg ${isWarning ? 'bg-danger/10 text-danger' : 'bg-accent/10 text-accent'}`}>
          {icon}
        </div>
        <div>
          <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider">{title}</p>
          <h4 className="text-2xl font-bold text-white">{value}</h4>
        </div>
      </div>
    </div>
  );
}
