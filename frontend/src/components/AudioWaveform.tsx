import React from 'react';
import { AssistantState } from '../types';

interface AudioWaveformProps {
  state: AssistantState;
  isPushToTalkActive: boolean;
}

export const AudioWaveform: React.FC<AudioWaveformProps> = ({ state, isPushToTalkActive }) => {
  const isActive = isPushToTalkActive || state === 'LISTENING' || state === 'SPEAKING' || state === 'THINKING';
  const bars = [16, 28, 42, 24, 38, 54, 30, 48, 20, 36, 50, 22];

  let colorClass = 'bg-slate-600';
  if (isPushToTalkActive || state === 'LISTENING') {
    colorClass = 'bg-aura-rose shadow-[0_0_8px_#f43f5e]';
  } else if (state === 'SPEAKING') {
    colorClass = 'bg-aura-cyan shadow-[0_0_8px_#00f0ff]';
  } else if (state === 'THINKING' || state === 'EXECUTING') {
    colorClass = 'bg-aura-amber shadow-[0_0_8px_#ffb300]';
  }

  return (
    <div className="flex items-center justify-center gap-1.5 h-10 px-4 py-1">
      {bars.map((height, idx) => {
        const dynamicHeight = isActive
          ? Math.max(12, Math.floor(height * (0.6 + 0.4 * Math.sin((idx + Date.now() / 150)))))
          : 6;

        return (
          <div
            key={idx}
            className={`w-1.5 rounded-full transition-all duration-150 ${colorClass}`}
            style={{
              height: `${dynamicHeight}px`,
              animation: isActive ? `wave 1s ease-in-out infinite ${idx * 0.08}s` : 'none'
            }}
          />
        );
      })}
    </div>
  );
};
