import { useEffect, useState, useRef, useCallback } from 'react';
import Sidebar from '../components/Sidebar';
import CanvasHeader from '../components/CanvasHeader';
import LiveTab from '../components/LiveTab';
import type { InferenceConfig } from '../components/LiveTab';
import ChatTab from '../components/ChatTab';
import { Eye, EyeOff, Laptop } from 'lucide-react';
import { applyWrapper } from '../utils/promptWrapper';

interface ChatMessage {
  sender: 'user' | 'ai';
  text: string;
  isStreaming?: boolean;
}

interface HardwareMetrics {
  cpu: { load: number; temp: number };
  memory: { total: number; active: number; percentage: number };
  gpu?: { name: string; memTotal: number; memUsed: number; load: number };
  activeConnections: number;
  activeIps: string[];
}

// ─── Conversation cache helpers (TTL = 3 hours) ────────────────────────────
const CACHE_KEY = 'ml_chat_history';
const CACHE_TTL_MS = 3 * 60 * 60 * 1000; // 3 hours

const INITIAL_MESSAGE: ChatMessage = {
  sender: 'ai',
  text: 'Local AI sandbox ready. Input your prompt to test inference streaming.',
};

function loadCachedHistory(): ChatMessage[] {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return [INITIAL_MESSAGE];
    const { messages, savedAt } = JSON.parse(raw) as { messages: ChatMessage[]; savedAt: number };
    if (Date.now() - savedAt > CACHE_TTL_MS) {
      localStorage.removeItem(CACHE_KEY);
      return [INITIAL_MESSAGE];
    }
    return messages.length > 0 ? messages : [INITIAL_MESSAGE];
  } catch {
    return [INITIAL_MESSAGE];
  }
}

function saveCachedHistory(messages: ChatMessage[]) {
  try {
    // Never persist a message that is still streaming
    const stable = messages.map(m => ({ ...m, isStreaming: false }));
    localStorage.setItem(CACHE_KEY, JSON.stringify({ messages: stable, savedAt: Date.now() }));
  } catch { /* quota exceeded — ignore */ }
}

// ─── Env config ────────────────────────────────────────────────────────────
// Start blank — user must configure before connecting
const DEFAULT_ENDPOINT = import.meta.env.VITE_API_ENDPOINT || (typeof window !== 'undefined' ? `http://${window.location.hostname}:3000` : '');
const DEFAULT_TOKEN = import.meta.env.VITE_ACCESS_TOKEN || '';

const getInitialEndpoint = () => {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('bento_api_endpoint');
    if (saved) return saved;
  }
  return DEFAULT_ENDPOINT;
};

