import React, { useState } from 'react';
import { Sparkles, Eye, Mic, Brain, ArrowRight, ShieldCheck } from 'lucide-react';

interface IntroModalProps {
  isOpen: boolean;
  onEnter: () => void;
  onOpenAuth: () => void;
  userName?: string;
}

export const IntroModal: React.FC<IntroModalProps> = ({
  isOpen,
  onEnter,
  onOpenAuth,
  userName
}) => {
  const [dontShowAgain, setDontShowAgain] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleEnterWorkspace = () => {
    if (dontShowAgain) {
      localStorage.setItem('aegis_intro_dismissed', 'true');
    }
    onEnter();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-xl animate-fade-in">
      {/* Ambient background soft glow orbs */}
      <div className="absolute w-96 h-96 rounded-full bg-cyan-600/15 blur-[120px] pointer-events-none -top-10 -left-10 animate-pulse" />
      <div className="absolute w-96 h-96 rounded-full bg-indigo-600/15 blur-[120px] pointer-events-none -bottom-10 -right-10 animate-pulse" />

      <div className="relative w-full max-w-2xl bg-slate-900/90 border border-slate-700/60 rounded-3xl p-8 sm:p-10 shadow-2xl shadow-cyan-950/40 text-slate-100 overflow-hidden backdrop-blur-2xl">
        {/* Top luminous ring badge */}
        <div className="flex justify-center mb-6">
          <div className="relative">
            <div className="w-20 h-20 rounded-3xl bg-gradient-to-tr from-cyan-500 via-indigo-500 to-purple-500 p-0.5 shadow-xl shadow-cyan-500/30">
              <div className="w-full h-full bg-slate-950 rounded-[22px] flex items-center justify-center">
                <Sparkles className="w-10 h-10 text-cyan-400 animate-pulse" />
              </div>
            </div>
            <span className="absolute -bottom-1 -right-1 flex h-4 w-4">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-4 w-4 bg-emerald-500 border-2 border-slate-950" />
            </span>
          </div>
        </div>

        {/* Title & Philosophy */}
        <div className="text-center space-y-2 mb-8">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-950/80 border border-cyan-500/30 text-xs font-mono text-cyan-400 tracking-wider uppercase font-semibold">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Problem Statement SIH26204</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
            Welcome to <span className="bg-gradient-to-r from-cyan-400 to-indigo-400 bg-clip-text text-transparent">AEGIS</span>
          </h1>

          <p className="text-xs sm:text-sm text-slate-400 max-w-lg mx-auto font-medium leading-relaxed">
            Assisted Executive Guidance & Intelligence System — an organic, voice-first companion with continuous spatial perception and personal memory.
          </p>

          {userName && userName !== 'Guest Explorer' && (
            <p className="text-xs font-semibold text-emerald-400 pt-1">
              Welcome back, {userName}! Your profile and environmental memories are loaded.
            </p>
          )}
        </div>

        {/* 3 Core Pillars */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-8">
          <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800/80 hover:border-cyan-500/30 transition shadow-sm space-y-2">
            <div className="w-8 h-8 rounded-xl bg-cyan-950/80 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
              <Eye className="w-4 h-4" />
            </div>
            <h2 className="text-xs font-bold text-slate-200">Spatial Vision</h2>
            <p className="text-[11px] text-slate-400 leading-normal">
              Real-time YOLOv5m object detection & NVIDIA LocateAnything-3B grounding.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800/80 hover:border-indigo-500/30 transition shadow-sm space-y-2">
            <div className="w-8 h-8 rounded-xl bg-indigo-950/80 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
              <Mic className="w-4 h-4" />
            </div>
            <h2 className="text-xs font-bold text-slate-200">Conversational Voice</h2>
            <p className="text-[11px] text-slate-400 leading-normal">
              Fluid speaking presence, instant voice barge-in, and natural auditory pacing.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800/80 hover:border-purple-500/30 transition shadow-sm space-y-2">
            <div className="w-8 h-8 rounded-xl bg-purple-950/80 border border-purple-500/40 flex items-center justify-center text-purple-400">
              <Brain className="w-4 h-4" />
            </div>
            <h2 className="text-xs font-bold text-slate-200">Personal Memory</h2>
            <p className="text-[11px] text-slate-400 leading-normal">
              Persistent memory of who you are, daily routines, habits, and lost items.
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="space-y-3">
          <div className="flex flex-col sm:flex-row items-center gap-3">
            {/* 1-Click Google Sign In */}
            <button
              onClick={() => {
                onOpenAuth();
              }}
              className="w-full sm:w-1/2 flex items-center justify-center gap-2.5 px-5 py-3.5 rounded-2xl bg-white hover:bg-slate-100 text-slate-900 font-semibold text-xs tracking-wide transition shadow-lg hover:shadow-white/20 active:scale-95"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"
                />
                <path
                  fill="#34A853"
                  d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15z"
                />
                <path
                  fill="#EA4335"
                  d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"
                />
              </svg>
              <span>Sign In with Google</span>
            </button>

            {/* Enter Workspace Direct */}
            <button
              onClick={handleEnterWorkspace}
              className="w-full sm:w-1/2 flex items-center justify-center gap-2 px-5 py-3.5 rounded-2xl bg-gradient-to-r from-cyan-600 via-indigo-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold text-xs tracking-wide uppercase transition shadow-lg shadow-cyan-950/60 active:scale-95 border border-cyan-400/40"
            >
              <span>Enter Workspace</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Dismiss preference */}
          <div className="flex items-center justify-center pt-2">
            <label className="flex items-center gap-2 cursor-pointer text-[11px] text-slate-400 hover:text-slate-300 select-none">
              <input
                type="checkbox"
                checked={dontShowAgain}
                onChange={(e) => setDontShowAgain(e.target.checked)}
                className="w-3.5 h-3.5 rounded bg-slate-950 border-slate-700 text-cyan-500 focus:ring-0 focus:ring-offset-0 cursor-pointer"
              />
              <span>Don't show this intro on next startup</span>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
};
