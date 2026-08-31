import React, { useState, useEffect } from 'react';
import { Clock, Calendar, CheckCircle2 } from 'lucide-react';

export const LiveClock: React.FC = () => {
  const [now, setNow] = useState<Date>(new Date());

  useEffect(() => {
    // Update live every second from actual local system clock
    const timer = setInterval(() => {
      setNow(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
  const dateStr = now.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });

  return (
    <div className="flex items-center gap-3 px-4 py-2 rounded-xl bg-slate-900/80 border border-cyan-500/30 shadow-lg shadow-cyan-950/20 backdrop-blur-md">
      <div className="p-2 rounded-lg bg-cyan-950/60 border border-cyan-500/40 text-aura-cyan">
        <Clock className="w-5 h-5 animate-pulse" />
      </div>
      <div>
        <div className="flex items-center gap-2">
          <span className="font-mono text-lg font-bold tracking-wider text-slate-100">{timeStr}</span>
          <span className="flex items-center gap-1 text-[10px] uppercase tracking-wider font-semibold px-1.5 py-0.5 rounded bg-emerald-950/80 border border-emerald-500/40 text-emerald-400">
            <CheckCircle2 className="w-3 h-3" /> Real Win Clock
          </span>
        </div>
        <div className="flex items-center gap-1 text-xs text-slate-400 font-medium">
          <Calendar className="w-3.5 h-3.5 text-cyan-400" />
          <span>{dateStr}</span>
        </div>
      </div>
    </div>
  );
};
