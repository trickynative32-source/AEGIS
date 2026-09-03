import React, { useEffect, useRef, useState } from 'react';
import { 
  Bot, User, CheckCircle2, AlertCircle, Wrench, Volume2, Square, 
  Copy, Check, Sparkles, Terminal, ArrowRight, ShieldCheck, Zap,
  Plane, ExternalLink, Calendar
} from 'lucide-react';
import { ChatMessage, AssistantState } from '../types';

interface ChatViewProps {
  messages: ChatMessage[];
  state: AssistantState;
  onBargeIn: () => void;
  onQuickReply?: (prompt: string) => void;
}

export const ChatView: React.FC<ChatViewProps> = ({ 
  messages, 
  state, 
  onBargeIn,
  onQuickReply 
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [speakingMsgId, setSpeakingMsgId] = useState<string | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, state]);

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1500);
  };

  const handlePlayAudio = (id: string, text: string) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.05;
      utterance.pitch = 1.0;
      utterance.onend = () => setSpeakingMsgId(null);
      utterance.onerror = () => setSpeakingMsgId(null);
      setSpeakingMsgId(id);
      window.speechSynthesis.speak(utterance);
    }
  };

  const lastAssistantMsg = [...messages].reverse().find((m) => m.role === 'assistant');

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden relative">
      {/* Live Speaking Subtitle Banner with Barge-in Interruption */}
      {state === 'SPEAKING' && lastAssistantMsg && (
        <div className="absolute top-2 left-4 right-4 z-20 flex items-center justify-between p-3.5 rounded-2xl bg-cyan-950/90 border border-cyan-400/60 shadow-xl shadow-cyan-950/60 backdrop-blur-xl animate-fade-in">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="p-2 rounded-xl bg-cyan-500/20 text-cyan-300 animate-pulse shrink-0">
              <Volume2 className="w-5 h-5" />
            </div>
            <div className="overflow-hidden">
              <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 font-bold block">
                AEGIS Vocal Transmission
              </span>
              <p className="text-xs sm:text-sm font-medium text-slate-100 truncate">
                {lastAssistantMsg.content}
              </p>
            </div>
          </div>
          <button
            onClick={onBargeIn}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-rose-500/25 hover:bg-rose-500/40 border border-rose-500/50 text-rose-300 text-xs font-bold tracking-wide transition shadow-sm active:scale-95 shrink-0"
            title="Interrupt speech (Barge-in)"
          >
            <Square className="w-3.5 h-3.5 fill-rose-300" />
            <span>Interrupt</span>
          </button>
        </div>
      )}

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-5">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center text-slate-500 text-xs py-8">
            <div className="w-12 h-12 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center justify-center mb-3 text-cyan-400/60">
              <Terminal className="w-6 h-6" />
            </div>
            <p className="text-slate-400 font-medium">Ready for your input.</p>
            <p className="text-slate-500 text-[11px] mt-1">
              Type a request, click the Core, or hold <span className="text-cyan-400 font-semibold">Spacebar</span> for voice.
            </p>
          </div>
        )}

        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          const isAlert = msg.role === 'system';

          if (isAlert) {
            return (
              <div key={msg.id} className="flex justify-center my-2">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-950/60 border border-amber-500/40 text-amber-300 text-xs font-mono shadow-sm">
                  <ShieldCheck className="w-4 h-4 text-amber-400" />
                  <span>{msg.content}</span>
                  <span className="text-[10px] text-amber-400/60 ml-1">{msg.timestamp}</span>
                </div>
              </div>
            );
          }

          return (
            <div
              key={msg.id}
              className={`flex gap-3 max-w-[88%] sm:max-w-[80%] ${
                isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'
              } group`}
            >
              {/* Avatar Hologram */}
              <div
                className={`w-9 h-9 rounded-2xl flex items-center justify-center shrink-0 shadow-md transition-all ${
                  isUser
                    ? 'bg-gradient-to-tr from-indigo-600 to-purple-600 border border-indigo-400/40 text-white'
                    : 'bg-gradient-to-tr from-cyan-600 to-blue-600 border border-cyan-400/50 text-white shadow-cyan-950/50'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div className="flex flex-col gap-1.5 flex-1 min-w-0">
                {/* Sender Tag & Timestamp */}
                <div className={`flex items-center gap-2 px-1 ${isUser ? 'justify-end' : 'justify-start'}`}>
                  <span className="text-[11px] font-bold text-slate-300">
                    {isUser ? 'You' : 'AEGIS Core'}
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">
                    {msg.timestamp} {msg.isVoice ? ' Voice' : ''}
                  </span>
                </div>

                {/* Message Bubble Card */}
                <div
                  className={`p-4 rounded-3xl text-sm leading-relaxed relative ${
                    isUser
                      ? 'cyber-card-user text-slate-100 rounded-tr-none'
                      : 'cyber-card text-slate-200 rounded-tl-none'
                  }`}
                >
                  <div className="whitespace-pre-wrap select-text font-normal">
                    {msg.content}
                  </div>

                  {/* Tool Execution Telemetry Pill */}
                  {msg.tool && (
                    <div className="mt-3 pt-2.5 border-t border-slate-700/50 flex flex-wrap items-center justify-between gap-2 text-xs">
                      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900/90 border border-slate-700 font-mono text-cyan-300 text-[11px]">
                        <Wrench className="w-3 h-3 text-cyan-400" />
                        <span>tool: {msg.tool}</span>
                      </div>

                      <div className="flex items-center gap-1 text-[11px] font-medium text-emerald-400">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Verified & Executed</span>
                      </div>
                    </div>
                  )}

                  {/* Holographic Flight Booking Card */}
                  {msg.booking_data && (
                    <div className="mt-3 p-3.5 rounded-2xl bg-slate-950/80 border border-cyan-500/40 shadow-lg shadow-cyan-950/40 space-y-3 animate-fade-in">
                      <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-xl bg-cyan-950/80 border border-cyan-400/50 flex items-center justify-center text-cyan-300 shadow-sm">
                            <Plane className="w-4 h-4" />
                          </div>
                          <div>
                            <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 font-bold block">
                              Flight Booking &bull; {msg.booking_data.site || 'Portal Redirection'}
                            </span>
                            <div className="flex items-center gap-1.5 text-xs font-bold text-slate-100">
                              <span>{msg.booking_data.origin}</span>
                              {msg.booking_data.origin_code && (
                                <span className="font-mono text-[10px] text-cyan-300 px-1.5 py-0.5 rounded bg-cyan-950/80 border border-cyan-500/30">
                                  {msg.booking_data.origin_code}
                                </span>
                              )}
                              <ArrowRight className="w-3 h-3 text-cyan-400" />
                              <span>{msg.booking_data.destination}</span>
                              {msg.booking_data.dest_code && (
                                <span className="font-mono text-[10px] text-purple-300 px-1.5 py-0.5 rounded bg-purple-950/80 border border-purple-500/30">
                                  {msg.booking_data.dest_code}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>

                        {msg.booking_data.date && (
                          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-slate-900 border border-slate-700 text-[11px] font-mono text-slate-300">
                            <Calendar className="w-3.5 h-3.5 text-cyan-400" />
                            <span>{msg.booking_data.date}</span>
                          </div>
                        )}
                      </div>

                      {/* Direct Redirection Button */}
                      {(msg.url || msg.booking_data.url) && (
                        <a
                          href={msg.url || msg.booking_data.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 via-teal-600 to-indigo-600 hover:from-cyan-500 hover:via-teal-500 hover:to-indigo-500 text-white font-bold text-xs tracking-wide transition-all shadow-md hover:shadow-cyan-500/25 active:scale-95 text-center"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                          <span>Open {msg.booking_data.site || 'Portal'} with Pre-filled Flight ↗</span>
                        </a>
                      )}

                      {/* Portal Selection Chips if awaiting site */}
                      {msg.booking_data.awaiting_site && onQuickReply && (
                        <div className="space-y-1.5 pt-1">
                          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                            Tap Preferred Booking Portal:
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {['Google Flights', 'MakeMyTrip', 'Skyscanner', 'Expedia'].map((site) => (
                              <button
                                key={site}
                                onClick={() => onQuickReply(site)}
                                className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 hover:border-cyan-400 text-[11px] font-semibold text-slate-200 hover:text-cyan-300 transition active:scale-95"
                              >
                                {site}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Destination Suggestion Chips if awaiting destination */}
                      {msg.booking_data.awaiting_destination && onQuickReply && (
                        <div className="space-y-1.5 pt-1">
                          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                            Quick Destination Responses:
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {['To Delhi tomorrow', 'To Mumbai on Friday', 'To Goa next week', 'To Dubai on MakeMyTrip'].map((prompt) => (
                              <button
                                key={prompt}
                                onClick={() => onQuickReply(prompt)}
                                className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 hover:border-cyan-400 text-[11px] font-medium text-slate-300 hover:text-cyan-300 transition active:scale-95"
                              >
                                {prompt}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Card Action Controls (Hover Reveal) */}
                  <div className={`mt-2 flex items-center gap-1 pt-1 opacity-80 group-hover:opacity-100 transition-opacity ${isUser ? 'justify-end' : 'justify-start'}`}>
                    <button
                      onClick={() => handleCopy(msg.id, msg.content)}
                      className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-cyan-300 text-[11px] transition"
                      title="Copy to clipboard"
                    >
                      {copiedId === msg.id ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>

                    {!isUser && (
                      <button
                        onClick={() => handlePlayAudio(msg.id, msg.content)}
                        className={`p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-cyan-300 text-[11px] transition ${
                          speakingMsgId === msg.id ? 'text-cyan-400 animate-pulse' : ''
                        }`}
                        title="Replay speech audio"
                      >
                        <Volume2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Contextual Smart Follow-Up Suggestions for Assistant Messages */}
                {!isUser && onQuickReply && (
                  <div className="flex items-center gap-1.5 pt-1 overflow-x-auto no-scrollbar">
                    <button
                      onClick={() => onQuickReply('Tell me more about this')}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-900/60 hover:bg-slate-800 border border-slate-700/60 hover:border-cyan-500/40 text-[10px] font-medium text-slate-400 hover:text-cyan-300 transition shrink-0"
                    >
                      <ArrowRight className="w-2.5 h-2.5" />
                      <span>Elaborate</span>
                    </button>
                    <button
                      onClick={() => onQuickReply('What can you see in front of the camera?')}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-900/60 hover:bg-slate-800 border border-slate-700/60 hover:border-cyan-500/40 text-[10px] font-medium text-slate-400 hover:text-cyan-300 transition shrink-0"
                    >
                      <Zap className="w-2.5 h-2.5 text-cyan-400" />
                      <span>Check Camera</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* State Indicators */}
        {state === 'THINKING' && (
          <div className="flex items-center gap-2 text-xs font-mono text-amber-300 bg-amber-950/40 border border-amber-500/40 px-3.5 py-2 rounded-xl w-fit animate-pulse">
            <span className="animate-spin text-sm">?</span>
            <span>Synthesizing neural model & planning action...</span>
          </div>
        )}
        {state === 'EXECUTING' && (
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-300 bg-cyan-950/40 border border-cyan-500/40 px-3.5 py-2 rounded-xl w-fit animate-pulse">
            <Zap className="w-3.5 h-3.5 text-cyan-400" />
            <span>Executing system automation tool...</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
};
