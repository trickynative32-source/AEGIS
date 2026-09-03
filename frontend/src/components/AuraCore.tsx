import React from 'react';
import { Sparkles, Mic, Volume2, Cpu, Eye } from 'lucide-react';
import { AssistantState } from '../types';

interface AuraCoreProps {
  state: AssistantState;
  isPushToTalkActive: boolean;
  onCoreClick: () => void;
  latestAssistantUtterance?: string;
  isCompact?: boolean;
}

export const AuraCore: React.FC<AuraCoreProps> = ({
  state,
  isPushToTalkActive,
  onCoreClick,
  latestAssistantUtterance,
  isCompact = false
}) => {
  // Determine color and glow styles based on organic assistant state
  const getStateMeta = () => {
    if (isPushToTalkActive || state === 'LISTENING') {
      return {
        label: 'Listening...',
        glow: 'shadow-[0_0_90px_rgba(16,185,129,0.45)]',
        border: 'border-emerald-400/80',
        ringGradient: 'from-emerald-400 via-teal-300 to-cyan-500',
        badgeBg: 'bg-emerald-950/80 border-emerald-500/60 text-emerald-300',
        icon: Mic,
        iconColor: 'text-emerald-300',
        pulseClass: 'animate-pulse'
      };
    }

    if (state === 'THINKING' || state === 'EXECUTING') {
      return {
        label: 'Synthesizing...',
        glow: 'shadow-[0_0_90px_rgba(245,158,11,0.45)]',
        border: 'border-amber-400/80',
        ringGradient: 'from-amber-400 via-orange-400 to-purple-500',
        badgeBg: 'bg-amber-950/80 border-amber-500/60 text-amber-300',
        icon: Cpu,
        iconColor: 'text-amber-300',
        pulseClass: 'animate-spin'
      };
    }

    if (state === 'SPEAKING') {
      return {
        label: 'Transmitting...',
        glow: 'shadow-[0_0_100px_rgba(6,182,212,0.6)]',
        border: 'border-cyan-400',
        ringGradient: 'from-cyan-400 via-indigo-400 to-fuchsia-400',
        badgeBg: 'bg-cyan-950/80 border-cyan-500/60 text-cyan-300',
        icon: Volume2,
        iconColor: 'text-cyan-300',
        pulseClass: 'animate-pulse'
      };
    }

    return {
      label: 'Mindful & Attuned',
      glow: 'shadow-[0_0_70px_rgba(99,102,241,0.3)]',
      border: 'border-indigo-400/50',
      ringGradient: 'from-cyan-500 via-indigo-500 to-purple-500',
      badgeBg: 'bg-slate-900/80 border-slate-700/70 text-slate-300',
      icon: Sparkles,
      iconColor: 'text-cyan-300',
      pulseClass: ''
    };
  };

  const meta = getStateMeta();
  const Icon = meta.icon;

  const orbSizeClass = isCompact 
    ? 'w-24 h-24 sm:w-28 sm:h-28' 
    : 'w-36 h-36 sm:w-44 sm:h-44';

  const containerPadding = isCompact ? 'py-2' : 'py-5';

  return (
    <div className={`relative flex flex-col items-center justify-center ${containerPadding} px-4 select-none overflow-hidden transition-all duration-500`}>
      {/* Background celestial radial ambient nebula */}
      <div
        className={`absolute rounded-full blur-[100px] transition-all duration-700 pointer-events-none opacity-40 ${
          isCompact ? 'w-48 h-48' : 'w-80 h-80'
        } ${
          state === 'SPEAKING'
            ? 'bg-cyan-500/40 scale-125'
            : state === 'LISTENING'
            ? 'bg-emerald-500/40 scale-125'
            : state === 'THINKING'
            ? 'bg-amber-500/40 scale-110'
            : 'bg-indigo-600/30 scale-100'
        }`}
      />

      {/* Interactive Core Hologram Orb */}
      <button
        onClick={onCoreClick}
        title={state === 'SPEAKING' ? 'Tap to interrupt speech' : 'Tap to speak'}
        className="group relative cursor-pointer focus:outline-none transition-transform duration-300 active:scale-95 hover:scale-105"
      >
        {/* Expanding organic ripples when active */}
        {(state === 'SPEAKING' || state === 'LISTENING' || isPushToTalkActive) && (
          <>
            <span
              className="absolute -inset-4 rounded-full border border-cyan-400/40 animate-ping opacity-60 pointer-events-none"
            />
            <span
              className="absolute -inset-8 rounded-full border border-indigo-400/25 animate-pulse opacity-40 pointer-events-none"
            />
          </>
        )}

        {/* Outer Rotating Gradient Ring */}
        <div
          className={`${orbSizeClass} rounded-full p-1 bg-gradient-to-tr ${meta.ringGradient} ${meta.glow} transition-all duration-500 flex items-center justify-center animate-spin-slow`}
        >
          {/* Middle Translucent Layer with Counter Rotation */}
          <div className="w-full h-full rounded-full bg-slate-950/80 backdrop-blur-md p-2 flex items-center justify-center border border-white/10">
            {/* Innermost Radiant Core */}
            <div
              className={`w-full h-full rounded-full bg-gradient-to-br from-slate-900 via-slate-950 to-black flex flex-col items-center justify-center border ${meta.border} transition-all duration-500 shadow-inner`}
            >
              <Icon className={`${isCompact ? 'w-6 h-6' : 'w-9 h-9'} ${meta.iconColor} ${meta.pulseClass} transition-transform duration-300 drop-shadow-[0_0_10px_rgba(6,182,212,0.6)]`} />

              {/* Dynamic Sound Wave frequency bars inside core when speaking */}
              {state === 'SPEAKING' && (
                <div className="flex items-center gap-1 mt-1.5 h-3">
                  <span className="w-1 bg-cyan-400 rounded-full animate-bounce [animation-delay:0ms] h-2.5" />
                  <span className="w-1 bg-teal-300 rounded-full animate-bounce [animation-delay:120ms] h-4" />
                  <span className="w-1 bg-indigo-400 rounded-full animate-bounce [animation-delay:240ms] h-3" />
                  <span className="w-1 bg-fuchsia-400 rounded-full animate-bounce [animation-delay:360ms] h-4.5" />
                  <span className="w-1 bg-cyan-300 rounded-full animate-bounce [animation-delay:480ms] h-2" />
                </div>
              )}
            </div>
          </div>
        </div>
      </button>

      {/* State Badge */}
      <div className="mt-3 flex items-center gap-2">
        <div
          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-[11px] font-mono font-medium backdrop-blur-md transition-all duration-300 shadow-sm ${meta.badgeBg}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
          <span>{meta.label}</span>
        </div>
      </div>

      {/* Floating Spoken Subtitle Transmission */}
      {latestAssistantUtterance && !isCompact && (
        <div className="mt-3 max-w-xl text-center px-4 animate-fade-in">
          <p className="text-xs sm:text-sm text-slate-200 font-medium italic leading-relaxed bg-slate-950/70 border border-cyan-500/30 backdrop-blur-xl px-4 py-2.5 rounded-2xl shadow-lg shadow-cyan-950/30">
            "{latestAssistantUtterance}"
          </p>
        </div>
      )}
    </div>
  );
};
