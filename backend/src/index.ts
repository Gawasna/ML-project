import { Elysia, t } from 'elysia';
import { cors } from '@elysiajs/cors';
import { swagger } from '@elysiajs/swagger';
import si from 'systeminformation';

const PORT = process.env.PORT ? parseInt(process.env.PORT) : 3000;
const HOST = '0.0.0.0';
const ACCESS_TOKEN = process.env.ACCESS_TOKEN || 'ml_secure_sandbox_token_2026';

// WS client registry: wsId -> { ip, ws }
// This is the ground truth for "who is currently connected"
const wsClients = new Map<string, { ip: string; ws: any }>();

function getActiveIps(): string[] {
  return Array.from(new Set(Array.from(wsClients.values()).map(c => c.ip)));
}

// Broadcast latest hardware metrics + active IPs to all connected WS clients
async function broadcastMetrics() {
  if (wsClients.size === 0) return;

  try {
    const [cpuLoad, cpuTemp, mem, gpu] = await Promise.all([
      si.currentLoad(),
      si.cpuTemperature(),
      si.mem(),
      si.graphics(),
    ]);

    const nvidiaGpu = gpu.controllers.find(c =>
      c.vendor.toLowerCase().includes('nvidia') ||
      c.model.toLowerCase().includes('nvidia') ||
      c.model.toLowerCase().includes('rtx') ||
      c.model.toLowerCase().includes('gtx')
    );

    const payload: Record<string, unknown> = {
      cpu: { load: cpuLoad.currentLoad, temp: cpuTemp.main || 0 },
      memory: {
        total: mem.total,
        active: mem.active,
        percentage: (mem.active / mem.total) * 100,
      },
      activeConnections: wsClients.size,
      activeIps: getActiveIps(),
    };

    if (nvidiaGpu) {
      const memUsed = (nvidiaGpu as any).memoryUsed ?? (nvidiaGpu as any).vramUsed ?? 0;
      payload.gpu = {
        name: nvidiaGpu.model,
        memTotal: nvidiaGpu.vram || 0,
        memUsed,
        memFree: (nvidiaGpu.vram || 0) - memUsed,
        load: nvidiaGpu.utilizationGpu || 0,
      };
    }

    const message = JSON.stringify(payload);
    for (const { ws } of wsClients.values()) {
      try { ws.send(message); } catch (_) { /* client already gone */ }
    }
  } catch (err) {
    console.error('[Metrics] Broadcast error:', err);
  }
}

// Single global interval — starts when first client connects, never stops
// (low overhead: exits early when no clients)
setInterval(broadcastMetrics, 1500);

// ─── HTTP token validation helper ────────────────────────────────────────────
function validateToken(request: Request, query: Record<string, string | undefined>): boolean {
  const authHeader = request.headers.get('Authorization');
  if (authHeader?.startsWith('Bearer ')) {
    return authHeader.substring(7) === ACCESS_TOKEN;
  }
  return (query.token ?? query.access_token) === ACCESS_TOKEN;
}

