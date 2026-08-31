import React, { useState, useEffect } from 'react';
import { Workflow, Sparkles, Trash2, X, Check, ArrowRight } from 'lucide-react';
import { RoutineItem, RoutineSuggestion } from '../types';
import { wsService } from '../services/websocket';

interface RoutinesDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const RoutinesDrawer: React.FC<RoutinesDrawerProps> = ({ isOpen, onClose }) => {
  const [routines, setRoutines] = useState<RoutineItem[]>([]);
  const [suggestions, setSuggestions] = useState<RoutineSuggestion[]>([]);

  const fetchRoutines = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/routines');
      if (res.ok) {
        const data = await res.json();
        setRoutines(data.routines || []);
        setSuggestions(data.suggestions || []);
      }
    } catch (e) {
      console.error('Failed to fetch routines:', e);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchRoutines();
    }
  }, [isOpen]);

  const handleExecuteSuggestion = (target: string) => {
    wsService.sendMessage(`Open ${target}`);
  };

  const handleClearAll = async () => {
    await fetch('http://127.0.0.1:8000/api/routines', { method: 'DELETE' });
    fetchRoutines();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-40 w-full sm:w-96 glass-panel border-l border-cyan-500/30 shadow-2xl p-5 flex flex-col justify-between animate-slide-left">
      <div>
        <div className="flex items-center justify-between pb-4 border-b border-slate-700/60 mb-4">
          <div className="flex items-center gap-2 text-aura-purple">
            <Workflow className="w-5 h-5" />
            <h2 className="text-base font-bold text-slate-100">Learned Routines (SIH)</h2>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Proactive Suggestions */}
        {suggestions.length > 0 && (
          <div className="mb-6 space-y-2">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-aura-amber uppercase tracking-wider">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Proactive Habit Suggestions</span>
            </div>
            {suggestions.map((s) => (
              <div key={s.id} className="p-3 rounded-xl bg-amber-950/40 border border-amber-500/40 space-y-2">
                <p className="text-xs text-amber-200">{s.message}</p>
                <button
                  onClick={() => handleExecuteSuggestion(s.target)}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-amber-500/20 hover:bg-amber-500/40 border border-amber-500/40 text-amber-300 text-xs font-medium transition active:scale-95"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>Yes, open {s.target}</span>
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Routines Table */}
        <div className="space-y-2 max-h-[55vh] overflow-y-auto pr-1">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Tracked Frequency</h3>
          {routines.length === 0 ? (
            <div className="text-center py-8 text-slate-500 text-xs">
              No routines learned yet. As you use applications throughout the day, AEGIS learns usage frequency safely.
            </div>
          ) : (
            routines.map((r) => (
              <div key={r.id} className="flex items-center justify-between p-2.5 rounded-xl glass-card text-xs">
                <div>
                  <span className="font-semibold text-slate-200">{r.target}</span>
                  <span className="text-slate-400 text-[11px] ml-2">({r.time_of_day})</span>
                </div>
                <span className="px-2 py-0.5 rounded-full bg-cyan-950/80 border border-cyan-500/30 text-aura-cyan text-[10px] font-mono font-bold">
                  {r.frequency}x
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="pt-4 border-t border-slate-700/60 flex items-center justify-between">
        <button
          onClick={handleClearAll}
          className="flex items-center gap-1.5 text-xs text-rose-400 hover:text-rose-300 transition"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>Clear Learned Routines</span>
        </button>
      </div>
    </div>
  );
};
