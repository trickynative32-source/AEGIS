import React from 'react';
import { Eye, Type, Volume2, Sparkles, Sliders, Contrast } from 'lucide-react';

interface AccessibilityBarProps {
  highContrast: boolean;
  largeFont: boolean;
  dyslexicFont: boolean;
  voiceFirst: boolean;
  simplifiedMode: boolean;
  onToggleHighContrast: () => void;
  onToggleLargeFont: () => void;
  onToggleDyslexicFont: () => void;
  onToggleVoiceFirst: () => void;
  onToggleSimplifiedMode: () => void;
}

export const AccessibilityBar: React.FC<AccessibilityBarProps> = ({
  highContrast,
  largeFont,
  dyslexicFont,
  voiceFirst,
  simplifiedMode,
  onToggleHighContrast,
  onToggleLargeFont,
  onToggleDyslexicFont,
  onToggleVoiceFirst,
  onToggleSimplifiedMode
}) => {
  return (
    <div className="flex items-center justify-between px-4 py-2 bg-slate-950/80 border-b border-slate-800 text-xs text-slate-300">
      <div className="flex items-center gap-2 font-semibold text-aura-cyan">
        <Sliders className="w-3.5 h-3.5" />
        <span className="hidden sm:inline">Inclusive Accessibility (SIH):</span>
      </div>

      <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
        <button
          onClick={onToggleHighContrast}
          className={`flex items-center gap-1 px-2.5 py-1 rounded-lg border transition ${
            highContrast ? 'bg-cyan-500 text-black border-cyan-400 font-bold' : 'bg-slate-900 border-slate-700 text-slate-300'
          }`}
          title="High contrast for visual clarity"
        >
          <Contrast className="w-3 h-3" />
          <span>High Contrast</span>
        </button>

        <button
          onClick={onToggleLargeFont}
          className={`flex items-center gap-1 px-2.5 py-1 rounded-lg border transition ${
            largeFont ? 'bg-cyan-500 text-black border-cyan-400 font-bold' : 'bg-slate-900 border-slate-700 text-slate-300'
          }`}
          title="Enlarge text"
        >
          <Type className="w-3 h-3" />
          <span>Large Text</span>
        </button>

        <button
          onClick={onToggleDyslexicFont}
          className={`flex items-center gap-1 px-2.5 py-1 rounded-lg border transition ${
            dyslexicFont ? 'bg-cyan-500 text-black border-cyan-400 font-bold' : 'bg-slate-900 border-slate-700 text-slate-300'
          }`}
          title="Dyslexia friendly font"
        >
          <span>OpenDyslexic</span>
        </button>

        <button
          onClick={onToggleVoiceFirst}
          className={`flex items-center gap-1 px-2.5 py-1 rounded-lg border transition ${
            voiceFirst ? 'bg-cyan-500 text-black border-cyan-400 font-bold' : 'bg-slate-900 border-slate-700 text-slate-300'
          }`}
          title="Voice-first automatic speech readout"
        >
          <Volume2 className="w-3 h-3" />
          <span>Voice-First</span>
        </button>

        <button
          onClick={onToggleSimplifiedMode}
          className={`flex items-center gap-1 px-2.5 py-1 rounded-lg border transition ${
            simplifiedMode ? 'bg-amber-500 text-black border-amber-400 font-bold' : 'bg-slate-900 border-slate-700 text-slate-300'
          }`}
          title="Simplified cognitive mode with low clutter"
        >
          <Sparkles className="w-3 h-3" />
          <span>Simplified UI</span>
        </button>
      </div>
    </div>
  );
};
