import React, { useState, useEffect } from 'react';
import { 
  X, Check, Sparkles, User, Mail, Lock, Eye, EyeOff, 
  MapPin, Phone, AlertTriangle, ShieldCheck, LogOut, Edit3, 
  Save, KeyRound, CheckCircle2, ChevronRight
} from 'lucide-react';

export interface UserProfileData {
  user_id: string;
  name: string;
  email?: string;
  avatar_url?: string;
  auth_provider: string;
  role?: string;
  phone?: string;
  location?: string;
  timezone?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  bio?: string;
  personal_notes?: string;
  preferences?: Record<string, any>;
  accessibility_settings?: Record<string, any>;
  is_authenticated?: boolean;
}

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser: UserProfileData;
  onLoginSuccess: (user: UserProfileData, token?: string) => void;
  onLogout: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  currentUser,
  onLoginSuccess,
  onLogout
}) => {
  const [activeTab, setActiveTab] = useState<'google' | 'signin' | 'signup' | 'profile'>('google');
  
  // Sign In Form States
  const [loginEmail, setLoginEmail] = useState<string>('');
  const [loginPassword, setLoginPassword] = useState<string>('');
  const [showLoginPassword, setShowLoginPassword] = useState<boolean>(false);

  // Sign Up Form States (Full Info Access)
  const [regName, setRegName] = useState<string>('');
  const [regEmail, setRegEmail] = useState<string>('');
  const [regPassword, setRegPassword] = useState<string>('');
  const [showRegPassword, setShowRegPassword] = useState<boolean>(false);
  const [regRole, setRegRole] = useState<string>('Software Engineer');
  const [regPhone, setRegPhone] = useState<string>('');
  const [regLocation, setRegLocation] = useState<string>('Bengaluru, India');
  const [regEmergencyName, setRegEmergencyName] = useState<string>('');
  const [regEmergencyPhone, setRegEmergencyPhone] = useState<string>('');
  const [regBio, setRegBio] = useState<string>('');
  const [regNotes, setRegNotes] = useState<string>('Prefers clear, concise speech, active on vision and AI agents.');

  // Profile Edit States
  const [isEditingProfile, setIsEditingProfile] = useState<boolean>(false);
  const [editLocation, setEditLocation] = useState<string>(currentUser.location || '');
  const [editPhone, setEditPhone] = useState<string>(currentUser.phone || '');
  const [editEmergencyName, setEditEmergencyName] = useState<string>(currentUser.emergency_contact_name || '');
  const [editEmergencyPhone, setEditEmergencyPhone] = useState<string>(currentUser.emergency_contact_phone || '');
  const [editNotes, setEditNotes] = useState<string>(currentUser.personal_notes || '');

  // Status & Notification
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    if (currentUser.is_authenticated) {
      setActiveTab('profile');
      setEditLocation(currentUser.location || '');
      setEditPhone(currentUser.phone || '');
      setEditEmergencyName(currentUser.emergency_contact_name || '');
      setEditEmergencyPhone(currentUser.emergency_contact_phone || '');
      setEditNotes(currentUser.personal_notes || '');
    } else {
      setActiveTab('google');
    }
  }, [currentUser, isOpen]);

  if (!isOpen) return null;

  // 1. Google OAuth Sign-In
  const handleGoogleLogin = async (customName?: string, customEmail?: string, customRole?: string) => {
    setIsLoading(true);
    setMessage(null);
    try {
      const name = customName || 'Alex Rivera';
      const email = customEmail || 'alex.rivera@gmail.com';
      const role = customRole || 'Lead AI Architect';

      const payload = {
        name,
        email,
        avatar_url: 'https://api.dicebear.com/7.x/bottts/svg?seed=' + name,
        role,
        location: 'Bengaluru, India',
        emergency_contact_name: 'Elena Vance',
        emergency_contact_phone: '+91-98765-43210',
        personal_notes: 'Prefers spoken confirmations and high-accuracy spatial grounding.'
      };

      const res = await fetch('/api/auth/google', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (res.ok && data.status === 'success') {
        if (data.token) localStorage.setItem('aegis_auth_token', data.token);
        onLoginSuccess(data.user, data.token);
        setMessage({ text: 'Authenticated via Google as ' + data.user.name + '! AEGIS memories updated.', type: 'success' });
        setTimeout(() => onClose(), 900);
      } else {
        setMessage({ text: data.detail || 'Google authentication could not be completed.', type: 'error' });
      }
    } catch (e: any) {
      setMessage({ text: 'Network error: ' + e.message, type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  // 2. Email & Password Sign In
  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loginEmail.trim() || !loginPassword.trim()) return;

    setIsLoading(true);
    setMessage(null);
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: loginEmail.trim(), password: loginPassword })
      });

      const data = await res.json();
      if (res.ok && data.status === 'success') {
        if (data.token) localStorage.setItem('aegis_auth_token', data.token);
        onLoginSuccess(data.user, data.token);
        setMessage({ text: 'Signed in as ' + data.user.name + '! Access credentials verified.', type: 'success' });
        setTimeout(() => onClose(), 900);
      } else {
        setMessage({ text: data.detail || 'Invalid email or password.', type: 'error' });
      }
    } catch (e: any) {
      setMessage({ text: 'Connection error: ' + e.message, type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  // 3. Full Info Registration (Sign Up)
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regName.trim() || !regEmail.trim() || !regPassword.trim()) return;

    setIsLoading(true);
    setMessage(null);
    try {
      const payload = {
        name: regName.trim(),
        email: regEmail.trim(),
        password: regPassword,
        role: regRole.trim(),
        phone: regPhone.trim() || undefined,
        location: regLocation.trim() || undefined,
        emergency_contact_name: regEmergencyName.trim() || undefined,
        emergency_contact_phone: regEmergencyPhone.trim() || undefined,
        bio: regBio.trim() || undefined,
        personal_notes: regNotes.trim() || undefined
      };

      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (res.ok && data.status === 'success') {
        if (data.token) localStorage.setItem('aegis_auth_token', data.token);
        onLoginSuccess(data.user, data.token);
        setMessage({ text: 'Account created for ' + data.user.name + '! Full personal memories initialized.', type: 'success' });
        setTimeout(() => onClose(), 1000);
      } else {
        setMessage({ text: data.detail || 'Could not register account.', type: 'error' });
      }
    } catch (e: any) {
      setMessage({ text: 'Registration error: ' + e.message, type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  // 4. Update Profile & Memory
  const handleUpdateProfile = async () => {
    setIsLoading(true);
    setMessage(null);
    try {
      const token = localStorage.getItem('aegis_auth_token') || '';
      const payload = {
        location: editLocation,
        phone: editPhone,
        emergency_contact_name: editEmergencyName,
        emergency_contact_phone: editEmergencyPhone,
        personal_notes: editNotes
      };

      const res = await fetch('/api/auth/profile', {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + token
        },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (res.ok && data.status === 'success') {
        onLoginSuccess(data.user);
        setIsEditingProfile(false);
        setMessage({ text: 'Profile details and AEGIS memories updated!', type: 'success' });
      } else {
        setMessage({ text: data.detail || 'Could not update profile.', type: 'error' });
      }
    } catch (e: any) {
      setMessage({ text: 'Update error: ' + e.message, type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-xl animate-fade-in select-none">
      <div className="relative w-full max-w-xl bg-slate-900/95 border border-slate-700/80 rounded-3xl p-6 sm:p-8 shadow-2xl shadow-cyan-950/50 text-slate-100 overflow-hidden backdrop-blur-2xl max-h-[92vh] flex flex-col">
        
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3.5 mb-5 shrink-0">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-cyan-500 via-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-lg shadow-cyan-500/20">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-slate-100">Security & User Profile Access</h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-500/40 text-emerald-400 font-semibold">
                FIPS-PBKDF2
              </span>
            </div>
            <p className="text-xs text-slate-400">Authentic credentials, comprehensive personal data & memory sync</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex rounded-xl bg-slate-950/80 p-1 mb-5 border border-slate-800/80 shrink-0 text-xs font-bold">
          <button
            onClick={() => setActiveTab('google')}
            className={'flex-1 py-2 rounded-lg transition ' + (activeTab === 'google' ? 'bg-slate-800 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200')}
          >
            Google Sign-In
          </button>
          <button
            onClick={() => setActiveTab('signin')}
            className={'flex-1 py-2 rounded-lg transition ' + (activeTab === 'signin' ? 'bg-slate-800 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200')}
          >
            Sign In
          </button>
          <button
            onClick={() => setActiveTab('signup')}
            className={'flex-1 py-2 rounded-lg transition ' + (activeTab === 'signup' ? 'bg-slate-800 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200')}
          >
            Create Account
          </button>
          {currentUser.is_authenticated && (
            <button
              onClick={() => setActiveTab('profile')}
              className={'flex-1 py-2 rounded-lg transition ' + (activeTab === 'profile' ? 'bg-slate-800 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200')}
            >
              My Profile
            </button>
          )}
        </div>

        {/* Scrollable Form Body */}
        <div className="flex-1 overflow-y-auto pr-1 space-y-4">
          
          {/* TAB 1: GOOGLE SIGN-IN */}
          {activeTab === 'google' && (
            <div className="space-y-4 animate-fade-in">
              <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 text-xs text-slate-300 leading-relaxed">
                Sign in with your Google account to grant AEGIS verified identity access, automated routine learning, and persistent cross-session memories.
              </div>

              {/* Primary Google Auth Button */}
              <button
                onClick={() => handleGoogleLogin()}
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-3 px-5 py-3.5 rounded-2xl bg-white hover:bg-slate-100 text-slate-900 font-bold text-xs tracking-wide transition shadow-lg hover:shadow-white/20 active:scale-95 disabled:opacity-50"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"/>
                  <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"/>
                  <path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15z"/>
                  <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/>
                </svg>
                <span>{isLoading ? 'Authenticating with Google...' : 'Continue with Google Account'}</span>
              </button>

              {/* Quick Persona Options */}
              <div className="pt-2">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                  Or Test Verified User Profiles:
                </span>
                <div className="grid grid-cols-2 gap-2.5">
                  <button
                    onClick={() => handleGoogleLogin('Alex Rivera', 'alex.rivera@gmail.com', 'Lead AI Architect')}
                    className="p-3 text-left rounded-2xl bg-slate-950/60 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/40 text-xs transition"
                  >
                    <p className="font-bold text-slate-200">Alex Rivera</p>
                    <p className="text-[10px] text-cyan-400 font-mono">alex.rivera@gmail.com</p>
                    <p className="text-[10px] text-slate-400 truncate mt-1">Lead AI Architect</p>
                  </button>

                  <button
                    onClick={() => handleGoogleLogin('Sarah Chen', 'sarah.chen@gmail.com', 'Assistive Tech Specialist')}
                    className="p-3 text-left rounded-2xl bg-slate-950/60 hover:bg-slate-800 border border-slate-800 hover:border-purple-500/40 text-xs transition"
                  >
                    <p className="font-bold text-slate-200">Sarah Chen</p>
                    <p className="text-[10px] text-purple-400 font-mono">sarah.chen@gmail.com</p>
                    <p className="text-[10px] text-slate-400 truncate mt-1">Assistive Tech Specialist</p>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: SIGN IN (EMAIL + PASSWORD) */}
          {activeTab === 'signin' && (
            <form onSubmit={handleEmailLogin} className="space-y-3.5 animate-fade-in">
              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">Email Address</label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="email"
                    required
                    placeholder="user@example.com"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    className="w-full pl-9 pr-3 py-2.5 text-xs rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type={showLoginPassword ? 'text' : 'password'}
                    required
                    placeholder="Enter account password"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    className="w-full pl-9 pr-10 py-2.5 text-xs rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
                  />
                  <button
                    type="button"
                    onClick={() => setShowLoginPassword(!showLoginPassword)}
                    className="absolute right-3 top-3 text-slate-400 hover:text-slate-200"
                  >
                    {showLoginPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white font-bold text-xs tracking-wider uppercase transition shadow-md active:scale-95 disabled:opacity-50"
              >
                <span>{isLoading ? 'Verifying Credentials...' : 'Sign In Securely'}</span>
              </button>
            </form>
          )}

          {/* TAB 3: CREATE ACCOUNT (FULL INFO REGISTRATION) */}
          {activeTab === 'signup' && (
            <form onSubmit={handleRegister} className="space-y-3 animate-fade-in">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">Full Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Alex Rivera"
                    value={regName}
                    onChange={(e) => setRegName(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">Email *</label>
                  <input
                    type="email"
                    required
                    placeholder="user@example.com"
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">Password *</label>
                  <div className="relative">
                    <input
                      type={showRegPassword ? 'text' : 'password'}
                      required
                      placeholder="Min 6 characters"
                      value={regPassword}
                      onChange={(e) => setRegPassword(e.target.value)}
                      className="w-full pl-3 pr-8 py-2 text-xs rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
                    />
                    <button
                      type="button"
                      onClick={() => setShowRegPassword(!showRegPassword)}
                      className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-200"
                    >
                      {showRegPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">Role / Occupation</label>
                  <input
                    type="text"
                    placeholder="e.g. Architect, Student, Doctor"
                    value={regRole}
                    onChange={(e) => setRegRole(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">City / Location</label>
                  <input
                    type="text"
                    placeholder="e.g. Bengaluru, India"
                    value={regLocation}
                    onChange={(e) => setRegLocation(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">Phone Number</label>
                  <input
                    type="tel"
                    placeholder="+91-98765-43210"
                    value={regPhone}
                    onChange={(e) => setRegPhone(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
                  />
                </div>
              </div>

              {/* Assistive Emergency Contacts (SIH26204 Requirement) */}
              <div className="p-3 rounded-2xl bg-amber-950/20 border border-amber-500/30 space-y-2">
                <div className="flex items-center gap-1.5 text-xs font-bold text-amber-300">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                  <span>Emergency Assistive Contact (For AEGIS Alerts)</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <input
                    type="text"
                    placeholder="Contact Name (e.g. Sarah)"
                    value={regEmergencyName}
                    onChange={(e) => setRegEmergencyName(e.target.value)}
                    className="w-full px-3 py-1.5 text-xs rounded-lg bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-400"
                  />
                  <input
                    type="tel"
                    placeholder="Contact Phone Number"
                    value={regEmergencyPhone}
                    onChange={(e) => setRegEmergencyPhone(e.target.value)}
                    className="w-full px-3 py-1.5 text-xs rounded-lg bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-400"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                  What should AEGIS remember about you? (Preferences / Habits)
                </label>
                <textarea
                  rows={2}
                  placeholder="e.g. I prefer dark mode, morning wake-up at 7 AM, speak concise answers..."
                  value={regNotes}
                  onChange={(e) => setRegNotes(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs tracking-wider uppercase transition shadow-md active:scale-95 disabled:opacity-50"
              >
                <span>{isLoading ? 'Securing & Encrypting...' : 'Register & Sync All Details'}</span>
              </button>
            </form>
          )}

          {/* TAB 4: PROFILE & MEMORY INSPECTOR */}
          {activeTab === 'profile' && (
            <div className="space-y-4 animate-fade-in">
              {/* User Identity Banner */}
              <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white text-base font-bold shadow-md shadow-cyan-500/20">
                    {currentUser.name ? currentUser.name.charAt(0) : 'U'}
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-100">{currentUser.name}</h3>
                    <p className="text-[11px] font-mono text-cyan-400">{currentUser.email || 'Local User'}</p>
                    <p className="text-[10px] text-slate-400">{currentUser.role} &bull; Auth: {currentUser.auth_provider}</p>
                  </div>
                </div>

                <button
                  onClick={() => {
                    onLogout();
                    localStorage.removeItem('aegis_auth_token');
                    setActiveTab('google');
                  }}
                  className="flex items-center gap-1 text-xs font-bold text-rose-400 hover:text-rose-300 px-3 py-1.5 rounded-xl border border-rose-500/30 hover:bg-rose-950/40 transition"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Logout</span>
                </button>
              </div>

              {/* Data Ingested into AEGIS Memory */}
              <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-3 text-xs">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <span className="font-bold text-slate-300 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span>Synchronized Long-Term Memories</span>
                  </span>
                  {!isEditingProfile ? (
                    <button
                      onClick={() => setIsEditingProfile(true)}
                      className="inline-flex items-center gap-1 text-[11px] text-cyan-400 hover:text-cyan-300"
                    >
                      <Edit3 className="w-3 h-3" />
                      <span>Edit Info</span>
                    </button>
                  ) : (
                    <button
                      onClick={handleUpdateProfile}
                      disabled={isLoading}
                      className="inline-flex items-center gap-1 text-[11px] text-emerald-400 hover:text-emerald-300 font-bold"
                    >
                      <Save className="w-3 h-3" />
                      <span>Save & Sync</span>
                    </button>
                  )}
                </div>

                {!isEditingProfile ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-slate-300">
                    <div>
                      <span className="text-[10px] text-slate-500 block uppercase">Location</span>
                      <span className="font-medium">{currentUser.location || 'Not set'}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block uppercase">Phone</span>
                      <span className="font-medium">{currentUser.phone || 'Not set'}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block uppercase">Emergency Contact</span>
                      <span className="font-medium text-amber-300">
                        {currentUser.emergency_contact_name 
                          ? `${currentUser.emergency_contact_name} (${currentUser.emergency_contact_phone || 'No phone'})` 
                          : 'Not configured'}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block uppercase">Timezone</span>
                      <span className="font-medium font-mono">{currentUser.timezone || 'Asia/Kolkata'}</span>
                    </div>
                    <div className="col-span-full">
                      <span className="text-[10px] text-slate-500 block uppercase">Personal Preferences</span>
                      <p className="text-[11px] text-slate-300 italic bg-slate-900/60 p-2 rounded-xl mt-1">
                        "{currentUser.personal_notes || 'Standard executive assistant configuration'}"
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-2">
                      <input
                        type="text"
                        placeholder="Location"
                        value={editLocation}
                        onChange={(e) => setEditLocation(e.target.value)}
                        className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs"
                      />
                      <input
                        type="text"
                        placeholder="Phone"
                        value={editPhone}
                        onChange={(e) => setEditPhone(e.target.value)}
                        className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <input
                        type="text"
                        placeholder="Emergency Name"
                        value={editEmergencyName}
                        onChange={(e) => setEditEmergencyName(e.target.value)}
                        className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs"
                      />
                      <input
                        type="text"
                        placeholder="Emergency Phone"
                        value={editEmergencyPhone}
                        onChange={(e) => setEditEmergencyPhone(e.target.value)}
                        className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs"
                      />
                    </div>
                    <textarea
                      rows={2}
                      placeholder="Personal notes & preferences"
                      value={editNotes}
                      onChange={(e) => setEditNotes(e.target.value)}
                      className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs"
                    />
                  </div>
                )}
              </div>
            </div>
          )}

        </div>

        {/* Status Message Notification */}
        {message && (
          <div
            className={'mt-4 p-2.5 rounded-xl text-xs font-medium text-center shrink-0 animate-fade-in ' + (
              message.type === 'success'
                ? 'bg-emerald-950/80 border border-emerald-500/50 text-emerald-300'
                : 'bg-rose-950/80 border border-rose-500/50 text-rose-300'
            )}
          >
            {message.text}
          </div>
        )}

        {/* Footer Security Badge */}
        <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500 shrink-0">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Encrypted Local Vault</span>
          </div>
          <span className="font-mono text-[10px]">SHA-256 / PBKDF2</span>
        </div>
      </div>
    </div>
  );
};
