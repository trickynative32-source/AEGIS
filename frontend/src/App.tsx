import React, { useState, useEffect, useRef } from 'react';
import {
  Mic, Send, Camera, Bell, Workflow, Settings as SettingsIcon,
  Layers, Volume2, Sparkles, AlertCircle, ShieldAlert, Cpu, User, LogIn, Sliders
} from 'lucide-react';
import { wsService } from './services/websocket';
import { ChatMessage, AssistantState } from './types';
import { LiveClock } from './components/LiveClock';
import { AudioWaveform } from './components/AudioWaveform';
import { ChatView } from './components/ChatView';
import { CameraHUD } from './components/CameraHUD';
import { QuickActions } from './components/QuickActions';
import { RemindersDrawer } from './components/RemindersDrawer';
import { RoutinesDrawer } from './components/RoutinesDrawer';
import { VisualMemoryDrawer } from './components/VisualMemoryDrawer';
import { SettingsModal } from './components/SettingsModal';
import { AccessibilityBar } from './components/AccessibilityBar';
import { AuraCore } from './components/AuraCore';
import { IntroModal } from './components/IntroModal';
import { AuthModal, UserProfileData } from './components/AuthModal';

export const App: React.FC = () => {
  // Assistant States
  const [state, setState] = useState<AssistantState>('IDLE');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState<string>('');
  const [isPushToTalkActive, setIsPushToTalkActive] = useState<boolean>(false);
  const [speechPreview, setSpeechPreview] = useState<string>('');
  const [isAccessibilityOpen, setIsAccessibilityOpen] = useState<boolean>(false);

  // User Profile & Intro States
  const [currentUser, setCurrentUser] = useState<UserProfileData>({
    user_id: 'guest',
    name: 'Guest Explorer',
    auth_provider: 'guest',
    role: 'Guest'
  });
  const [isAuthOpen, setIsAuthOpen] = useState<boolean>(false);
  const [isIntroOpen, setIsIntroOpen] = useState<boolean>(() => {
    return localStorage.getItem('aegis_intro_dismissed') !== 'true';
  });

  // Senses & Modals
  const [cameraActive, setCameraActive] = useState<boolean>(false);
  const [continuousCamera, setContinuousCamera] = useState<boolean>(false);
  const [isRemindersOpen, setIsRemindersOpen] = useState<boolean>(false);
  const [isRoutinesOpen, setIsRoutinesOpen] = useState<boolean>(false);
  const [isVisualMemoryOpen, setIsVisualMemoryOpen] = useState<boolean>(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [remindersRefreshKey, setRemindersRefreshKey] = useState<number>(0);

  // Accessibility States
  const [highContrast, setHighContrast] = useState<boolean>(false);
  const [largeFont, setLargeFont] = useState<boolean>(false);
  const [dyslexicFont, setDyslexicFont] = useState<boolean>(false);
  const [voiceFirst, setVoiceFirst] = useState<boolean>(false);
  const [simplifiedMode, setSimplifiedMode] = useState<boolean>(false);

  // Web Speech Recognition for Push-to-Talk
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    // Initialize Web Speech API if supported
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const rec = new SpeechRecognition();
      rec.continuous = true;
      rec.interimResults = true;
      rec.lang = 'en-US';

      rec.onresult = (event: any) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          transcript += event.results[i][0].transcript;
        }
        setSpeechPreview(transcript);
      };

      rec.onerror = (e: any) => {
        console.warn('Speech recognition notice:', e);
      };

      recognitionRef.current = rec;
    }

    // Fetch authenticated user profile & personal memory
    const token = localStorage.getItem('aegis_auth_token');
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    fetch('/api/auth/me', { headers })
      .then((res) => res.json())
      .then((data) => {
        if (data && data.user && data.user.name) {
          setCurrentUser(data.user);
        }
      })
      .catch((e) => console.debug('Profile fetch note:', e));

    // Connect WebSocket
    wsService.connect();

    const unsubscribe = wsService.subscribe((data) => {
      if (data.type === 'init') {
        setCameraActive(data.camera_active);
      } else if (data.type === 'state_change') {
        setState(data.state);
      } else if (data.type === 'agent_response') {
        const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        // Add User message if provided
        if (data.user_text) {
          setMessages((prev) => [
            ...prev,
            {
              id: `user-${Date.now()}`,
              role: 'user',
              content: data.user_text,
              timestamp: timeStr,
              isVoice: isPushToTalkActive
            }
          ]);
        }

        // Add Assistant message
        setMessages((prev) => [
          ...prev,
          {
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: data.response,
            tool: data.tool,
            verified: data.verified,
            action: data.action,
            url: data.url,
            booking_data: data.booking_data,
            timestamp: timeStr
          }
        ]);

        // Auto-open URL in browser window if requested
        if (data.action === 'open_url' && data.url) {
          try {
            window.open(data.url, '_blank');
          } catch (e) {
            console.debug('Auto-open URL popup note:', e);
          }
        }

        if (data.tool === 'create_reminder' || data.tool === 'delete_reminder') {
          setRemindersRefreshKey((k) => k + 1);
        }
      } else if (data.type === 'reminder_alert') {
        const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        setMessages((prev) => [
          ...prev,
          {
            id: `alert-${Date.now()}`,
            role: 'system',
            content: `🔔 Reminder: ${data.text} (${data.time})`,
            timestamp: timeStr,
            verified: true
          }
        ]);
        setRemindersRefreshKey((k) => k + 1);
      } else if (data.type === 'camera_status') {
        setCameraActive(data.active);
        setContinuousCamera(data.continuous);
      }
    });

    return () => unsubscribe();
  }, []);

  // Push-to-Talk Handlers
  const handleStartPushToTalk = () => {
    setIsPushToTalkActive(true);
    setSpeechPreview('Listening...');
    wsService.bargeIn();
    setState('LISTENING');

    if (recognitionRef.current) {
      try {
        recognitionRef.current.start();
      } catch (e) {}
    }
  };

  const handleStopPushToTalk = () => {
    setIsPushToTalkActive(false);
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
    }

    if (speechPreview && speechPreview !== 'Listening...') {
      wsService.sendMessage(speechPreview, true);
    }
    setSpeechPreview('');
  };

  // Keyboard Spacebar Hold for Push-to-Talk
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === 'Space' && (e.target as HTMLElement).tagName !== 'INPUT' && !isPushToTalkActive) {
        e.preventDefault();
        handleStartPushToTalk();
      } else if (e.key === 'Escape') {
        wsService.bargeIn();
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code === 'Space' && (e.target as HTMLElement).tagName !== 'INPUT' && isPushToTalkActive) {
        e.preventDefault();
        handleStopPushToTalk();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [isPushToTalkActive, speechPreview]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    wsService.sendMessage(inputText, false);
    setInputText('');
  };

  const handleSelectQuickPrompt = (prompt: string) => {
    wsService.sendMessage(prompt, false);
  };

  const handleToggleCamera = () => {
    wsService.send({ type: 'camera_toggle', continuous: false });
  };

  return (
    <div
      className={`flex flex-col h-screen w-screen bg-aura-dark text-slate-100 overflow-hidden ${
        highContrast ? 'high-contrast' : ''
      } ${largeFont ? 'large-font' : ''} ${dyslexicFont ? 'font-dyslexic' : ''}`}
    >
      {/* Main Header */}
      <header className="flex items-center justify-between px-5 py-3 border-b border-slate-800 glass-panel shrink-0">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-cyan-950/50 border border-cyan-400/40">
              <Sparkles className="w-5 h-5 animate-pulse" />
            </div>
            <span
              className={`absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-slate-950 ${
                state === 'LISTENING'
                  ? 'bg-rose-500 animate-ping'
                  : state === 'SPEAKING'
                  ? 'bg-aura-cyan'
                  : state === 'THINKING' || state === 'EXECUTING'
                  ? 'bg-aura-amber'
                  : 'bg-emerald-500'
              }`}
            />
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-extrabold tracking-wider text-slate-100 uppercase">AEGIS</h1>
              <span className="text-[10px] px-1.5 py-0.5 rounded font-mono font-bold bg-cyan-950/80 border border-cyan-500/40 text-aura-cyan">
                SIH26204
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium hidden sm:block">
              Assisted Executive Guidance and Intelligence System
            </p>
          </div>
        </div>

        {/* Real Windows Live Clock & Telemetry Bar */}
        <div className="flex items-center gap-3">
          <div className="hidden xl:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/60 border border-slate-800 text-[10px] font-mono">
            <span className="flex items-center gap-1 text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>LATENCY &lt;1ms</span>
            </span>
            <span className="text-slate-600">&bull;</span>
            <span className="text-cyan-400">YOLOv5m + LocateAnything</span>
            <span className="text-slate-600">&bull;</span>
            <span className="text-purple-300">SECURE VAULT</span>
          </div>

          <LiveClock />
        </div>

        {/* Action Controls & Drawers */}
        <div className="flex items-center gap-2">
          {/* User Profile / Auth Status Chip */}
          <button
            onClick={() => setIsAuthOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 border border-slate-700/80 hover:border-cyan-500/50 text-slate-200 text-xs font-semibold transition shadow-sm"
            title="User Profile, Security & Personal Memory"
          >
            {currentUser.avatar_url ? (
              <img
                src={currentUser.avatar_url}
                alt={currentUser.name}
                className="w-5 h-5 rounded-full border border-cyan-400/50 object-cover"
              />
            ) : (
              <div className="w-5 h-5 rounded-full bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white text-[10px] font-bold shadow-sm">
                {currentUser.name ? currentUser.name.charAt(0) : 'G'}
              </div>
            )}
            <div className="text-left hidden sm:block">
              <span className="text-xs font-semibold text-slate-200 block max-w-[180px] truncate leading-tight">
                {currentUser.name}
              </span>
              <span className="text-[9px] font-mono text-cyan-400 uppercase tracking-wider block leading-none">
                {currentUser.role || 'User'}
              </span>
            </div>
          </button>

          {/* Intro Replay Button */}
          <button
            onClick={() => setIsIntroOpen(true)}
            className="p-2 rounded-xl bg-slate-900/80 border border-slate-700 hover:border-cyan-500/40 text-slate-300 transition"
            title="Replay AEGIS Intro"
          >
            <Sparkles className="w-4 h-4 text-cyan-400" />
          </button>

          <button
            onClick={handleToggleCamera}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl border text-xs font-semibold tracking-wide transition shadow-sm ${
              cameraActive
                ? 'bg-rose-950/80 border-rose-500/60 text-rose-300 shadow-[0_0_12px_rgba(244,63,94,0.4)]'
                : 'bg-slate-900/80 border-slate-700 hover:border-slate-500 text-slate-300'
            }`}
            title="Toggle Camera & Vision"
          >
            <Camera className="w-4 h-4" />
            <span className="hidden md:inline">{cameraActive ? 'Camera ON' : 'Camera'}</span>
          </button>

          {!simplifiedMode && (
            <>
              <button
                onClick={() => setIsVisualMemoryOpen(true)}
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-900/80 border border-slate-700 hover:border-cyan-500/40 text-slate-300 text-xs font-semibold transition"
                title="Environmental Visual Memory"
              >
                <Layers className="w-4 h-4 text-cyan-400" />
                <span className="hidden lg:inline">Visual Memory</span>
              </button>

              <button
                onClick={() => setIsRoutinesOpen(true)}
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-900/80 border border-slate-700 hover:border-purple-500/40 text-slate-300 text-xs font-semibold transition"
                title="Learned Routines"
              >
                <Workflow className="w-4 h-4 text-purple-400" />
                <span className="hidden lg:inline">Routines</span>
              </button>
            </>
          )}

          <button
            onClick={() => setIsRemindersOpen(true)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-900/80 border border-slate-700 hover:border-amber-500/40 text-slate-300 text-xs font-semibold transition"
            title="User Reminders"
          >
            <Bell className="w-4 h-4 text-amber-400" />
            <span className="hidden sm:inline">Reminders</span>
          </button>

          <button
            onClick={() => setIsAccessibilityOpen(!isAccessibilityOpen)}
            className={`p-2 rounded-xl border transition ${
              isAccessibilityOpen || highContrast || largeFont || dyslexicFont || voiceFirst || simplifiedMode
                ? 'bg-cyan-950/80 border-cyan-400/60 text-cyan-300 shadow-sm'
                : 'bg-slate-900/80 border-slate-700 hover:border-slate-500 text-slate-300'
            }`}
            title="Accessibility & Inclusion Settings (SIH26204)"
          >
            <Sliders className="w-4 h-4" />
          </button>

          <button
            onClick={() => setIsSettingsOpen(true)}
            className="p-2 rounded-xl bg-slate-900/80 border border-slate-700 hover:border-slate-500 text-slate-300 transition"
            title="Settings & Privacy"
          >
            <SettingsIcon className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Expandable Accessibility Tray (SIH Inclusion) */}
      {isAccessibilityOpen && (
        <div className="animate-fade-in border-b border-slate-800 bg-slate-950/90 backdrop-blur-xl shrink-0">
          <AccessibilityBar
            highContrast={highContrast}
            largeFont={largeFont}
            dyslexicFont={dyslexicFont}
            voiceFirst={voiceFirst}
            simplifiedMode={simplifiedMode}
            onToggleHighContrast={() => setHighContrast(!highContrast)}
            onToggleLargeFont={() => setLargeFont(!largeFont)}
            onToggleDyslexicFont={() => setDyslexicFont(!dyslexicFont)}
            onToggleVoiceFirst={() => setVoiceFirst(!voiceFirst)}
            onToggleSimplifiedMode={() => setSimplifiedMode(!simplifiedMode)}
          />
        </div>
      )}

      {/* Main Workspace */}
      <main className="flex-1 flex flex-col min-h-0 relative">
        {/* Living Conversational Core ("AuraCore") */}
        <AuraCore
          state={state}
          isPushToTalkActive={isPushToTalkActive}
          isCompact={messages.length > 1}
          onCoreClick={() => {
            if (state === 'SPEAKING') {
              wsService.bargeIn();
            } else if (isPushToTalkActive) {
              handleStopPushToTalk();
            } else {
              handleStartPushToTalk();
            }
          }}
          latestAssistantUtterance={
            messages
              .slice()
              .reverse()
              .find((m) => m.role === 'assistant')?.content
          }
        />

        {/* Quick Actions Chips */}
        {!simplifiedMode && <QuickActions onSelectAction={handleSelectQuickPrompt} />}

        {/* Chat Timeline */}
        <ChatView
          messages={messages}
          state={state}
          onBargeIn={() => wsService.bargeIn()}
          onQuickReply={handleSelectQuickPrompt}
        />

        {/* Camera HUD Window */}
        <CameraHUD
          isActive={cameraActive}
          isContinuous={continuousCamera}
          onToggleCamera={handleToggleCamera}
          onClose={() => setCameraActive(false)}
        />

        {/* Drawers & Modals */}
        <RemindersDrawer
          isOpen={isRemindersOpen}
          onClose={() => setIsRemindersOpen(false)}
          onRefreshTrigger={remindersRefreshKey}
        />
        <RoutinesDrawer isOpen={isRoutinesOpen} onClose={() => setIsRoutinesOpen(false)} />
        <VisualMemoryDrawer isOpen={isVisualMemoryOpen} onClose={() => setIsVisualMemoryOpen(false)} />
        <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />

        {/* Soft Intro Onboarding Modal */}
        <IntroModal
          isOpen={isIntroOpen}
          onEnter={() => setIsIntroOpen(false)}
          onOpenAuth={() => {
            setIsIntroOpen(false);
            setIsAuthOpen(true);
          }}
          userName={currentUser.name}
        />

        {/* User Profile & Authentication Modal */}
        <AuthModal
          isOpen={isAuthOpen}
          onClose={() => setIsAuthOpen(false)}
          currentUser={currentUser}
          onLoginSuccess={(user) => {
            setCurrentUser(user);
          }}
          onLogout={() => {
            setCurrentUser({
              user_id: 'guest',
              name: 'Guest Explorer',
              auth_provider: 'guest',
              role: 'Guest'
            });
            fetch('/api/user/logout', { method: 'POST' }).catch(() => {});
          }}
        />

        {/* Speech Preview Strip */}
        {speechPreview && (
          <div className="mx-4 mb-2 p-2.5 rounded-xl bg-cyan-950/80 border border-cyan-500/50 text-xs text-aura-cyan font-mono animate-pulse flex items-center gap-2">
            <Mic className="w-4 h-4" />
            <span>{speechPreview}</span>
          </div>
        )}

        {/* Audio Waveform */}
        <AudioWaveform state={state} isPushToTalkActive={isPushToTalkActive} />

        {/* Bottom Floating Glassmorphic Console */}
        <div className="p-3 sm:p-4 shrink-0 pointer-events-none">
          <div className="max-w-4xl mx-auto flex items-center gap-2.5 p-2 rounded-3xl bg-slate-900/85 border border-slate-700/80 shadow-2xl shadow-cyan-950/40 backdrop-blur-2xl pointer-events-auto">
            {/* Push-to-Talk Button */}
            <button
              onMouseDown={handleStartPushToTalk}
              onMouseUp={handleStopPushToTalk}
              onTouchStart={handleStartPushToTalk}
              onTouchEnd={handleStopPushToTalk}
              className={`flex items-center gap-2 px-4 sm:px-5 py-3 rounded-2xl font-bold text-xs tracking-wider uppercase transition-all duration-300 shadow-lg select-none shrink-0 ${
                isPushToTalkActive
                  ? 'bg-rose-600 hover:bg-rose-500 text-white shadow-rose-950/80 scale-95 border-2 border-white animate-pulse'
                  : 'bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white border border-cyan-400/40 shadow-cyan-950/50 active:scale-95'
              }`}
              title="Hold to Speak (or hold Spacebar)"
            >
              <Mic className="w-4 h-4" />
              <span className="hidden sm:inline">{isPushToTalkActive ? 'Release to Send' : 'Push to Talk'}</span>
            </button>

            {/* Chat Input Field */}
            <form onSubmit={handleSendMessage} className="flex-1 flex items-center gap-2">
              <input
                type="text"
                placeholder="Ask AEGIS anything or give a command (e.g. 'What do you see?', 'Where is my phone?')..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                className="flex-1 px-4 py-2.5 text-xs sm:text-sm rounded-2xl bg-slate-950/70 border border-slate-700/60 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/30 transition shadow-inner"
              />
              <button
                type="submit"
                disabled={!inputText.trim()}
                className="p-3 rounded-2xl bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white disabled:opacity-30 disabled:hover:from-cyan-600 disabled:hover:to-indigo-600 transition-all duration-200 shadow-md active:scale-95 shrink-0"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
          <div className="max-w-4xl mx-auto flex items-center justify-between px-6 pt-1 text-[10px] font-mono text-slate-500">
            <span>Hold Spacebar for Voice Core</span>
            <span>Press Enter to send</span>
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