export default function Playground() {
  const [apiEndpoint, setApiEndpoint] = useState<string>(getInitialEndpoint);
  const [accessToken, setAccessToken] = useState(DEFAULT_TOKEN);
  const [showToken, setShowToken] = useState(false);
  const [hostIp, setHostIp] = useState<string>('localhost');
  const [activeTab, setActiveTab] = useState<'live' | 'chat'>('live');
  const [metricsStatus, setMetricsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');

  // Hardware metrics from WS
  const [hwMetrics, setHwMetrics] = useState<HardwareMetrics | null>(null);
  const [activeIps, setActiveIps] = useState<string[]>([]);

  const [models, setModels] = useState<string[]>(['qwen2.5:3b']);
  const [selectedModel, setSelectedModel] = useState<string>('qwen2.5:3b');
  const [activeWrapperId, setActiveWrapperId] = useState<string | null>('vi'); // default: Vietnamese wrapper

  // Load conversation from cache on first render
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>(loadCachedHistory);
  const [isGenerating, setIsGenerating] = useState(false);

  // Inference performance stats (only meaningful while/after generation)
  const [speed, setSpeed] = useState<number | null>(null);     // tokens/sec
  const [latency, setLatency] = useState<number | null>(null); // ms/token (TTFT)
  const [totalTokens, setTotalTokens] = useState<number | null>(null);

  const [timeoutVal, setTimeoutVal] = useState<number>(30);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | null>(null);
  // Track whether unmount has been signalled to stop auto-reconnect
  const unmountedRef = useRef(false);

  // Persist conversation to localStorage whenever it changes (debounced via ref)
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(() => {
      // Don't persist while a message is actively streaming
      if (!isGenerating) saveCachedHistory(chatHistory);
    }, 500);
    return () => { if (saveTimerRef.current) clearTimeout(saveTimerRef.current); };
  }, [chatHistory, isGenerating]);

  // Persist apiEndpoint
  useEffect(() => {
    localStorage.setItem('bento_api_endpoint', apiEndpoint);
  }, [apiEndpoint]);

  const handleEndpointBlur = () => {
    let val = apiEndpoint.trim();
    if (!val) {
      val = DEFAULT_ENDPOINT;
    } else {
      val = val.replace(/\/+$/, '');
      if (!/^https?:\/\//i.test(val)) {
        val = 'http://' + val;
      }
      try {
        const url = new URL(val);
        // Default to port 3000 if missed on localhost or IPv4
        if (url.protocol === 'http:' && !url.port && (url.hostname === 'localhost' || /^\d+\.\d+\.\d+\.\d+$/.test(url.hostname))) {
          url.port = '3000';
        }
        val = url.origin;
      } catch {
        val = DEFAULT_ENDPOINT;
      }
    }
    setApiEndpoint(val);
  };

  // Derive Host IP for display when endpoint changes
  useEffect(() => {
    try {
      const url = new URL(apiEndpoint);
      setHostIp(url.hostname);
    } catch { /* ignore partial input */ }
  }, [apiEndpoint]);

  // ── WebSocket: real-time metrics + client tracking ──────────────────────
  useEffect(() => {
    unmountedRef.current = false;

    const clearReconnect = () => {
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
    };
    const clearHeartbeat = () => {
      if (heartbeatRef.current) clearInterval(heartbeatRef.current);
    };
    const closeWs = () => {
      if (wsRef.current) {
        wsRef.current.onclose = null; // suppress onclose → no rogue reconnect
        wsRef.current.close();
        wsRef.current = null;
      }
    };

    setActiveIps([]);
    clearReconnect();
    clearHeartbeat();
    closeWs();

    // Don't attempt connection until both fields are filled
    if (!apiEndpoint.trim() || !accessToken.trim()) {
      setMetricsStatus('disconnected');
      return;
    }

    setMetricsStatus('connecting');

    // Derive ws(s):// from the configured http(s):// endpoint
    const wsUrl = (() => {
      try {
        const url = new URL(apiEndpoint);
        url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
        url.pathname = '/ws';
        url.search = ''; // clear first, then set via searchParams to avoid double-?
        url.searchParams.set('token', accessToken);
        return url.toString();
      } catch {
        return `ws://localhost:3000/ws?token=${encodeURIComponent(accessToken)}`;
      }
    })();

    const connect = () => {
      if (unmountedRef.current) return;

      let ws: WebSocket;
      try {
        ws = new WebSocket(wsUrl);
      } catch {
        // Invalid URL (e.g. user still typing) — retry later
        setMetricsStatus('disconnected');
        reconnectTimerRef.current = setTimeout(connect, 3000);
        return;
      }
      wsRef.current = ws;

      ws.onopen = () => {
        setMetricsStatus('connected');
        heartbeatRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) ws.send('ping');
        }, 30_000);
      };

      ws.onmessage = (event) => {
        // Skip heartbeat echo — backend sends "pong" which is not JSON
        if (typeof event.data === 'string' && event.data === 'pong') return;

        try {
          const data = JSON.parse(event.data as string) as Partial<HardwareMetrics>;
          setHwMetrics(data as HardwareMetrics);
          if (Array.isArray(data.activeIps)) setActiveIps(data.activeIps);
        } catch (e) {
          console.warn('[WS] Unrecognised metrics message:', event.data);
        }
      };

      ws.onerror = () => {
        setMetricsStatus('disconnected');
      };

      ws.onclose = () => {
        setMetricsStatus('disconnected');
        clearHeartbeat();
        if (!unmountedRef.current) {
          reconnectTimerRef.current = setTimeout(connect, 3000);
        }
      };
    };

    connect();

    return () => {
      unmountedRef.current = true;
      clearReconnect();
      clearHeartbeat();
      closeWs();
    };
  }, [apiEndpoint, accessToken]);

  // Fetch Ollama models on WS connect
  useEffect(() => {
    if (metricsStatus !== 'connected') return;

    const fetchModels = async () => {
      try {
        const response = await fetch(`${apiEndpoint}/api/ai/models`, {
          headers: { Authorization: `Bearer ${accessToken}` },
        });
        if (response.ok) {
          const data = await response.json() as { models?: string[] };
          if (data.models && data.models.length > 0) {
            setModels(data.models);
            setSelectedModel(prev => data.models!.includes(prev) ? prev : data.models![0]);
          }
        }
      } catch (e) {
        console.warn('[Models] Fetch failed (backend unreachable or blocked by browser extension):', e);
      }
    };

    fetchModels();
  }, [apiEndpoint, accessToken, metricsStatus]);

  // ── Inference handler ───────────────────────────────────────────────────
  const handleSendMessage = useCallback(async (userPrompt: string) => {
    if (isGenerating) return;

    setIsGenerating(true);
    setSpeed(null);
    setLatency(null);
    setTotalTokens(null);

    setChatHistory(prev => [
      ...prev,
      { sender: 'user', text: userPrompt },
      { sender: 'ai', text: '', isStreaming: true },
    ]);

    const startTime = performance.now();
    let firstTokenTime: number | null = null;
    let receivedTokens = 0;

    // Apply active wrapper prefix before sending
    const wrappedPrompt = applyWrapper(userPrompt, activeWrapperId);

    try {
      const response = await fetch(`${apiEndpoint}/api/ai/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ prompt: wrappedPrompt, model: selectedModel }),
      });

      if (response.status === 401) throw new Error('Unauthorized: Invalid access token.');
      if (!response.body) throw new Error('Streaming not supported by this browser.');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let finished = false;
      let accumulatedText = '';
      let buffer = '';

      while (!finished) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? ''; // keep incomplete last line

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const dataStr = line.slice(6).trim();

          if (dataStr === '[DONE]') { finished = true; break; }

          try {
            const parsed = JSON.parse(dataStr);
            if (parsed.token) {
              // TTFT: time from request sent to first token received
              if (firstTokenTime === null) {
                firstTokenTime = performance.now();
                setLatency(Math.round(firstTokenTime - startTime));
              }

              accumulatedText += parsed.token;
              receivedTokens++;

              const elapsedSec = (performance.now() - startTime) / 1000;
              if (elapsedSec > 0) {
                setSpeed(parseFloat((receivedTokens / elapsedSec).toFixed(1)));
                setTotalTokens(receivedTokens);
              }

              setChatHistory(prev => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last?.sender === 'ai') last.text = accumulatedText;
                return updated;
              });
            }
          } catch { /* skip unparseable line */ }
        }
      }
    } catch (error: any) {
      setChatHistory(prev => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last?.sender === 'ai') {
          last.text = error.message || 'Inference failed. Check host connection.';
          last.isStreaming = false;
        }
        return updated;
      });
    } finally {
      setIsGenerating(false);
      setChatHistory(prev => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last?.sender === 'ai') last.isStreaming = false;
        return updated;
      });
    }
  }, [isGenerating, apiEndpoint, accessToken, selectedModel]);

  // ── Derived display values for Live Analytics ───────────────────────────
  const cpuLoad = hwMetrics?.cpu.load ?? null;
  const cpuTemp = hwMetrics?.cpu.temp ?? null;
  const memPct  = hwMetrics?.memory.percentage ?? null;
  const memUsedGb = hwMetrics ? (hwMetrics.memory.active / 1_073_741_824).toFixed(1) : null;
  const memTotalGb = hwMetrics ? (hwMetrics.memory.total / 1_073_741_824).toFixed(0) : null;

  return (
    <div className="flex bg-[#f1f5f9] min-h-screen font-sans w-full p-4 gap-4 box-border items-start">
      {/* Sidebar */}
      <div className="sticky top-4 shrink-0 h-[calc(100vh-32px)]">
        <Sidebar />
      </div>

      {/* Bento Grid */}
      <div className="flex-1 flex gap-4 items-start h-[calc(100vh-32px)] min-h-0">

        {/* Center column */}
        <div className="flex-1 flex flex-col gap-4 h-full min-h-0">
          <div className="bg-white border border-slate-200 rounded-2xl shadow-2xs flex flex-col p-6 box-border gap-4 h-full min-h-0">
            <CanvasHeader
              activeTab={activeTab}
              onTabChange={setActiveTab}
              selectedModel={selectedModel}
              setSelectedModel={setSelectedModel}
              models={models}
              activeWrapperId={activeWrapperId}
              onWrapperChange={setActiveWrapperId}
            />
            <div className="bg-[#f8fafc] border border-slate-200 rounded-xl flex flex-col flex-1 min-h-0">
              {activeTab === 'live' ? (
                <LiveTab inferenceConfig={{
                  apiEndpoint,
                  accessToken,
                  selectedModel,
                  activeWrapperId,
                } satisfies InferenceConfig} />
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

        {/* Right column */}
        <div className="w-85 flex flex-col gap-4 shrink-0 h-full min-h-0 overflow-y-auto">

          {/* A. Network Config */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-2xs flex flex-col gap-4 shrink-0">
            <h3 className="text-sm font-extrabold text-slate-800">Network Config</h3>

            <div className="flex flex-col gap-1.5 w-full">
              <label className="text-[10px] font-bold text-slate-500 uppercase">API Endpoint</label>
              <div className="bg-[#f8fafc] border border-slate-200 rounded-lg px-3 py-2 w-full">
                <input
                  type="text"
                  value={apiEndpoint}
                  onChange={(e) => setApiEndpoint(e.target.value)}
                  onBlur={handleEndpointBlur}
                  onKeyDown={(e) => { if (e.key === 'Enter') handleEndpointBlur(); }}
                  className="bg-transparent border-none text-slate-800 font-medium text-xs outline-none w-full"
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5 w-full">
              <label className="text-[10px] font-bold text-slate-500 uppercase">Access Token</label>
              <div className="bg-[#f8fafc] border border-slate-200 rounded-lg px-3 py-2 flex items-center justify-between w-full">
                <input
                  type={showToken ? 'text' : 'password'}
                  value={accessToken}
                  onChange={(e) => setAccessToken(e.target.value)}
                  className="bg-transparent border-none text-slate-800 font-medium text-xs outline-none flex-1"
                  placeholder="Enter access token"
                />
                <button
                  type="button"
                  onClick={() => setShowToken(v => !v)}
                  className="text-slate-400 hover:text-slate-600 cursor-pointer transition-colors duration-100 flex items-center justify-center shrink-0 ml-1.5"
                >
                  {showToken ? <EyeOff size={13} /> : <Eye size={13} />}
                </button>
              </div>
            </div>

            <div className="flex flex-col gap-1.5 w-full">
              <div className="flex justify-between items-center text-[10px] font-bold text-slate-500 uppercase">
                <span>Connection Timeout</span>
                <span className="text-indigo-600 font-mono font-bold text-[11px]">{timeoutVal}s</span>
              </div>
              <input
                type="range" min="5" max="120" step="5"
                value={timeoutVal}
                onChange={(e) => setTimeoutVal(parseInt(e.target.value))}
                className="w-full h-1.5 rounded-full appearance-none outline-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right, #6366f1 0%, #6366f1 ${((timeoutVal - 5) / 115) * 100}%, #e2e8f0 ${((timeoutVal - 5) / 115) * 100}%, #e2e8f0 100%)`
                }}
              />
            </div>

            <div className="flex flex-col gap-1.5 w-full">
              <label className="text-[10px] font-bold text-slate-500 uppercase">Protocol</label>
              <div className="bg-[#f8fafc] border border-slate-200 rounded-lg px-3 py-2">
                <span className="text-slate-800 font-bold text-xs">WebSocket / HTTP SSE</span>
              </div>
            </div>
          </div>

          {/* B. Active Connections */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-2xs flex flex-col gap-3 shrink-0">
            <h3 className="text-sm font-extrabold text-slate-800">Active Connections</h3>

            <div className="flex flex-col gap-2 w-full max-h-[220px] overflow-y-auto pr-1 select-none">
              {/* Host gateway status */}
              <div className="bg-[#f8fafc] border border-slate-100 rounded-lg p-2.5 flex items-center gap-3 w-full">
                <span className={`w-2 h-2 rounded-full shrink-0 ${
                  metricsStatus === 'connected'
                    ? 'bg-emerald-500 animate-pulse shadow-sm shadow-emerald-400'
                    : metricsStatus === 'connecting'
                    ? 'bg-amber-400 animate-pulse'
                    : 'bg-rose-500 animate-pulse'
                }`} />
                <div className="flex-1 min-w-0">
                  <h4 className="text-xs font-bold text-slate-800 truncate">Host Server Gateway</h4>
                  <p className="text-[9px] font-mono text-slate-400 truncate mt-0.5">{apiEndpoint}</p>
                </div>
                <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded-full shrink-0 ${
                  metricsStatus === 'connected' ? 'bg-emerald-50 text-emerald-700' :
                  metricsStatus === 'connecting' ? 'bg-amber-50 text-amber-700' :
                  'bg-rose-50 text-rose-700'
                }`}>
                  {metricsStatus.toUpperCase()}
                </span>
              </div>

              {/* LAN client list */}
              {activeIps.length === 0 ? (
                <div className="bg-[#f8fafc] border border-slate-100 rounded-lg p-2.5 flex items-center gap-3 w-full opacity-60">
                  <span className="w-2 h-2 rounded-full bg-slate-300 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <h4 className="text-xs font-bold text-slate-700 truncate">No Clients Connected</h4>
                    <p className="text-[9px] font-mono text-slate-400 truncate mt-0.5">Waiting for WebSocket handshake</p>
                  </div>
                </div>
              ) : (
                activeIps.map((ip, idx) => {
                  const isMe = ip === '127.0.0.1' || ip === window.location.hostname || ip === 'localhost';
                  return (
                    <div key={`${ip}-${idx}`} className="bg-[#f8fafc] border border-slate-100 rounded-lg p-2.5 flex items-center gap-3 w-full">
                      <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse shadow-xs shadow-indigo-400 shrink-0" />
                      <div className="flex-1 min-w-0 flex items-center gap-2 justify-between">
                        <div className="min-w-0 flex-1">
                          <h4 className="text-xs font-bold text-slate-800 truncate flex items-center gap-1.5">
                            LAN Client {idx + 1}
                            {isMe && <span className="text-[8px] px-1 bg-indigo-50 text-indigo-600 rounded border border-indigo-100">You</span>}
                          </h4>
                          <p className="text-[9px] font-mono text-slate-500 truncate mt-0.5">IP: {ip}</p>
                        </div>
                        <Laptop size={12} className="text-slate-400 shrink-0" />
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* C. Live Analytics */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-2xs flex flex-col gap-4 shrink-0">
            <h3 className="text-sm font-extrabold text-slate-800">Live Analytics</h3>

            {/* Inference stats */}
            <div>
              <p className="text-[9px] font-bold text-slate-400 uppercase mb-2">Inference</p>
              <div className="grid grid-cols-3 gap-2">
                <div className="bg-[#f8fafc] border border-slate-200 rounded-lg p-3 flex flex-col gap-0.5">
                  <span className="text-[9px] text-slate-400 font-semibold uppercase">Speed</span>
                  <span className="text-sm font-extrabold text-indigo-600 font-mono">
                    {speed !== null ? `${speed}` : '—'}
                  </span>
                  <span className="text-[8px] text-slate-400 font-mono">tok/s</span>
                </div>
                <div className="bg-[#f8fafc] border border-slate-200 rounded-lg p-3 flex flex-col gap-0.5">
                  <span className="text-[9px] text-slate-400 font-semibold uppercase">TTFT</span>
                  <span className="text-sm font-extrabold text-slate-800 font-mono">
                    {latency !== null ? `${latency}` : '—'}
                  </span>
                  <span className="text-[8px] text-slate-400 font-mono">ms</span>
                </div>
                <div className="bg-[#f8fafc] border border-slate-200 rounded-lg p-3 flex flex-col gap-0.5">
                  <span className="text-[9px] text-slate-400 font-semibold uppercase">Tokens</span>
                  <span className="text-sm font-extrabold text-slate-800 font-mono">
                    {totalTokens !== null ? `${totalTokens}` : '—'}
                  </span>
                  <span className="text-[8px] text-slate-400 font-mono">total</span>
                </div>
              </div>
            </div>

            {/* Hardware metrics from WS */}
            <div>
              <p className="text-[9px] font-bold text-slate-400 uppercase mb-2">Hardware</p>
              <div className="flex flex-col gap-2">

                {/* CPU */}
                <div className="bg-[#f8fafc] border border-slate-200 rounded-lg p-3">
                  <div className="flex justify-between items-center mb-1.5">
                    <span className="text-[9px] text-slate-400 font-semibold uppercase">CPU Load</span>
                    <div className="flex items-center gap-2">
                      {cpuTemp !== null && cpuTemp > 0 && (
                        <span className="text-[9px] font-mono text-slate-500">{cpuTemp.toFixed(0)}°C</span>
                      )}
                      <span className="text-xs font-extrabold text-slate-800 font-mono">
                        {cpuLoad !== null ? `${cpuLoad.toFixed(1)}%` : '—'}
                      </span>
                    </div>
                  </div>
                  <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{
                        width: cpuLoad !== null ? `${Math.min(cpuLoad, 100)}%` : '0%',
                        background: cpuLoad !== null && cpuLoad > 80
                          ? '#ef4444'
                          : cpuLoad !== null && cpuLoad > 60
                          ? '#f59e0b'
                          : '#6366f1',
                      }}
                    />
                  </div>
                </div>

                {/* RAM */}
                <div className="bg-[#f8fafc] border border-slate-200 rounded-lg p-3">
                  <div className="flex justify-between items-center mb-1.5">
                    <span className="text-[9px] text-slate-400 font-semibold uppercase">RAM</span>
                    <span className="text-xs font-extrabold text-slate-800 font-mono">
                      {memUsedGb !== null ? `${memUsedGb} / ${memTotalGb} GB` : '—'}
                    </span>
                  </div>
                  <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{
                        width: memPct !== null ? `${Math.min(memPct, 100)}%` : '0%',
                        background: memPct !== null && memPct > 85 ? '#ef4444' : '#10b981',
                      }}
                    />
                  </div>
                </div>

                {/* GPU (conditional) */}
                {hwMetrics?.gpu && (
                  <div className="bg-[#f8fafc] border border-slate-200 rounded-lg p-3">
                    <div className="flex justify-between items-center mb-1.5">
                      <span className="text-[9px] text-slate-400 font-semibold uppercase">GPU</span>
                      <span className="text-xs font-extrabold text-slate-800 font-mono">
                        {hwMetrics.gpu.load.toFixed(0)}%
                      </span>
                    </div>
                    <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-violet-500 rounded-full transition-all duration-700"
                        style={{ width: `${Math.min(hwMetrics.gpu.load, 100)}%` }}
                      />
                    </div>
                    <p className="text-[8px] font-mono text-slate-400 mt-1 truncate">
                      {hwMetrics.gpu.name} — VRAM {(hwMetrics.gpu.memUsed / 1024).toFixed(1)} / {(hwMetrics.gpu.memTotal / 1024).toFixed(0)} GB
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
