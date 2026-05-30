import { useState, useEffect, useRef } from 'react';
import { Terminal } from 'lucide-react';
import ChatInput from './ChatInput';

interface ChatMessage {
  sender: 'user' | 'ai';
  text: string;
  isStreaming?: boolean;
}

interface ChatTabProps {
  hostIp?: string;
  chatHistory?: ChatMessage[];
  onSendMessage?: (text: string) => void;
  isGenerating?: boolean;
}

export default function ChatTab({ 
  hostIp = 'localhost',
  chatHistory: propsChatHistory,
  onSendMessage,
  isGenerating: propsIsGenerating
}: ChatTabProps) {
  
  // Local state as fallback if not controlled by parent (e.g. inside Component Warehouse)
  const [localChatHistory, setLocalChatHistory] = useState<ChatMessage[]>([
    { sender: 'ai', text: 'Local AI sandbox ready in light theme. Input your instructions to test inference.' }
  ]);
  const [localIsGenerating, setLocalIsGenerating] = useState(false);
  const [inputText, setInputText] = useState('');
  
  const chatHistory = propsChatHistory || localChatHistory;
  const isGenerating = propsIsGenerating !== undefined ? propsIsGenerating : localIsGenerating;

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const handleLocalSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isGenerating) return;

    const userPrompt = inputText;
    setInputText('');

    if (onSendMessage) {
      onSendMessage(userPrompt);
      return;
    }

    // Standalone fallback execution (for warehouse viewing)
    setLocalIsGenerating(true);
    setLocalChatHistory(prev => [
      ...prev,
      { sender: 'user', text: userPrompt },
      { sender: 'ai', text: '', isStreaming: true }
    ]);

    try {
      const response = await fetch(`http://${hostIp}:3000/api/ai/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: userPrompt })
      });

      if (!response.body) throw new Error('Readable stream unsupported');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let finished = false;
      let accumulatedText = '';

      while (!finished) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim();
            if (dataStr === '[DONE]') {
              finished = true;
              break;
            }

            try {
              const data = JSON.parse(dataStr);
              if (data.token) {
                accumulatedText += data.token;
                setLocalChatHistory(prev => {
                  const updated = [...prev];
                  const last = updated[updated.length - 1];
                  if (last && last.sender === 'ai') {
                    last.text = accumulatedText;
                  }
                  return updated;
                });
              }
            } catch (err) {}
          }
        }
      }
    } catch (error) {
      setLocalChatHistory(prev => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last && last.sender === 'ai') {
          last.text = 'Failed to connect. Make sure your local gateway server is active.';
          last.isStreaming = false;
        }
        return updated;
      });
    } finally {
      setLocalIsGenerating(false);
      setLocalChatHistory(prev => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last && last.sender === 'ai') {
          last.isStreaming = false;
        }
        return updated;
      });
    }
  };

  return (
    <div className="w-full h-full bg-transparent border-none rounded-none p-0 flex flex-col select-none font-sans flex-1 min-h-0">
      {/* Unified Chat Window (CGsoM) - Removed border wrap and filled container */}
      <div className="w-full h-full flex flex-col bg-white rounded-xl shadow-2xs overflow-hidden min-h-0">
        {/* Chat Header (oBMHz) */}
        <div className="h-13 bg-slate-50 border-b border-slate-100 flex items-center justify-between px-5 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-indigo-50 border border-indigo-100 flex items-center justify-center text-xs font-bold text-indigo-600">
              AI
            </div>
            <div>
              <h3 className="text-xs font-bold text-slate-800 leading-none">AI Assistant</h3>
              <p className="text-[9px] text-emerald-500 font-bold flex items-center gap-1 mt-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                Online
              </p>
            </div>
          </div>
          <Terminal size={14} className="text-slate-400" />
        </div>

        {/* Chat History Body (ulg13) */}
        <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-4 bg-white min-h-0">
          {chatHistory.map((msg, index) => (
            <div
              key={index}
              className={`max-w-[80%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed border transition-all duration-150 ${
                msg.sender === 'user'
                  ? 'bg-indigo-50/50 border-indigo-100 text-slate-800 self-end rounded-br-none shadow-3xs'
                  : 'bg-slate-50/60 border-slate-150 text-slate-800 self-start rounded-bl-none shadow-3xs'
              } ${msg.isStreaming ? 'border-purple-200 shadow-purple-50/50 shadow-sm animate-pulse' : ''}`}
            >
              {msg.text || (msg.isStreaming ? <span className="animate-ping font-bold">|</span> : '')}
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>

        {/* Chat Footer (VlHxn) */}
        <div className="h-16 bg-slate-50 border-t border-slate-100 flex items-center justify-center px-5 shrink-0">
          <ChatInput
            value={inputText}
            onChange={setInputText}
            onSubmit={handleLocalSubmit}
            disabled={isGenerating}
            placeholder={isGenerating ? "AI is processing stream..." : "Ask AI to modify pipeline..."}
          />
        </div>
      </div>
    </div>
  );
}
