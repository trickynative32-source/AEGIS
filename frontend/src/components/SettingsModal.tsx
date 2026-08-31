import React, { useState, useEffect } from 'react';
import { Settings, Key, Shield, Cpu, Mic, Eye, MapPin, Trash2, X, Check, Globe } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const [apiKey, setApiKey] = useState<string>('');
  const [geminiKey, setGeminiKey] = useState<string>('');
  const [model, setModel] = useState<string>('google/gemini-2.0-flash-001');
  const [cameraEnabled, setCameraEnabled] = useState<boolean>(false);
  const [locationEnabled, setLocationEnabled] = useState<boolean>(true);
  const [learningEnabled, setLearningEnabled] = useState<boolean>(true);
  const [voiceFirstMode, setVoiceFirstMode] = useState<boolean>(false);
  const [saveStatus, setSaveStatus] = useState<string>('');

  useEffect(() => {
    if (isOpen) {
      fetch('http://127.0.0.1:8000/api/settings')
        .then((res) => res.json())
        .then((data) => {
          setModel(data.OPENROUTER_MODEL || 'google/gemini-2.0-flash-001');
          setCameraEnabled(data.CAMERA_ENABLED || false);
          setLocationEnabled(data.LOCATION_ENABLED || true);
          setLearningEnabled(data.LEARNING_ENABLED || true);
          setVoiceFirstMode(data.VOICE_FIRST_MODE || false);
        })
        .catch((e) => console.error(e));
    }
  }, [isOpen]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch('http://127.0.0.1:8000/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          OPENROUTER_API_KEY: apiKey,
          GEMINI_API_KEY: geminiKey,
          OPENROUTER_MODEL: model,
          CAMERA_ENABLED: cameraEnabled,
          LOCATION_ENABLED: locationEnabled,
          LEARNING_ENABLED: learningEnabled,
          VOICE_FIRST_MODE: voiceFirstMode
        })
      });
      if (res.ok) {
        setSaveStatus('Settings updated successfully.');
        setTimeout(() => setSaveStatus(''), 2500);
      }
    } catch (e) {
      setSaveStatus('Error saving settings.');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg glass-panel border border-cyan-500/30 rounded-2xl p-6 shadow-2xl space-y-5">
        <div className="flex items-center justify-between pb-3 border-b border-slate-700/60">
          <div className="flex items-center gap-2 text-aura-cyan">
            <Settings className="w-5 h-5" />
            <h2 className="text-base font-bold text-slate-100">AEGIS System & Privacy Settings</h2>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSave} className="space-y-4 text-xs">
          {/* Gemini API Key */}
          <div className="space-y-1.5">
            <label className="flex items-center gap-1.5 font-semibold text-slate-300">
              <Key className="w-3.5 h-3.5 text-cyan-400" />
              <span>Google Gemini API Key (Recommended)</span>
            </label>
            <input
              type="password"
              placeholder="AIzaSy..."
              value={geminiKey}
              onChange={(e) => setGeminiKey(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-aura-cyan"
            />
            <p className="text-[10px] text-slate-500">Supports native Gemini 2.0 Flash Vision & Multimodal Reasoning.</p>
          </div>

          {/* OpenRouter API Key */}
          <div className="space-y-1.5">
            <label className="flex items-center gap-1.5 font-semibold text-slate-300">
              <Key className="w-3.5 h-3.5 text-indigo-400" />
              <span>OpenRouter API Key (Alternative)</span>
            </label>
            <input
              type="password"
              placeholder="sk-or-v1-..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-aura-cyan"
            />
          </div>

          {/* Model Selector */}
          <div className="space-y-1.5">
            <label className="flex items-center gap-1.5 font-semibold text-slate-300">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" />
              <span>AI Model</span>
            </label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-100 focus:outline-none focus:border-aura-cyan"
            >
              <option value="google/gemini-2.0-flash-001">Gemini 2.0 Flash (Recommended, Fast & Free)</option>
              <option value="google/gemini-2.0-flash-lite-preview-02-05:free">Gemini 2.0 Flash Lite (Free)</option>
              <option value="qwen/qwen3-30b-a3b:free">Qwen 3 30B (Fast & Free)</option>
              <option value="qwen/qwen-2.5-72b-instruct">Qwen 2.5 72B Instruct</option>
              <option value="meta-llama/llama-3.3-70b-instruct">Meta Llama 3.3 70B</option>
              <option value="anthropic/claude-3.5-sonnet">Claude 3.5 Sonnet</option>
            </select>
          </div>

          {/* Privacy Toggles */}
          <div className="space-y-2 pt-2 border-t border-slate-700/60">
            <h3 className="font-semibold text-slate-300 uppercase tracking-wider text-[10px]">Privacy & Permissions</h3>

            <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800">
              <div className="flex items-center gap-2">
                <Eye className="w-4 h-4 text-cyan-400" />
                <span>Camera Access</span>
              </div>
              <input
                type="checkbox"
                checked={cameraEnabled}
                onChange={(e) => setCameraEnabled(e.target.checked)}
                className="w-4 h-4 rounded border-slate-700 text-aura-cyan focus:ring-0"
              />
            </div>

            <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800">
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-blue-400" />
                <span>Location Access (For Maps Navigation)</span>
              </div>
              <input
                type="checkbox"
                checked={locationEnabled}
                onChange={(e) => setLocationEnabled(e.target.checked)}
                className="w-4 h-4 rounded border-slate-700 text-aura-cyan focus:ring-0"
              />
            </div>

            <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800">
              <div className="flex items-center gap-2">
                <Globe className="w-4 h-4 text-purple-400" />
                <span>Daily Routine Learning (SIH)</span>
              </div>
              <input
                type="checkbox"
                checked={learningEnabled}
                onChange={(e) => setLearningEnabled(e.target.checked)}
                className="w-4 h-4 rounded border-slate-700 text-aura-cyan focus:ring-0"
              />
            </div>
          </div>

          {saveStatus && (
            <div className="flex items-center gap-1.5 text-xs text-emerald-400">
              <Check className="w-3.5 h-3.5" />
              <span>{saveStatus}</span>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-700/60">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition"
            >
              Close
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium shadow-md transition active:scale-95"
            >
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
