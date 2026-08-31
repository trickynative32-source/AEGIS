import React, { useState, useEffect } from 'react';
import { Eye, MapPin, Trash2, X, RefreshCw, Layers } from 'lucide-react';
import { VisualMemoryItem } from '../types';

interface VisualMemoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const VisualMemoryDrawer: React.FC<VisualMemoryDrawerProps> = ({ isOpen, onClose }) => {
  const [memories, setMemories] = useState<VisualMemoryItem[]>([]);

  const fetchVisualMemories = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/visual-memories');
      if (res.ok) {
        const data = await res.json();
        setMemories(data.visual_memories || []);
      }
    } catch (e) {
      console.error('Failed to fetch visual memories:', e);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchVisualMemories();
    }
  }, [isOpen]);

  const handleClear = async () => {
    await fetch('http://127.0.0.1:8000/api/visual-memories', { method: 'DELETE' });
    fetchVisualMemories();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-40 w-full sm:w-96 glass-panel border-l border-cyan-500/30 shadow-2xl p-5 flex flex-col justify-between animate-slide-left">
      <div>
        <div className="flex items-center justify-between pb-4 border-b border-slate-700/60 mb-4">
          <div className="flex items-center gap-2 text-aura-cyan">
            <Layers className="w-5 h-5" />
            <h2 className="text-base font-bold text-slate-100">Environmental Visual Memory</h2>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition">
            <X className="w-4 h-4" />
          </button>
        </div>

        <p className="text-xs text-slate-400 mb-4">
          AEGIS maintains semantic short-term spatial memory of surroundings observed by the camera without storing raw video.
        </p>

        {/* Visual Memory Items */}
        <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
          {memories.length === 0 ? (
            <div className="text-center py-8 text-slate-500 text-xs">
              No visual observations yet. Turn on camera and ask "What do you see?" or "Where is my laptop?"
            </div>
          ) : (
            memories.map((m) => (
              <div key={m.id} className="p-3 rounded-xl glass-card space-y-1.5 border-l-2 border-l-cyan-400">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-100 capitalize">{m.object}</span>
                  <span className="text-[10px] text-cyan-400 font-mono">{(m.confidence * 100).toFixed(0)}% conf</span>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-slate-300">
                  <MapPin className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                  <span>
                    {m.location_context}
                    {m.spatial_relationship ? ` (${m.spatial_relationship})` : ''}
                  </span>
                </div>
                <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-700/40">
                  <span>Room: {m.room}</span>
                  <span>Last seen: {m.last_seen}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="pt-4 border-t border-slate-700/60 flex items-center justify-between">
        <button onClick={handleClear} className="flex items-center gap-1.5 text-xs text-rose-400 hover:text-rose-300 transition">
          <Trash2 className="w-3.5 h-3.5" />
          <span>Clear Visual Memory</span>
        </button>
        <button onClick={fetchVisualMemories} className="flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 transition">
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>
    </div>
  );
};
