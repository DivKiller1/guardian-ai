import React from 'react';
import { motion } from 'framer-motion';

export default function StatCard({ title, value, icon, trend, variant = 'default' }) {
  const isWarning = variant === 'warning';
  
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass p-5 rounded-2xl border-white/5 relative overflow-hidden group"
    >
      <div className="flex justify-between items-start mb-4">
        <div className={`p-2.5 rounded-xl ${isWarning ? 'bg-warning/10 text-warning' : 'bg-accent/10 text-accent'} border border-white/5`}>
          {icon}
        </div>
        {trend && (
           <span className="text-[10px] font-bold text-success bg-success/10 px-1.5 py-0.5 rounded italic">
             +{trend}%
           </span>
        )}
      </div>
      <div>
        <p className="text-sm text-slate-400 font-medium mb-1">{title}</p>
        <h4 className="text-2xl font-bold text-slate-100">{value}</h4>
      </div>
      
      {/* Decorative backdrop */}
      <div className={`absolute -right-4 -bottom-4 w-24 h-24 rounded-full blur-3xl opacity-10 group-hover:opacity-20 transition-opacity ${isWarning ? 'bg-warning' : 'bg-accent'}`} />
    </motion.div>
  );
}
