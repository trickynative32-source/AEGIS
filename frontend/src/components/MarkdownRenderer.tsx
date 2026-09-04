import React, { useState } from 'react';
import { Copy, Check, Terminal } from 'lucide-react';

interface MarkdownRendererProps {
  content: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const handleCopyCode = (code: string, index: number) => {
    navigator.clipboard.writeText(code);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  // Split content into code blocks vs standard text blocks
  const parts: Array<{ type: 'code' | 'text'; content: string; language?: string }> = [];
  const codeBlockRegex = new RegExp('```([a-zA-Z0-9_-]*)\\n([\\s\\S]*?)```', 'g');
  let lastIndex = 0;
  let match;

  while ((match = codeBlockRegex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      parts.push({
        type: 'text',
        content: content.slice(lastIndex, match.index)
      });
    }
    parts.push({
      type: 'code',
      language: match[1] || 'code',
      content: match[2].trimEnd()
    });
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < content.length) {
    parts.push({
      type: 'text',
      content: content.slice(lastIndex)
    });
  }

  const renderInlineFormattedText = (text: string): React.ReactNode => {
    // Process inline bold, italic, code
    const inlineRegex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
    const segments = text.split(inlineRegex);

    return segments.map((seg, i) => {
      if (seg.startsWith('**') && seg.endsWith('**')) {
        return <strong key={i} className="font-bold text-slate-100">{seg.slice(2, -2)}</strong>;
      }
      if (seg.startsWith('*') && seg.endsWith('*')) {
        return <em key={i} className="italic text-slate-300">{seg.slice(1, -1)}</em>;
      }
      if (seg.startsWith('`') && seg.endsWith('`')) {
        return (
          <code key={i} className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700/80 font-mono text-[12px] text-cyan-300">
            {seg.slice(1, -1)}
          </code>
        );
      }
      return seg;
    });
  };

  const renderTextBlock = (text: string, keyPrefix: string | number) => {
    const lines = text.split('\n');
    const elements: React.ReactNode[] = [];

    lines.forEach((line, lineIdx) => {
      const trimmed = line.trim();

      if (!trimmed) {
        elements.push(<div key={`${keyPrefix}-${lineIdx}`} className="h-2" />);
        return;
      }

      // Headers
      if (trimmed.startsWith('### ')) {
        elements.push(
          <h3 key={`${keyPrefix}-${lineIdx}`} className="text-sm font-bold text-cyan-300 mt-3 mb-1">
            {renderInlineFormattedText(trimmed.slice(4))}
          </h3>
        );
      } else if (trimmed.startsWith('## ')) {
        elements.push(
          <h2 key={`${keyPrefix}-${lineIdx}`} className="text-base font-bold text-slate-100 mt-3.5 mb-1.5 border-b border-slate-800 pb-1">
            {renderInlineFormattedText(trimmed.slice(3))}
          </h2>
        );
      } else if (trimmed.startsWith('# ')) {
        elements.push(
          <h1 key={`${keyPrefix}-${lineIdx}`} className="text-lg font-extrabold text-cyan-400 mt-4 mb-2">
            {renderInlineFormattedText(trimmed.slice(2))}
          </h1>
        );
      } else if (trimmed.startsWith('#### ')) {
        elements.push(
          <h4 key={`${keyPrefix}-${lineIdx}`} className="text-xs font-bold text-slate-200 mt-2 mb-0.5">
            {renderInlineFormattedText(trimmed.slice(5))}
          </h4>
        );
      }
      // Callout / Blockquote
      else if (trimmed.startsWith('> [!NOTE]') || trimmed.startsWith('> [!TIP]')) {
        const isTip = trimmed.includes('TIP');
        elements.push(
          <div key={`${keyPrefix}-${lineIdx}`} className={`my-2 p-2.5 rounded-xl border text-xs ${
            isTip ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-300' : 'bg-cyan-950/30 border-cyan-500/40 text-cyan-300'
          }`}>
            <span className="font-bold uppercase tracking-wider text-[10px] block mb-0.5">
              {isTip ? '💡 Pro Tip' : '📌 Context Note'}
            </span>
          </div>
        );
      } else if (trimmed.startsWith('> ')) {
        elements.push(
          <blockquote key={`${keyPrefix}-${lineIdx}`} className="border-l-2 border-cyan-500/50 pl-3 my-1.5 text-slate-300 italic text-xs">
            {renderInlineFormattedText(trimmed.slice(2))}
          </blockquote>
        );
      }
      // Bullet list items
      else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        elements.push(
          <div key={`${keyPrefix}-${lineIdx}`} className="flex items-start gap-2 my-1 text-xs text-slate-200 pl-1">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-1.5 shrink-0" />
            <div className="leading-relaxed">{renderInlineFormattedText(trimmed.slice(2))}</div>
          </div>
        );
      }
      // Numbered list items
      else if (/^\d+\.\s+/.test(trimmed)) {
        const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
        if (numMatch) {
          elements.push(
            <div key={`${keyPrefix}-${lineIdx}`} className="flex items-start gap-2 my-1 text-xs text-slate-200 pl-1">
              <span className="font-mono text-[11px] font-bold text-cyan-400 shrink-0 mt-0.5">{numMatch[1]}.</span>
              <div className="leading-relaxed">{renderInlineFormattedText(numMatch[2])}</div>
            </div>
          );
        }
      }
      // Regular Paragraph
      else {
        elements.push(
          <p key={`${keyPrefix}-${lineIdx}`} className="text-xs leading-relaxed text-slate-200 my-1">
            {renderInlineFormattedText(line)}
          </p>
        );
      }
    });

    return elements;
  };

  return (
    <div className="markdown-body space-y-1 select-text">
      {parts.map((part, index) => {
        if (part.type === 'code') {
          return (
            <div key={index} className="my-3 rounded-xl border border-slate-800 bg-slate-950 overflow-hidden shadow-md">
              <div className="flex items-center justify-between px-3.5 py-1.5 bg-slate-900/90 border-b border-slate-800 text-[11px] font-mono text-slate-400">
                <div className="flex items-center gap-1.5">
                  <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                  <span className="uppercase text-[10px] font-bold tracking-wider text-cyan-300">{part.language}</span>
                </div>
                <button
                  onClick={() => handleCopyCode(part.content, index)}
                  className="flex items-center gap-1 px-2 py-0.5 rounded-md hover:bg-slate-800 text-slate-300 hover:text-white transition active:scale-95"
                  title="Copy code"
                >
                  {copiedIndex === index ? (
                    <>
                      <Check className="w-3 h-3 text-emerald-400" />
                      <span className="text-[10px] text-emerald-400 font-semibold">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" />
                      <span className="text-[10px]">Copy</span>
                    </>
                  )}
                </button>
              </div>
              <pre className="p-3.5 overflow-x-auto text-[11.5px] font-mono leading-relaxed text-slate-200">
                <code>{part.content}</code>
              </pre>
            </div>
          );
        }

        return <React.Fragment key={index}>{renderTextBlock(part.content, index)}</React.Fragment>;
      })}
    </div>
  );
};
