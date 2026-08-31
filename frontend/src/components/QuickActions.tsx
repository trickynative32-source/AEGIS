import React from 'react';
import { Clock, Palette, Music, Navigation, FileCode, MapPin, Mic, LogOut, Eye, Search } from 'lucide-react';

interface QuickActionsProps {
  onSelectAction: (prompt: string) => void;
}

export const QuickActions: React.FC<QuickActionsProps> = ({ onSelectAction }) => {
  const actions = [
    { label: 'Time & Date', prompt: 'What time is it?', icon: Clock, color: 'text-cyan-400 border-cyan-500/30 bg-cyan-950/40' },
    { label: 'Draw House in Paint', prompt: 'Open Paint and draw a house', icon: Palette, color: 'text-amber-400 border-amber-500/30 bg-amber-950/40' },
    { label: 'Play Believer', prompt: 'Play Believer by Imagine Dragons', icon: Music, color: 'text-rose-400 border-rose-500/30 bg-rose-950/40' },
    { label: 'Directions to Airport', prompt: 'Show directions from my current location to Bangalore Airport', icon: Navigation, color: 'text-blue-400 border-blue-500/30 bg-blue-950/40' },
    { label: 'Python Calculator', prompt: 'Create a Python calculator on my Desktop', icon: FileCode, color: 'text-emerald-400 border-emerald-500/30 bg-emerald-950/40' },
    { label: 'Where is the clock?', prompt: 'Where is the clock?', icon: Search, color: 'text-purple-400 border-purple-500/30 bg-purple-950/40' },
    { label: 'Detect Person', prompt: 'Is there a person in front of me?', icon: Eye, color: 'text-teal-400 border-teal-500/30 bg-teal-950/40' },
    { label: 'Start Dictation', prompt: 'Start dictation', icon: Mic, color: 'text-yellow-400 border-yellow-500/30 bg-yellow-950/40' },
    { label: 'Goodbye', prompt: 'Goodbye', icon: LogOut, color: 'text-red-400 border-red-500/30 bg-red-950/40' },
  ];

  return (
    <div className="flex items-center gap-2 overflow-x-auto py-2 px-4 no-scrollbar">
      <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider shrink-0 mr-1">
        Quick Prompts:
      </span>
      {actions.map((act, i) => {
        const Icon = act.icon;
        return (
          <button
            key={i}
            onClick={() => onSelectAction(act.prompt)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-medium whitespace-nowrap transition-all hover:scale-105 active:scale-95 shadow-sm ${act.color}`}
          >
            <Icon className="w-3.5 h-3.5" />
            <span>{act.label}</span>
          </button>
        );
      })}
    </div>
  );
};