// ─── App ──────────────────────────────────────────────────────────────────────
export const app = new Elysia()
  .use(cors({
    origin: '*',
    methods: ['GET', 'POST', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
  }))
  .use(swagger({
    path: '/docs',
    documentation: {
      info: {
        title: 'Bento ML Studio - API Gateway',
        description: 'BFF for local AI inference and real-time telemetry via WebSocket.',
        version: '2.0.0',
      },
    },
  }))

  // ── Auth middleware for HTTP endpoints ──────────────────────────────────────
  .onBeforeHandle(({ request, set, query }) => {
    const url = new URL(request.url);

    // Skip auth for: docs, OPTIONS, and the WS upgrade endpoint (WS auth handled separately)
    if (
      url.pathname.startsWith('/docs') ||
      url.pathname === '/ws' ||
      request.method === 'OPTIONS'
    ) {
      return;
    }

    if (!validateToken(request, query as Record<string, string | undefined>)) {
      console.warn(`[Security] Unauthorized attempt: ${url.pathname}`);
      set.status = 401;
      return { error: 'Unauthorized: Invalid or missing access token' };
    }
    return; // pass through
  })

  // ── WebSocket: real-time metrics channel + client tracking ──────────────────
  .ws('/ws', {
    query: t.Object({ token: t.Optional(t.String()) }),

    open(ws) {
      // Validate token on WS handshake — reject immediately if invalid
      const token = ws.data.query.token;
      if (token !== ACCESS_TOKEN) {
        ws.close(1008, 'Unauthorized');
        return;
      }

      // Bun exposes remoteAddress on the raw socket
      const rawIp = (ws as any).remoteAddress ?? '127.0.0.1';
      const cleanIp = rawIp === '::1' || rawIp === '::ffff:127.0.0.1' ? '127.0.0.1' : rawIp;

      wsClients.set(ws.id, { ip: cleanIp, ws });
      console.log(`[WS] Client connected: ${cleanIp} (id=${ws.id}). Total: ${wsClients.size}`);

      // Immediately push current state so UI doesn't wait 1.5s
      broadcastMetrics();
    },

    close(ws) {
      const client = wsClients.get(ws.id);
      wsClients.delete(ws.id);
      console.log(`[WS] Client disconnected: ${client?.ip ?? 'unknown'} (id=${ws.id}). Total: ${wsClients.size}`);
      // Push updated IP list to remaining clients
      broadcastMetrics();
    },

    // Accept ping messages from client to keep connection alive
    message(ws, message) {
      if (message === 'ping') ws.send('pong');
    },
  })

  // ── GET /api/ai/models ──────────────────────────────────────────────────────
  .get('/api/ai/models', async () => {
    const OLLAMA_TAGS_URL = 'http://127.0.0.1:11434/api/tags';
    try {
      const response = await fetch(OLLAMA_TAGS_URL);
      if (!response.ok) throw new Error('Ollama tags unavailable');

      const data = await response.json() as { models?: Array<{ name: string }> };
      const models = data.models?.map(m => m.name) ?? [];
      return { models: models.length > 0 ? models : ['qwen2.5:3b'] };
    } catch {
      console.warn('[AI] Ollama unreachable — returning fallback model list.');
      return { models: ['qwen2.5:3b', 'llama3:latest', 'phi3:latest'] };
    }
  })

  // ── POST /api/ai/generate — SSE streaming to frontend ──────────────────────
  .post('/api/ai/generate', async function* ({ body }) {
    const { prompt, model } = body as { prompt: string; model?: string };
    const MODEL = model || 'qwen2.5:3b';
    const OLLAMA_URL = 'http://127.0.0.1:11434/api/chat';

    console.log(`[AI] Inference: model="${MODEL}" prompt="${prompt.slice(0, 60)}${prompt.length > 60 ? '...' : ''}"`);

    try {
      const response = await fetch(OLLAMA_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: MODEL,
          messages: [{ role: 'user', content: prompt }],
          stream: true,
          options: {
            temperature: 0.7,
            num_ctx: 4096,
            num_predict: 512,
            top_p: 0.9,
            repeat_penalty: 1.1,
          },
        }),
      });

      if (!response.ok) throw new Error(`Ollama HTTP ${response.status}`);
      if (!response.body) throw new Error('No response body from Ollama');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;
          try {
            const chunk = JSON.parse(trimmed);
            if (chunk.message?.content) {
              yield `data: ${JSON.stringify({ token: chunk.message.content })}\n\n`;
            }
          } catch { /* partial line — skip */ }
        }
      }

      // Flush remaining buffer
      if (buffer.trim()) {
        try {
          const chunk = JSON.parse(buffer.trim());
          if (chunk.message?.content) {
            yield `data: ${JSON.stringify({ token: chunk.message.content })}\n\n`;
          }
        } catch { /* ignore */ }
      }
    } catch (error) {
      const msg = `[Error: Cannot reach Ollama. Run: ollama run ${MODEL}]`;
      console.error('[AI] Inference failure:', error);
      yield `data: ${JSON.stringify({ token: msg })}\n\n`;
    }

    yield 'data: [DONE]\n\n';
    console.log('[AI] Stream completed.');
  }, {
    body: t.Object({
      prompt: t.String({ minLength: 1 }),
      model: t.Optional(t.String()),
    }),
  })

  .listen({ port: PORT, hostname: HOST });

console.log(`Gateway running at http://${HOST}:${PORT}`);
console.log(`WebSocket endpoint: ws://${HOST}:${PORT}/ws?token=<token>`);
console.log(`Swagger docs: http://${HOST}:${PORT}/docs`);
