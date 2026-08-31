import React, { useState, useEffect } from 'react';
import { Bell, Plus, Trash2, CheckCircle, Clock, X, AlertCircle } from 'lucide-react';
import { ReminderItem } from '../types';

interface RemindersDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onRefreshTrigger?: number;
}

export const RemindersDrawer: React.FC<RemindersDrawerProps> = ({ isOpen, onClose, onRefreshTrigger }) => {
  const [reminders, setReminders] = useState<ReminderItem[]>([]);
  const [newText, setNewText] = useState<string>('');
  const [newTime, setNewTime] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const fetchReminders = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/reminders');
      if (res.ok) {
        const data = await res.json();
        setReminders(data.reminders || []);
      }
    } catch (e) {
      console.error('Failed to fetch reminders:', e);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchReminders();
    }
  }, [isOpen, onRefreshTrigger]);

  const handleAddReminder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newText.trim()) {
      setErrorMsg('Please specify what to remind you about.');
      return;
    }
    if (!newTime.trim()) {
      setErrorMsg('SIH Policy: When should I remind you? (Time is required).');
      return;
    }

    setIsLoading(true);
    setErrorMsg('');
    try {
      const res = await fetch('http://127.0.0.1:8000/api/reminders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: newText, time_str: newTime })
      });
      if (res.ok) {
        setNewText('');
        setNewTime('');
        fetchReminders();
      }
    } catch (e) {
      setErrorMsg('Failed to add reminder.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await fetch(`http://127.0.0.1:8000/api/reminders/${id}`, { method: 'DELETE' });
      fetchReminders();
    } catch (e) {
      console.error('Failed to delete reminder:', e);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-40 w-full sm:w-96 glass-panel border-l border-cyan-500/30 shadow-2xl p-5 flex flex-col justify-between animate-slide-left">
      <div>
        <div className="flex items-center justify-between pb-4 border-b border-slate-700/60 mb-4">
          <div className="flex items-center gap-2 text-aura-cyan">
            <Bell className="w-5 h-5" />
            <h2 className="text-base font-bold text-slate-100">User-Defined Reminders</h2>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Add Reminder Form */}
        <form onSubmit={handleAddReminder} className="space-y-3 mb-6 p-3.5 rounded-xl bg-slate-900/60 border border-slate-700/60">
          <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Set New Reminder</h3>
          <input
            type="text"
            placeholder="Reminder task (e.g. Submit assignment)"
            value={newText}
            onChange={(e) => setNewText(e.target.value)}
            className="w-full px-3 py-2 text-xs rounded-lg bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-aura-cyan"
          />
          <input
            type="text"
            placeholder="When? (e.g. tomorrow at 5 PM, in 10 mins)"
            value={newTime}
            onChange={(e) => setNewTime(e.target.value)}
            className="w-full px-3 py-2 text-xs rounded-lg bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-aura-cyan"
          />
          {errorMsg && (
            <div className="flex items-center gap-1.5 text-xs text-rose-400">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>{errorMsg}</span>
            </div>
          )}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-xs shadow-md transition active:scale-95 disabled:opacity-50"
          >
            <Plus className="w-4 h-4" />
            <span>Create Reminder</span>
          </button>
        </form>

        {/* Reminders List */}
        <div className="space-y-2.5 max-h-[50vh] overflow-y-auto pr-1">
          {reminders.length === 0 ? (
            <div className="text-center py-8 text-slate-500 text-xs">
              No active reminders. Speak naturally: "Remind me tomorrow at 5 PM to submit assignment"
            </div>
          ) : (
            reminders.map((r) => (
              <div
                key={r.id}
                className="flex items-start justify-between p-3 rounded-xl glass-card hover:border-cyan-500/40 transition group"
              >
                <div className="flex items-start gap-2.5">
                  <div className="p-1.5 rounded-lg bg-cyan-950/80 text-aura-cyan shrink-0 mt-0.5">
                    <Clock className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-200">{r.text}</p>
                    <p className="text-[11px] text-cyan-400 font-mono mt-0.5">{r.time}</p>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(r.id)}
                  className="p-1 text-slate-500 hover:text-rose-400 rounded transition opacity-80 group-hover:opacity-100"
                  title="Cancel Reminder"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="pt-4 border-t border-slate-700/60 text-[11px] text-slate-500 text-center">
        Reminders are strictly user-defined & synced to real Windows clock.
      </div>
    </div>
  );
};
