import React from 'react';
import { Sparkles, Mic, Volume2, Cpu, Eye } from 'lucide-react';
import { AssistantState } from '../types';

interface AuraCoreProps {
  state: AssistantState;
  isPushToTalkActive: boolean;
  onCoreClick: () => void;
  latestAssistantUtterance?: string;
  onQuickAction?: (prompt: string) => void;
}

export const AuraCore: React.FC<AuraCoreProps> = ({
  state,
  isPushToTalkActive,
  onCoreClick,
  latestAssistantUtterance,
  onQuickAction
}) => {
  // Determine color and glow styles based on organic assistant state
  const getStateMeta = () => {
    if (isPushToTalkActive || state === 'LISTENING') {
      return {
        label: 'Listening to your voice...',
        glow: 'shadow-[0_0_80px_rgba(16,185,129,0.4)]',
        border: 'border-emerald-400/60',
        ringGradient: 'from-emerald-400 via-teal-300 to-cyan-500',
        badgeBg: 'bg-emerald-950/80 border-emerald-500/50 text-emerald-300',
        icon: Mic,
        iconColor: 'text-emerald-400',
        pulseClass: 'animate-ping'
      };
    }

    if (state === 'THINKING' || state === 'EXECUTING') {
      return {
        label: 'Reflecting & Processing...',
        glow: 'shadow-[0_0_80px_rgba(245,158,11,0.4)]',
        border: 'border-amber-400/60',
        ringGradient: 'from-amber-400 via-orange-400 to-purple-500',
        badgeBg: 'bg-amber-950/80 border-amber-500/50 text-amber-300',
        icon: Cpu,
        iconColor: 'text-amber-400',
        pulseClass: 'animate-spin'
      };
    }

    if (state === 'SPEAKING') {
      return {
        label: 'Speaking...',
        glow: 'shadow-[0_0_90px_rgba(6,182,212,0.5)]',
        border: 'border-cyan-400/80',
        ringGradient: 'from-cyan-400 via-indigo-400 to-fuchsia-400',
        badgeBg: 'bg-cyan-950/80 border-cyan-500/50 text-cyan-300',
        icon: Volume2,
        iconColor: 'text-cyan-400',
        pulseClass: 'animate-pulse'
      };
    }

    return {
      label: 'Mindful & Attuned',
      glow: 'shadow-[0_0_60px_rgba(99,102,241,0.25)]',
      border: 'border-indigo-400/40',
      ringGradient: 'from-cyan-500 via-indigo-500 to-purple-500',
      badgeBg: 'bg-slate-900/80 border-slate-700/60 text-slate-300',
      icon: Sparkles,
      iconColor: 'text-indigo-400',
      pulseClass: ''
    };
  };

  const meta = getStateMeta();
  const Icon = meta.icon;

  return (
    <div className="relative flex flex-col items-center justify-center py-6 px-4 select-none overflow-hidden">
      {/* Background radial ambient aura */}
      <div
        className={`absolute w-80 h-80 rounded-full blur-[90px] transition-all duration-700 pointer-events-none opacity-40 ${
          state === 'SPEAKING'
            ? 'bg-cyan-500/30 scale-125'
            : state === 'LISTENING'
            ? 'bg-emerald-500/30 scale-125'
            : state === 'THINKING'
            ? 'bg-amber-500/30 scale-110'
            : 'bg-indigo-600/20 scale-100'
        }`}
      />

      {/* Interactive Core Hologram Orb */}
      <button
        onClick={onCoreClick}
        title={state === 'SPEAKING' ? 'Tap to pause speaking' : 'Tap to speak'}
        className="group relative cursor-pointer focus:outline-none transition-transform duration-300 active:scale-95"
      >
        {/* Outermost expanding sound wave ripples when speaking or listening */}
        {(state === 'SPEAKING' || state === 'LISTENING' || isPushToTalkActive) && (
          <>
            <span
              className={`absolute -inset-4 rounded-full border border-cyan-400/30 animate-ping opacity-60 pointer-events-none`}
            />
            <span
              className={`absolute -inset-8 rounded-full border border-indigo-400/20 animate-pulse opacity-40 pointer-events-none`}
            />
          </>
        )}

        {/* Outer Rotating Gradient Ring */}
        <div
          className={`w-36 h-36 sm:w-40 sm:h-40 rounded-full p-1 bg-gradient-to-tr ${meta.ringGradient} ${meta.glow} transition-all duration-500 flex items-center justify-center`}
        >
          {/* Middle Translucent Layer */}
          <div className="w-full h-full rounded-full bg-slate-950/80 backdrop-blur-md p-2 flex items-center justify-center border border-white/10">
            {/* Innermost Radiant Core */}
            <div
              className={`w-full h-full rounded-full bg-gradient-to-br from-slate-900 via-slate-950 to-black flex flex-col items-center justify-center border ${meta.border} transition-all duration-500 group-hover:scale-105`}
            >
              <Icon className={`w-8 h-8 ${meta.iconColor} ${meta.pulseClass} transition-transform duration-300`} />

              {/* Dynamic Sound Wave frequency bars inside core when speaking */}
              {state === 'SPEAKING' && (
                <div className="flex items-center gap-1 mt-1.5 h-3">
                  <span className="w-1 bg-cyan-400 rounded-full animate-bounce [animation-delay:0ms] h-3" />
                  <span className="w-1 bg-teal-300 rounded-full animate-bounce [animation-delay:150ms] h-4" />
                  <span className="w-1 bg-indigo-400 rounded-full animate-bounce [animation-delay:300ms] h-2.5" />
                  <span className="w-1 bg-fuchsia-400 rounded-full animate-bounce [animation-delay:450ms] h-3.5" />
                </div>
              )}
            </div>
          </div>
        </div>
      </button>

      {/* State Badge */}
      <div className="mt-4 flex items-center gap-2">
        <div
          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-mono font-medium backdrop-blur-md transition-all duration-300 ${meta.badgeBg}`}
        >
          <span className="w-2 h-2 rounded-full bg-current animate-pulse" />
          <span>{meta.label}</span>
        </div>
      </div>

      {/* Live Speaking Subtitle Stream (gives the user the vibe that AEGIS is talking) */}
      {latestAssistantUtterance && (
        <div className="mt-3 max-w-xl text-center px-4">
          <p className="text-xs sm:text-sm text-slate-300/90 font-medium italic leading-relaxed bg-slate-950/60 border border-slate-800/80 backdrop-blur-md px-4 py-2 rounded-2xl shadow-sm">
            "{latestAssistantUtterance}"
          </p>
        </div>
      )}

      {/* Gentle Suggestion Chips under Core */}
      {onQuickAction && (
        <div className="mt-4 flex items-center gap-2 overflow-x-auto max-w-lg no-scrollbar py-1">
          <button
            onClick={() => onQuickAction('Describe what you see in front of the camera')}
            className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-slate-700/60 hover:border-cyan-500/40 text-[11px] text-slate-300 transition shrink-0"
          >
            <Eye className="w-3 h-3 text-cyan-400" />
            <span>Look at Surroundings</span>
          </button>

          <button
            onClick={() => onQuickAction('Where is my phone?')}
            className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-slate-700/60 hover:border-purple-500/40 text-[11px] text-slate-300 transition shrink-0"
          >
            <Sparkles className="w-3 h-3 text-purple-400" />
            <span>Where is my phone?</span>
          </button>

          <button
            onClick={() => onQuickAction('What is my schedule today?')}
            className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-slate-700/60 hover:border-amber-500/40 text-[11px] text-slate-300 transition shrink-0"
          >
            <Sparkles className="w-3 h-3 text-amber-400" />
            <span>Today's Schedule</span>
          </button>
        </div>
      )}
    </div>
  );
};
