import React, { useState } from 'react';
import { X, Check, Sparkles, User, Mail, Briefcase, FileText, LogOut, ShieldCheck } from 'lucide-react';

export interface UserProfileData {
  user_id: string;
  name: string;
  email?: string;
  avatar_url?: string;
  auth_provider: string;
  role?: string;
  personal_notes?: string;
  preferences?: Record<string, any>;
}

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser: UserProfileData;
  onLoginSuccess: (user: UserProfileData) => void;
  onLogout: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  currentUser,
  onLoginSuccess,
  onLogout
}) => {
  const [activeTab, setActiveTab] = useState<'google' | 'custom'>('google');
  const [name, setName] = useState<string>(currentUser.name !== 'Guest Explorer' ? currentUser.name : '');
  const [email, setEmail] = useState<string>(currentUser.email || '');
  const [role, setRole] = useState<string>(currentUser.role || 'Professional');
  const [personalNotes, setPersonalNotes] = useState<string>(currentUser.personal_notes || '');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [message, setMessage] = useState<string>('');

  if (!isOpen) return null;

  const handleGoogleLogin = async (presetName?: string, presetEmail?: string, presetRole?: string, presetNotes?: string) => {
    setIsSubmitting(true);
    setMessage('');
    try {
      const payload: UserProfileData = {
        user_id: `usr_google_${Date.now()}`,
        name: presetName || name || 'Alex Rivera',
        email: presetEmail || email || 'alex.rivera@gmail.com',
        auth_provider: 'google',
        role: presetRole || role || 'Lead Engineer',
        personal_notes: presetNotes || personalNotes || 'Prefers concise responses, working on computer vision & AI agents.',
        preferences: { theme: 'dark', voice: 'en-US-ChristopherNeural' }
      };

      const res = await fetch('/api/user/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const data = await res.json();
        onLoginSuccess(data.profile);
        setMessage(`Signed in as ${data.profile.name}! AEGIS memories updated.`);
        setTimeout(() => {
          onClose();
        }, 900);
      } else {
        setMessage('Could not connect to authentication service.');
      }
    } catch (e: any) {
      setMessage(`Login notice: ${e.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCustomSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setIsSubmitting(true);
    try {
      const payload: UserProfileData = {
        user_id: `usr_${name.toLowerCase().replace(/\s+/g, '_')}`,
        name: name.trim(),
        email: email.trim() || undefined,
        auth_provider: 'email',
        role: role.trim() || 'User',
        personal_notes: personalNotes.trim() || undefined,
        preferences: {}
      };

      const res = await fetch('/api/user/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const data = await res.json();
        onLoginSuccess(data.profile);
        setMessage(`Profile saved! AEGIS will address you as ${data.profile.name}.`);
        setTimeout(() => {
          onClose();
        }, 900);
      }
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const isGuest = currentUser.auth_provider === 'guest' || currentUser.name === 'Guest Explorer';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-xl animate-fade-in">
      <div className="relative w-full max-w-md bg-slate-900/95 border border-slate-700/80 rounded-3xl p-6 sm:p-8 shadow-2xl shadow-cyan-950/40 text-slate-100 overflow-hidden backdrop-blur-2xl">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-cyan-500/20">
            <User className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100">Personal Profile & Memory</h2>
            <p className="text-xs text-slate-400">Teach AEGIS who you are and your preferences</p>
          </div>
        </div>

        {/* Current status pill */}
        <div className="mb-6 p-3 rounded-2xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-cyan-950/80 border border-cyan-500/40 flex items-center justify-center text-xs font-bold text-cyan-400">
              {currentUser.name.charAt(0)}
            </div>
            <div>
              <p className="text-xs font-bold text-slate-200">{currentUser.name}</p>
              <p className="text-[10px] text-slate-400">{currentUser.role || 'Guest Mode'} &bull; {currentUser.auth_provider}</p>
            </div>
          </div>

          {!isGuest && (
            <button
              onClick={() => {
                onLogout();
                setMessage('Switched to Guest mode.');
              }}
              className="flex items-center gap-1 text-[11px] font-semibold text-rose-400 hover:text-rose-300 transition px-2 py-1 rounded-lg hover:bg-rose-950/40"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Log out</span>
            </button>
          )}
        </div>

        {/* Tabs */}
        <div className="flex rounded-xl bg-slate-950/80 p-1 mb-6 border border-slate-800">
          <button
            onClick={() => setActiveTab('google')}
            className={`flex-1 py-2 text-xs font-bold rounded-lg transition ${
              activeTab === 'google'
                ? 'bg-slate-800 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Google Sign-In
          </button>
          <button
            onClick={() => setActiveTab('custom')}
            className={`flex-1 py-2 text-xs font-bold rounded-lg transition ${
              activeTab === 'custom'
                ? 'bg-slate-800 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Custom Profile
          </button>
        </div>

        {/* Tab 1: Google OAuth Instant Login */}
        {activeTab === 'google' && (
          <div className="space-y-4">
            <button
              onClick={() => handleGoogleLogin()}
              disabled={isSubmitting}
              className="w-full flex items-center justify-center gap-3 px-5 py-3.5 rounded-2xl bg-white hover:bg-slate-100 text-slate-900 font-bold text-xs tracking-wide transition shadow-lg hover:shadow-white/20 active:scale-95 disabled:opacity-50"
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
              <span>{isSubmitting ? 'Authenticating...' : 'Continue with Google'}</span>
            </button>

            <div className="pt-2">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                Or Quick Test Personas:
              </span>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() =>
                    handleGoogleLogin(
                      'Alex Rivera',
                      'alex.rivera@example.com',
                      'Lead AI Architect',
                      'Prefers dark mode, focused on neural models & robotics.'
                    )
                  }
                  className="p-2.5 text-left rounded-xl bg-slate-950/60 hover:bg-slate-800 border border-slate-800 text-xs transition"
                >
                  <p className="font-bold text-slate-200">Alex Rivera</p>
                  <p className="text-[10px] text-slate-400 truncate">Lead AI Architect</p>
                </button>

                <button
                  onClick={() =>
                    handleGoogleLogin(
                      'Sarah Chen',
                      'sarah.chen@example.com',
                      'Product Designer',
                      'Prefers visual summaries, early morning schedules.'
                    )
                  }
                  className="p-2.5 text-left rounded-xl bg-slate-950/60 hover:bg-slate-800 border border-slate-800 text-xs transition"
                >
                  <p className="font-bold text-slate-200">Sarah Chen</p>
                  <p className="text-[10px] text-slate-400 truncate">Product Designer</p>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Custom Profile Form */}
        {activeTab === 'custom' && (
          <form onSubmit={handleCustomSubmit} className="space-y-3">
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">Your Name</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="text"
                  required
                  placeholder="e.g. Alex"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-xs rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">Email (Optional)</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="email"
                  placeholder="alex@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-xs rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">Role / Occupation</label>
              <div className="relative">
                <Briefcase className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="text"
                  placeholder="e.g. Researcher / Student / Executive"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-xs rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                What should AEGIS remember about you?
              </label>
              <div className="relative">
                <FileText className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <textarea
                  rows={2}
                  placeholder="e.g. Keep answers concise, my timezone is IST, I drink green tea in the morning..."
                  value={personalNotes}
                  onChange={(e) => setPersonalNotes(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-xs rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting || !name.trim()}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white font-bold text-xs tracking-wider uppercase transition shadow-md active:scale-95 disabled:opacity-40"
            >
              <span>{isSubmitting ? 'Saving Profile...' : 'Save & Sync Profile'}</span>
            </button>
          </form>
        )}

        {/* Message notification */}
        {message && (
          <div className="mt-4 p-2.5 rounded-xl bg-cyan-950/80 border border-cyan-500/50 text-xs text-cyan-300 font-medium text-center animate-fade-in">
            {message}
          </div>
        )}

        {/* Privacy Note */}
        <div className="mt-5 flex items-center gap-2 text-[11px] text-slate-400 justify-center">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Stored locally in your private SQLite database.</span>
        </div>
      </div>
    </div>
  );
};
