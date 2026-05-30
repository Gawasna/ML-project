import { useEffect, useState, useRef } from 'react';
import Sidebar from '../components/Sidebar';
import CanvasHeader from '../components/CanvasHeader';
import LiveTab from '../components/LiveTab';
import ChatTab from '../components/ChatTab';
import { ChevronDown, Lock } from 'lucide-react';



interface ChatMessage {
  sender: 'user' | 'ai';
  text: string;
  isStreaming?: boolean;
}

export default function Playground() {
  const [hostIp, setHostIp] = useState<string>(() => window.location.hostname || 'localhost');
  const [apiEndpoint, setApiEndpoint] = useState(`http://localhost:3000`);
  const [activeTab, setActiveTab] = useState<'live' | 'chat'>('live');
  const [metricsStatus, setMetricsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([
    { sender: 'ai', text: 'Local AI sandbox ready. Input your prompt to test inference streaming.' }
  ]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [speed, setSpeed] = useState<number>(0);
  const [latency, setLatency] = useState<number>(0);
  const [timeoutVal, setTimeoutVal] = useState<number>(30);
  
  const eventSourceRef = useRef<EventSource | null>(null);

  // Synchronize endpoint change with hostIp state
  useEffect(() => {
    try {
      const url = new URL(apiEndpoint);
      setHostIp(url.hostname);
    } catch (e) {
      // Handle incomplete typing URLs
    }
  }, [apiEndpoint]);

  // Monitor hardware telemetry via SSE
  useEffect(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    setMetricsStatus('connecting');
    const sseUrl = `http://${hostIp}:3000/api/metrics`;

    try {
      const source = new EventSource(sseUrl);
      eventSourceRef.current = source;

      source.onopen = () => {
        setMetricsStatus('connected');
      };

      source.onmessage = (event) => {
        try {
          JSON.parse(event.data);
          // Set values if needed, otherwise ignore metrics state
        } catch (e) {
          console.error('Failed parsing telemetry SSE:', e);
        }
      };

      source.onerror = () => {
        setMetricsStatus('disconnected');
        source.close();
      };
    } catch (e) {
      setMetricsStatus('disconnected');
    }

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [hostIp]);

  // Handle message sending to stream AI response
  const handleSendMessage = async (userPrompt: string) => {
    if (isGenerating) return;

    setIsGenerating(true);
    setChatHistory(prev => [
      ...prev,
      { sender: 'user', text: userPrompt },
      { sender: 'ai', text: '', isStreaming: true }
    ]);

    const startTime = performance.now();
    let receivedTokens = 0;
    
    // Initial static response latency benchmark
    setLatency(Math.floor(80 + Math.random() * 50));

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
                receivedTokens++;

                const elapsedSec = (performance.now() - startTime) / 1000;
                if (elapsedSec > 0) {
                  // Live update Speed (t/s) and Latency in Right Column
                  setSpeed(parseFloat((receivedTokens / elapsedSec).toFixed(1)));
                  setLatency(Math.floor((performance.now() - startTime) / receivedTokens));
                }

                setChatHistory(prev => {
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
      setChatHistory(prev => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last && last.sender === 'ai') {
          last.text = 'Failed to execute inference. Check host connection.';
          last.isStreaming = false;
        }
        return updated;
      });
    } finally {
      setIsGenerating(false);
      setChatHistory(prev => {
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
    <div className="flex bg-[#f1f5f9] min-h-screen font-sans w-full p-4 gap-4 box-border items-start">
      {/* 1. Sidebar Left (NAV_SIDEBAR_CTRL) - Sticky layout for page scroll compatibility */}
      <div className="sticky top-4 shrink-0 h-[calc(100vh-32px)]">
        <Sidebar />
      </div>

      {/* Bento Grid Container - Stretch layout to viewport height */}
      <div className="flex-1 flex gap-4 items-start h-[calc(100vh-32px)] min-h-0">
        
        {/* Cột Ở Giữa: Bento Header Selector + PLAYGROUND_CANVAS_EDITOR */}
        <div className="flex-1 flex flex-col gap-4 h-full min-h-0">
          

          {/* B. PLAYGROUND_CANVAS_EDITOR (fnPZ5) */}
          <div className="bg-white border border-slate-200 rounded-2xl shadow-2xs flex flex-col p-6 box-border gap-4 h-full min-h-0">
            {/* Canvas Header (EKBxA) */}
            <CanvasHeader activeTab={activeTab} onTabChange={setActiveTab} />

            {/* Canvas Area (u03nE) */}
            <div className="bg-[#f8fafc] border border-slate-200 rounded-xl flex flex-col flex-1 min-h-0">
              {activeTab === 'live' ? (
                <LiveTab />
              ) : (
                <ChatTab 
                  hostIp={hostIp} 
                  chatHistory={chatHistory}
                  onSendMessage={handleSendMessage}
                  isGenerating={isGenerating}
                />
              )}
            </div>
          </div>
        </div>

        {/* Cột Bên Phải: Config, Connection & Analytics - Stretch height */}
        <div className="w-85 flex flex-col gap-4 shrink-0 h-full min-h-0">
          
          {/* A. Bento Network Config (h9G2lJ) */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-2xs flex flex-col gap-4 shrink-0">
            <h3 className="text-sm font-extrabold text-slate-800">Network Config</h3>
            
            <div className="flex flex-col gap-1.5 w-full">
              <label className="text-[10px] font-bold text-slate-550 uppercase">API Endpoint</label>
              <div className="bg-[#f8fafc] border border-slate-200 rounded-lg px-3 py-2 w-full">
                <input 
                  type="text" 
                  value={apiEndpoint} 
                  onChange={(e) => setApiEndpoint(e.target.value)}
                  className="bg-transparent border-none text-slate-800 font-medium text-xs outline-none w-full"
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5 w-full">
              <label className="text-[10px] font-bold text-slate-550 uppercase">Access Token</label>
              <div className="bg-[#f8fafc] border border-slate-200 rounded-lg px-3 py-2 flex items-center justify-between w-full">
                <span className="text-slate-400 font-medium text-xs tracking-widest select-none">••••••••••••••••••••</span>
                <Lock size={12} className="text-slate-450" />
              </div>
            </div>

            <div className="flex flex-col gap-1.5 w-full">
              <div className="flex justify-between items-center text-[10px] font-bold text-slate-550 uppercase">
                <span>Connection Timeout</span>
                <span className="text-indigo-600 font-mono font-bold text-[11px]">{timeoutVal}s</span>
              </div>
              <div className="flex flex-col justify-center h-6 w-full relative">
                <input 
                  type="range" 
                  min="5" 
                  max="120" 
                  step="5"
                  value={timeoutVal} 
                  onChange={(e) => setTimeoutVal(parseInt(e.target.value))}
                  className="w-full h-1.5 bg-slate-100 rounded-full appearance-none outline-none cursor-pointer accent-indigo-650"
                  style={{
                    background: `linear-gradient(to right, #6366f1 0%, #6366f1 ${((timeoutVal - 5) / 115) * 100}%, #e2e8f0 ${((timeoutVal - 5) / 115) * 100}%, #e2e8f0 100%)`
                  }}
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5 w-full">
              <label className="text-[10px] font-bold text-slate-550 uppercase">Protocol</label>
              <div className="bg-[#f8fafc] border border-slate-200 rounded-lg px-3 py-2 flex items-center justify-between w-full cursor-pointer">
                <span className="text-slate-800 font-bold text-xs">WebSockets (WSS)</span>
                <ChevronDown size={14} className="text-slate-455" />
              </div>
            </div>
          </div>

          {/* B. Bento Activing Connection (mL50H) - Scrollbars completely disabled */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-2xs flex flex-col gap-3 shrink-0">
            <h3 className="text-sm font-extrabold text-slate-800">Activing Connection</h3>
            
            <div className="flex flex-col gap-2 w-full">
              <div className="bg-[#f8fafc] border border-slate-100 rounded-lg p-2.5 flex items-center gap-3 w-full">
                <span className={`w-2 h-2 rounded-full bg-emerald-500 ${metricsStatus === 'connected' ? 'animate-pulse shadow-sm shadow-emerald-400' : ''}`}></span>
                <div className="flex-1 min-w-0">
                  <h4 className="text-xs font-bold text-slate-800 truncate">Host Server Gateway</h4>
                  <p className="text-[9px] font-mono text-slate-400 truncate mt-0.5">http://{hostIp}:3000</p>
                </div>
              </div>

              <div className="bg-[#f8fafc] border border-slate-100 rounded-lg p-2.5 flex items-center gap-3 w-full">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <div className="flex-1 min-w-0">
                  <h4 className="text-xs font-bold text-slate-800 truncate">Developer Console</h4>
                  <p className="text-[9px] font-mono text-slate-400 truncate mt-0.5">Client ID: dev_sandbox_node</p>
                </div>
              </div>

              <div className="bg-[#f8fafc] border border-slate-100 rounded-lg p-2.5 flex items-center gap-3 w-full">
                <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
                <div className="flex-1 min-w-0">
                  <h4 className="text-xs font-bold text-slate-800 truncate">LAN Client (Listening)</h4>
                  <p className="text-[9px] font-mono text-slate-400 truncate mt-0.5">Waiting for hardware handshake</p>
                </div>
              </div>
            </div>
          </div>

          {/* C. Bento Analytics (jdaul) - VRAM chart removed, height stretched */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-2xs flex flex-col gap-4 flex-1 min-h-0">
            <h3 className="text-sm font-extrabold text-slate-800">Live Analytics</h3>
            
            <div className="grid grid-cols-2 gap-3 w-full">
              <div className="bg-[#f8fafc] border border-slate-200 rounded-lg p-3 flex flex-col gap-1">
                <span className="text-[9px] text-slate-400 font-semibold uppercase">Speed</span>
                <span className="text-sm font-extrabold text-indigo-600 font-mono">
                  {isGenerating ? `${speed} t/s` : '54.2 t/s'}
                </span>
              </div>
              <div className="bg-[#f8fafc] border border-slate-200 rounded-lg p-3 flex flex-col gap-1">
                <span className="text-[9px] text-slate-400 font-semibold uppercase">Latency</span>
                <span className="text-sm font-extrabold text-slate-800 font-mono">
                  {isGenerating ? `${latency} ms` : '120 ms'}
                </span>
              </div>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
