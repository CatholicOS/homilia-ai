import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { chat } from '@/services/api';
import ReactMarkdown from 'react-markdown';

type Msg = { role: 'user' | 'assistant'; content: string };

export default function ChatPage() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState('');

  const m = useMutation({
    mutationFn: async (text: string) => {
      const parishId = localStorage.getItem('selectedParishId') || undefined;
      return chat(text, undefined, parishId);
    },
    onSuccess: (data) => {
      setMessages((prev) => [...prev, { role: 'assistant', content: data.response }]);
    },
  });

  const onSend = () => {
    if (!input.trim() || m.isPending) return;
    const text = input.trim();
    setMessages((prev) => [...prev, { role: 'user', content: text }]);
    setInput('');
    m.mutate(text);
  };

  return (
    <div className="container-max py-10 md:py-16">
      <div className="max-w-3xl mx-auto">
        <h2 className="text-3xl font-semibold text-white mb-6">Ask a question</h2>
        <div className="card p-4 md:p-6 space-y-6" aria-live="polite" aria-busy={m.isPending}>
          <div className="space-y-4" role="log">
            {messages.map((msg, idx) => (
              <div key={idx} className={msg.role === 'user' ? 'text-zinc-200' : 'text-zinc-100'}>
                {msg.role === 'assistant' ? (
                  <div className="prose prose-invert max-w-none prose-headings:text-white prose-a:text-[var(--color-accent)]">
                    <ReactMarkdown
                      components={{
                        a: ({ node, ...props }) => (
                          <a
                            {...props}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={`text-[var(--color-accent)] underline underline-offset-4 decoration-2 hover:opacity-80 ${
                              (props as any).className || ''
                            }`}
                          >
                            {props.children}
                          </a>
                        ),
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <div className="italic text-zinc-300">{msg.content}</div>
                )}
              </div>
            ))}
            {m.isPending && (
              <div className="text-zinc-300">
                <span className="italic animate-pulse">Thinking…</span>
              </div>
            )}
          </div>
          <div className="flex gap-2">
            <input
              className="flex-1 bg-zinc-950 border border-zinc-700 rounded-md px-3 py-3 disabled:opacity-60"
              placeholder="Type your question…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && onSend()}
              aria-label="Your question"
              disabled={m.isPending}
            />
            <button className="btn btn-primary" onClick={onSend} disabled={m.isPending} aria-label="Send message">
              {m.isPending ? 'Sending…' : 'Send'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

