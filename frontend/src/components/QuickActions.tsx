import React from 'react';
import { Clock, Palette, Music, Navigation, FileCode, MapPin, Mic, LogOut, Eye, Search, Plane, Sparkles } from 'lucide-react';

interface QuickActionsProps {
  onSelectAction: (prompt: string) => void;
}

export const QuickActions: React.FC<QuickActionsProps> = ({ onSelectAction }) => {
  const actions = [
    { label: 'Play Believer on YouTube', prompt: 'Play Believer by Imagine Dragons', icon: Music, color: 'text-rose-400 border-rose-500/30 bg-rose-950/40' },
    { label: 'Book Flight Ticket', prompt: 'Book a flight ticket from my given location', icon: Plane, color: 'text-cyan-400 border-cyan-500/30 bg-cyan-950/40' },
    { label: 'Explain Quantum Computing', prompt: 'Explain quantum computing in detail', icon: Sparkles, color: 'text-indigo-400 border-indigo-500/30 bg-indigo-950/40' },
    { label: 'Time & Date', prompt: 'What time is it?', icon: Clock, color: 'text-cyan-400 border-cyan-500/30 bg-cyan-950/40' },
    { label: 'Scan Surroundings', prompt: 'Describe what you see in front of the camera', icon: Eye, color: 'text-teal-400 border-teal-500/30 bg-teal-950/40' },
    { label: 'Where is my phone?', prompt: 'Where is my phone?', icon: Search, color: 'text-purple-400 border-purple-500/30 bg-purple-950/40' },
    { label: 'Directions to Airport', prompt: 'Show directions from my current location to Bangalore Airport', icon: Navigation, color: 'text-blue-400 border-blue-500/30 bg-blue-950/40' },
    { label: 'Python Calculator', prompt: 'Create a Python calculator on my Desktop', icon: FileCode, color: 'text-emerald-400 border-emerald-500/30 bg-emerald-950/40' },
    { label: 'Goodbye', prompt: 'Goodbye', icon: LogOut, color: 'text-red-400 border-red-500/30 bg-red-950/40' },
  ];

  return (
    <div className="relative w-full overflow-hidden px-4 py-1.5 shrink-0">
      <div className="flex items-center gap-2 overflow-x-auto no-scrollbar scroll-smooth">
        <span className="text-[10px] font-mono font-bold text-slate-500 uppercase tracking-widest shrink-0 mr-1">
          SUGGESTIONS:
        </span>
        {actions.map((act, i) => {
          const Icon = act.icon;
          return (
            <button
              key={i}
              onClick={() => onSelectAction(act.prompt)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-medium whitespace-nowrap transition-all duration-300 hover:scale-105 active:scale-95 shadow-sm backdrop-blur-md hover:brightness-125 ${act.color}`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{act.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
