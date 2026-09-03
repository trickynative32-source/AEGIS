import React, { useState, useEffect } from 'react';
import { Clock, Calendar, CheckCircle2 } from 'lucide-react';

export const LiveClock: React.FC = () => {
  const [now, setNow] = useState<Date>(new Date());

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
  const dateStr = now.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-2xl bg-slate-900/60 border border-slate-700/60 shadow-sm backdrop-blur-md">
      <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
      <span className="font-mono text-xs sm:text-sm font-bold tracking-wider text-slate-100">{timeStr}</span>
      <span className="text-[10px] font-mono text-slate-400 hidden lg:inline border-l border-slate-700 pl-2">
        {dateStr}
      </span>
    </div>
  );
};
