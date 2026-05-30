import { Elysia, t } from 'elysia';
import { cors } from '@elysiajs/cors';
import { swagger } from '@elysiajs/swagger';
import si from 'systeminformation';

const PORT = 3000;
const HOST = '0.0.0.0'; // Accept LAN/WiFi connections

interface HardwareMetrics {
  cpu: { load: number; temp: number };
  memory: { total: number; active: number; percentage: number };
  gpu?: { name: string; memTotal: number; memUsed: number; memFree: number; load: number };
}

const app = new Elysia()
  .use(cors({
    origin: '*',
    methods: ['GET', 'POST', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization']
  }))
  .use(swagger({
    path: '/docs',
    documentation: {
      info: {
        title: 'Bento ML Studio - High Performance API Gateway',
        description: 'BFF Service for local AI execution and real-time hardware telemetry.',
        version: '1.0.0'
      }
    }
  }))

  // Server-Sent Events (SSE) for Real-Time Telemetry
  .get('/api/metrics', async function* () {
    while (true) {
      try {
        const cpuLoad = await si.currentLoad();
        const cpuTemp = await si.cpuTemperature();
        const mem = await si.mem();
        const gpu = await si.graphics();

        const nvidiaGpu = gpu.controllers.find(c => 
          c.vendor.toLowerCase().includes('nvidia') || 
          c.model.toLowerCase().includes('nvidia') || 
          c.model.toLowerCase().includes('rtx') ||
          c.model.toLowerCase().includes('gtx')
        );

        const payload: HardwareMetrics = {
          cpu: {
            load: cpuLoad.currentLoad,
            temp: cpuTemp.main || 0,
          },
          memory: {
            total: mem.total,
            active: mem.active,
            percentage: (mem.active / mem.total) * 100,
          }
        };

        if (nvidiaGpu) {
          payload.gpu = {
            name: nvidiaGpu.model,
            memTotal: nvidiaGpu.vram || 0,
            memUsed: nvidiaGpu.vramUsed || 0,
            memFree: (nvidiaGpu.vram || 0) - (nvidiaGpu.vramUsed || 0),
            load: nvidiaGpu.utilizationGpu || 0,
          };
        }

        yield `data: ${JSON.stringify(payload)}\n\n`;
      } catch (error) {
        console.error('Telemetry acquisition failure:', error);
      }
      
      // Delay for 1.5 seconds between metrics updates
      yield new Promise(resolve => setTimeout(resolve, 1500));
    }
  })

  // Server-Sent Events (SSE) for AI Token-by-Token Generation via local Ollama
  .post('/api/ai/generate', async function* ({ body }) {
    const { prompt } = body as { prompt: string };
    const OLLAMA_URL = 'http://127.0.0.1:11434/api/chat';
    const MODEL_NAME = 'qwen2.5:3b';
    
    console.log(`[AI Server] Prompt received: "${prompt.slice(0, 50)}${prompt.length > 50 ? '...' : ''}"`);

    try {
      const response = await fetch(OLLAMA_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: MODEL_NAME,
          messages: [{ role: 'user', content: prompt }],
          stream: true,
          options: {
            temperature: 0.7,
            num_ctx: 4096,     // Optimized context window size to preserve RAM/VRAM
            num_predict: 512,   // Limit max tokens predicted to speed up inference and save network bandwidth
            top_p: 0.9,
            repeat_penalty: 1.1 // Penalize word repetition for cleaner output
          }
        })
      });

      if (!response.ok) {
        throw new Error(`Ollama responded with status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('No response body returned from Ollama server.');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        // Save the incomplete last line back to buffer for next chunk read
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          try {
            const chunk = JSON.parse(trimmed);
            if (chunk.message?.content) {
              const payload = { token: chunk.message.content };
              yield `data: ${JSON.stringify(payload)}\n\n`;
            }
          } catch (e) {
            // Avoid parsing partial line fragments
          }
        }
      }

      // Parse any left-over data in buffer
      if (buffer.trim()) {
        try {
          const chunk = JSON.parse(buffer.trim());
          if (chunk.message?.content) {
            yield `data: ${JSON.stringify({ token: chunk.message.content })}\n\n`;
          }
        } catch (e) {}
      }

    } catch (error) {
      console.error('Ollama integration failure:', error);
      const errMessage = `[Inference Error: Cannot reach local Ollama on http://localhost:11434. Please verify that Ollama is running and model "${MODEL_NAME}" has been pulled. Try running "ollama run ${MODEL_NAME}" in your command prompt first.]`;
      yield `data: ${JSON.stringify({ token: errMessage })}\n\n`;
    }

    console.log('[AI Server] Stream generation completed.');
    yield 'data: [DONE]\n\n';
  }, {
    body: t.Object({
      prompt: t.String({ minLength: 1 })
    })
  })

  // Export system metrics in standard Prometheus exposition format
  .get('/metrics', async ({ set }) => {
    try {
      const cpu = await si.currentLoad();
      const mem = await si.mem();
      const gpu = await si.graphics();
      const nvidiaGpu = gpu.controllers.find(c => 
        c.vendor.toLowerCase().includes('nvidia') || 
        c.model.toLowerCase().includes('nvidia')
      );

      set.headers['Content-Type'] = 'text/plain; version=0.0.4; charset=utf-8';

      const metrics = [
        `# HELP node_cpu_utilization Hardware CPU Load Percentage`,
        `# TYPE node_cpu_utilization gauge`,
        `node_cpu_utilization ${cpu.currentLoad.toFixed(2)}`,
        
        `# HELP node_memory_bytes_total Total physical memory in bytes`,
        `# TYPE node_memory_bytes_total gauge`,
        `node_memory_bytes_total ${mem.total}`,
        
        `# HELP node_memory_bytes_active Active physical memory in bytes`,
        `# TYPE node_memory_bytes_active gauge`,
        `node_memory_bytes_active ${mem.active}`,
      ];

      if (nvidiaGpu) {
        metrics.push(
          `# HELP node_gpu_utilization Dedicated GPU Load Percentage`,
          `# TYPE node_gpu_utilization gauge`,
          `node_gpu_utilization ${nvidiaGpu.utilizationGpu || 0}`,
          
          `# HELP node_gpu_vram_bytes_total Total dedicated GPU memory in MB`,
          `# TYPE node_gpu_vram_bytes_total gauge`,
          `node_gpu_vram_bytes_total ${nvidiaGpu.vram || 0}`,
          
          `# HELP node_gpu_vram_bytes_used Used dedicated GPU memory in MB`,
          `# TYPE node_gpu_vram_bytes_used gauge`,
          `node_gpu_vram_bytes_used ${nvidiaGpu.vramUsed || 0}`
        );
      }

      return metrics.join('\n') + '\n';
    } catch (error) {
      set.status = 500;
      return 'Error gathering system metrics';
    }
  })

  .listen({
    port: PORT,
    hostname: HOST
  });

console.log(`🚀 Gateway Server running at http://${HOST}:${PORT}`);
console.log(`📖 Swagger API docs at http://${HOST}:${PORT}/docs`);
