import React, { useEffect, useRef } from 'react';
import { Bot, User, CheckCircle2, AlertCircle, Wrench, Volume2, Square } from 'lucide-react';
import { ChatMessage, AssistantState } from '../types';

interface ChatViewProps {
  messages: ChatMessage[];
  state: AssistantState;
  onBargeIn: () => void;
}

export const ChatView: React.FC<ChatViewProps> = ({ messages, state, onBargeIn }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, state]);

  const lastAssistantMsg = [...messages].reverse().find((m) => m.role === 'assistant');

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden relative">
      {/* Live Speaking Subtitle Banner with Barge-in Interruption */}
      {state === 'SPEAKING' && lastAssistantMsg && (
        <div className="absolute top-2 left-4 right-4 z-20 flex items-center justify-between p-3 rounded-xl bg-cyan-950/90 border border-cyan-400/50 shadow-lg shadow-cyan-950/50 backdrop-blur-md animate-fade-in">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="p-2 rounded-lg bg-cyan-500/20 text-aura-cyan animate-pulse">
              <Volume2 className="w-5 h-5" />
            </div>
            <p className="text-sm font-medium text-slate-100 truncate">
              <span className="text-aura-cyan font-semibold">AEGIS:</span> {lastAssistantMsg.content}
            </p>
          </div>
          <button
            onClick={onBargeIn}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/30 hover:bg-rose-500/50 border border-rose-500/50 text-rose-300 text-xs font-semibold tracking-wide transition-all shadow-sm active:scale-95"
            title="Interrupt speech (Barge-in)"
          >
            <Square className="w-3.5 h-3.5 fill-rose-300" />
            <span>Interrupt</span>
          </button>
        </div>
      )}

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 px-6">
            <div className="w-16 h-16 rounded-2xl bg-cyan-950/50 border border-cyan-500/30 flex items-center justify-center mb-4 text-aura-cyan shadow-lg shadow-cyan-950/40">
              <Bot className="w-8 h-8 animate-pulse" />
            </div>
            <h3 className="text-lg font-bold text-slate-200 mb-1">AEGIS Ready</h3>
            <p className="text-xs text-slate-400 max-w-sm">
              Press and hold <span className="font-semibold text-aura-cyan">Push to Talk</span> or type below. Ask me to open applications, draw in Paint, play music, find objects, set reminders, or create files.
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 max-w-[85%] ${
              msg.role === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
            }`}
          >
            <div
              className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 shadow-md ${
                msg.role === 'user'
                  ? 'bg-blue-600/30 border border-blue-400/40 text-blue-300'
                  : 'bg-cyan-950/80 border border-cyan-500/40 text-aura-cyan'
              }`}
            >
              {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            <div className="flex flex-col gap-1.5">
              <div
                className={`p-3.5 rounded-2xl text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-br from-blue-600 to-indigo-700 text-white shadow-md rounded-tr-none'
                    : 'glass-card text-slate-200 rounded-tl-none border-slate-700/60 shadow-lg'
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>

                {/* Tool Verification Badge */}
                {msg.tool && (
                  <div className="mt-2.5 pt-2 border-t border-slate-700/40 flex items-center gap-1.5 text-xs">
                    <Wrench className="w-3.5 h-3.5 text-cyan-400" />
                    <span className="font-mono text-cyan-300">{msg.tool}</span>
                    {msg.verified ? (
                      <span className="flex items-center gap-1 ml-auto text-emerald-400 font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Verified
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 ml-auto text-amber-400 font-medium">
                        <AlertCircle className="w-3.5 h-3.5" /> Checked
                      </span>
                    )}
                  </div>
                )}
              </div>

              <span className="text-[10px] text-slate-500 px-1">
                {msg.timestamp} {msg.isVoice ? '• Voice' : ''}
              </span>
            </div>
          </div>
        ))}

        {/* State Indicator */}
        {state === 'THINKING' && (
          <div className="flex items-center gap-2 text-xs font-mono text-aura-amber bg-amber-950/30 border border-amber-500/30 px-3 py-1.5 rounded-lg w-fit">
            <span className="animate-spin text-sm">✦</span> Reasoning & planning action...
          </div>
        )}
        {state === 'EXECUTING' && (
          <div className="flex items-center gap-2 text-xs font-mono text-aura-cyan bg-cyan-950/30 border border-cyan-500/30 px-3 py-1.5 rounded-lg w-fit">
            <span className="animate-pulse text-sm">⚡</span> Executing computer tool...
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
};
