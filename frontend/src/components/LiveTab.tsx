import { useState, useCallback, useEffect, useRef } from 'react';
import { 
  ReactFlow, 
  Background, 
  useNodesState, 
  useEdgesState, 
  addEdge, 
  useReactFlow, 
  ReactFlowProvider,
  MarkerType,
  Panel,
  BackgroundVariant,
  reconnectEdge
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Search, Trash2, ChevronDown, ChevronUp, Terminal, X } from 'lucide-react';

import CanvasTools from './CanvasTools';
import type { ToolType } from './CanvasTools';
import RunAction from './RunAction';
import MLPipelineNode from './MLPipelineNode';
import type { PipelineNodeStatus } from './MLPipelineNode';
import { estimateTTSDuration } from '../utils/ttsEstimator';
import { applyWrapper } from '../utils/promptWrapper';

// Inference config passed down from Playground
export interface InferenceConfig {
  apiEndpoint: string;
  accessToken: string;
  selectedModel: string;
  activeWrapperId: string | null;
}

// Console output entry for one pipeline node execution
interface ConsoleEntry {
  nodeId: string;
  nodeIndex: number;
  ttsDurationMs: number;    // estimated TTS duration of this node's text
  prompt: string;           // original node text (pre-wrapper)
  output: string;           // streamed AI response, built up incrementally
  deltaMs: number | null;   // time from prev node stream end → this node's first token (TTFT gap)
  streamDurationMs: number | null; // total time from first token → stream complete
  streaming: boolean;
  error?: string;
}

// Define custom node types for React Flow
const nodeTypes = {
  mlNode: MLPipelineNode,
};

// Initial nodes layout (TTS specific phrases)
const initialNodes = [
  { 
    id: '1', 
    type: 'mlNode',
    position: { x: 80, y: 200 },
    data: { 
      text: 'Welcome to the high-performance AI sandbox demo.', 
      ttsDuration: estimateTTSDuration('Welcome to the high-performance AI sandbox demo.'), 
      status: 'idle' as PipelineNodeStatus, 
      inPipeline: true, 
      index: 0 
    }
  },
  { 
    id: '2', 
    type: 'mlNode',
    position: { x: 290, y: 200 },
    data: { 
      text: 'This system monitors hardware telemetry in real-time.', 
      ttsDuration: estimateTTSDuration('This system monitors hardware telemetry in real-time.'), 
      status: 'idle' as PipelineNodeStatus, 
      inPipeline: true, 
      index: 1 
    }
  },
  { 
    id: '3', 
    type: 'mlNode',
    position: { x: 500, y: 200 },
    data: { 
      text: 'We can stream speech tokens directly from the model.', 
      ttsDuration: estimateTTSDuration('We can stream speech tokens directly from the model.'), 
      status: 'idle' as PipelineNodeStatus, 
      inPipeline: true, 
      index: 2 
    }
  },
  { 
    id: '4', 
    type: 'mlNode',
    position: { x: 710, y: 200 },
    data: { 
      text: 'Pipeline execution is now fully complete and ready.', 
      ttsDuration: estimateTTSDuration('Pipeline execution is now fully complete and ready.'), 
      status: 'stop' as PipelineNodeStatus, 
      inPipeline: true, 
      index: 3 
    }
  }
];

// Initial edges connecting the nodes linearly
const initialEdges = [
  { 
    id: 'e1-2', 
    source: '1', 
    target: '2', 
    style: { stroke: '#cbd5e1', strokeWidth: 1.5 },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#cbd5e1' }
  },
  { 
    id: 'e2-3', 
    source: '2', 
    target: '3',
    style: { stroke: '#cbd5e1', strokeWidth: 1.5 },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#cbd5e1' }
  },
  { 
    id: 'e3-4', 
    source: '3', 
    target: '4',
    style: { stroke: '#cbd5e1', strokeWidth: 1.5 },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#cbd5e1' }
  }
];

// Helper to check for cycles in graph connections
const hasCycle = (sourceId: string, targetId: string, edges: any[]) => {
  let current = targetId;
  const visited = new Set<string>();
  
  while (current) {
    if (current === sourceId) return true;
    if (visited.has(current)) break;
    visited.add(current);
    
    // Find next edge where current is the source
    const nextEdge = edges.find(e => e.source === current);
    current = nextEdge ? nextEdge.target : null;
  }
  return false;
};

// Pure function to recalculate the single linear pipeline and assign indices
const recalculatePipeline = (
  currentNodes: any[], 
  currentEdges: any[], 
  currentRunningId: string | null = null, 
  isPipelineActive: boolean = false
) => {
  const nextMap = new Map<string, string>();
  const prevMap = new Map<string, string>();
  
  currentEdges.forEach(edge => {
    nextMap.set(edge.source, edge.target);
    prevMap.set(edge.target, edge.source);
  });
  
  // Find all starting nodes (in-degree === 0 && out-degree === 1)
  const startNodes = currentNodes.filter(node => !prevMap.has(node.id) && nextMap.has(node.id));
  
  let mainPipelinePath: string[] = [];
  let maxLen = 0;
  
  startNodes.forEach(startNode => {
    const path: string[] = [];
    let curr: string | undefined = startNode.id;
    const visited = new Set<string>();
    
    while (curr && !visited.has(curr)) {
      path.push(curr);
      visited.add(curr);
      curr = nextMap.get(curr);
    }
    
    if (path.length > maxLen) {
      maxLen = path.length;
      mainPipelinePath = path;
    }
  });
  
  // If no clear start node but there are edges, fallback to find any unlinked start
  if (mainPipelinePath.length === 0 && currentEdges.length > 0) {
    const anyStart = currentNodes.find(node => !prevMap.has(node.id) && nextMap.has(node.id));
    if (anyStart) {
      const path: string[] = [];
      let curr: string | undefined = anyStart.id;
      while (curr) {
        path.push(curr);
        curr = nextMap.get(curr);
      }
      mainPipelinePath = path;
    }
  }

  const pipelineSet = new Set(mainPipelinePath);
  
  return currentNodes.map(node => {
    const inPipeline = pipelineSet.has(node.id);
    const index = inPipeline ? mainPipelinePath.indexOf(node.id) : -1;
    const isLast = inPipeline && index === mainPipelinePath.length - 1;
    
    let status: PipelineNodeStatus = 'idle';
    
    if (inPipeline) {
      if (isPipelineActive) {
        if (currentRunningId === node.id) {
          status = 'running';
        } else if (mainPipelinePath.indexOf(node.id) < mainPipelinePath.indexOf(currentRunningId || '')) {
          // Completed nodes return to idle or stop depending on if they are the end node
          status = isLast ? 'stop' : 'idle';
        } else {
          status = 'pending';
        }
      } else {
        // Inactive pipeline: Last node is designated as 'stop', others are 'idle'
        status = isLast ? 'stop' : 'idle';
      }
    } else {
      status = 'idle';
    }
    
    return {
      ...node,
      data: {
        ...node.data,
        inPipeline,
        index,
        status
      }
    };
  });
};

function LiveTabContent({ inferenceConfig }: { inferenceConfig?: InferenceConfig }) {
  const [activeTool, setActiveTool] = useState<ToolType>('select');
  const [isRunning, setIsRunning] = useState(false);
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [runningNodeId, setRunningNodeId] = useState<string | null>(null);
  const [detailNode, setDetailNode] = useState<any | null>(null);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; nodeId: string } | null>(null);

  // Pipeline output console
  const [consoleEntries, setConsoleEntries] = useState<ConsoleEntry[]>([]);
  const [isConsoleOpen, setIsConsoleOpen] = useState(false);
  const consoleEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll console to latest entry
  useEffect(() => {
    if (isConsoleOpen) {
      consoleEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [consoleEntries, isConsoleOpen]);
  
  const { screenToFlowPosition, fitView } = useReactFlow();

  // Helper to recalculate and update both nodes and edges states simultaneously (Single Source of Truth)
  const updatePipelineStates = useCallback((
    currentNodes: any[], 
    currentEdges: any[], 
    activeRunningId: string | null = null, 
    activeIsRunning: boolean = false
  ) => {
    // 1. Recalculate pipeline indices and statuses on nodes
    const nextNodes = recalculatePipeline(currentNodes, currentEdges, activeRunningId, activeIsRunning);
    
    // 2. Find indices for comparison
    const runningNode = activeRunningId ? nextNodes.find(n => n.id === activeRunningId) : null;
    const runningIdx = runningNode?.data?.index !== undefined ? (runningNode.data.index as number) : -1;

    // 3. Recalculate edge visual styles
    const nextEdges = currentEdges.map((edge) => {
      const sourceNode = nextNodes.find((n) => n.id === edge.source);
      const targetNode = nextNodes.find((n) => n.id === edge.target);

      if (!sourceNode || !targetNode) return edge;

      const sourceInPipe = sourceNode.data.inPipeline;
      const targetInPipe = targetNode.data.inPipeline;

      if (sourceInPipe && targetInPipe) {
        const isSourceRunning = sourceNode.data.status === 'running';
        const isTargetRunning = targetNode.data.status === 'running';
        const isTargetPending = targetNode.data.status === 'pending';
        const sourceIdx = sourceNode.data.index;
        const targetIdx = targetNode.data.index;

        const isEdgeFlowing = activeIsRunning && (
          (isSourceRunning && isTargetPending) || 
          (sourceNode.data.status === 'running' && isTargetPending) ||
          (sourceNode.data.status === 'idle' && isTargetRunning && targetIdx === sourceIdx + 1)
        );

        const isEdgeCompleted = sourceNode.data.status === 'idle' && 
          (targetNode.data.status === 'idle' || targetNode.data.status === 'stop') && 
          (!activeIsRunning || (activeRunningId !== null && targetIdx < runningIdx));

        let strokeColor = '#cbd5e1';
        let strokeWidth = 1.5;
        let animated = false;

        if (isEdgeFlowing) {
          strokeColor = '#6366f1'; // Indigo for active dynamic voice data pipeline
          strokeWidth = 2.5;
          animated = true;
        } else if (isEdgeCompleted) {
          strokeColor = '#10b981'; // Emerald for fully processed audio segments
          strokeWidth = 2.0;
          animated = false;
        }

        return {
          ...edge,
          animated,
          style: { stroke: strokeColor, strokeWidth },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: strokeColor,
          },
        };
      }

      return {
        ...edge,
        animated: false,
        style: { stroke: '#cbd5e1', strokeWidth: 1.5 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#cbd5e1',
        },
      };
    });

    setNodes(nextNodes);
    setEdges(nextEdges);
  }, [setNodes, setEdges]);

  // Recalculate pipeline ONLY when structural links or nodes length change.
  // This breaks infinite rendering loops and makes viewport dragging sub-millisecond fast!
  const edgesSignature = edges.map(e => `${e.source}->${e.target}`).join(',');
  const nodesLength = nodes.length;

  useEffect(() => {
    if (!isRunning) {
      updatePipelineStates(nodes, edges, null, false);
    }
  }, [edgesSignature, nodesLength, isRunning]);

  // Fit View automatically on change of tool to zoom
  useEffect(() => {
    if (activeTool === 'zoom') {
      fitView({ duration: 800 });
      setActiveTool('select');
    }
  }, [activeTool, fitView]);

  // Handler for adding a new edge manually (Smart Re-linking UX enabled!)
  const onConnect = useCallback(
    (params: any) => {
      if (params.source === params.target) return;
      
      // CONSTRAINT: Check cycle. Filter edges first to simulate removal of overwritten links.
      const filteredEdges = edges.filter(
        e => e.source !== params.source && e.target !== params.target
      );
      
      if (hasCycle(params.source, params.target, filteredEdges)) {
        alert("Không thể tạo kết nối vòng lặp. Pipeline bắt buộc phải là tuyến tính!");
        return;
      }
      
      // SMART UX: Auto replace existing links to maintain linear pipeline naturally
      const updatedEdges = edges.filter(
        e => e.source !== params.source && e.target !== params.target
      );

      const newEdge = {
        ...params,
        style: { stroke: '#cbd5e1', strokeWidth: 1.5 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#cbd5e1' }
      };

      const finalEdges = addEdge(newEdge, updatedEdges);
      updatePipelineStates(nodes, finalEdges, runningNodeId, isRunning);
    },
    [edges, nodes, runningNodeId, isRunning, updatePipelineStates]
  );

  // Handler for reconnecting / relocating edges smoothly
  const onReconnect = useCallback(
    (oldEdge: any, newConnection: any) => {
      if (newConnection.source === newConnection.target) return;
      
      // Filter out current edge and potential overwritten edges to check for cycle
      const filteredEdges = edges.filter(
        e => e.id !== oldEdge.id && e.source !== newConnection.source && e.target !== newConnection.target
      );
      
      if (hasCycle(newConnection.source, newConnection.target, filteredEdges)) {
        alert("Không thể tạo kết nối vòng lặp. Pipeline bắt buộc phải là tuyến tính!");
        return;
      }

      // Reconnect and overwrite conflict links
      const updatedEdges = edges.filter(
        e => e.id !== oldEdge.id && e.source !== newConnection.source && e.target !== newConnection.target
      );

      const finalEdges = reconnectEdge(oldEdge, newConnection, updatedEdges);
      updatePipelineStates(nodes, finalEdges, runningNodeId, isRunning);
    },
    [edges, nodes, runningNodeId, isRunning, updatePipelineStates]
  );

  // Handler for adding new nodes (Default TTS payload)
  const onPaneClick = useCallback(
    (event: React.MouseEvent) => {
      // Close context menu if click on pane
      setContextMenu(null);
      
      if (activeTool !== 'add') return;

      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      // Selection of text payloads for speech synthesis simulation
      const ttsPayloads = [
        'Generating high fidelity natural audio segments.',
        'Optimizing local GPU memory access kernels.',
        'Analyzing language semantics and phonemes.',
        'System diagnostics complete. Status nominal.'
      ];
      
      const text = ttsPayloads[nodes.length % ttsPayloads.length];
      const newNodeId = (nodes.length + 1).toString();
      
      const newNode = {
        id: newNodeId,
        type: 'mlNode',
        position,
        data: {
          text: text,
          ttsDuration: estimateTTSDuration(text),
          status: 'idle' as PipelineNodeStatus,
          inPipeline: false,
          index: -1
        },
      };

      const updatedNodes = nodes.concat(newNode);
      updatePipelineStates(updatedNodes, edges, runningNodeId, isRunning);
      setActiveTool('select');
    },
    [activeTool, nodes, edges, runningNodeId, isRunning, screenToFlowPosition, updatePipelineStates]
  );

  // Handler for clicking nodes (either delete node)
  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: any) => {
      setContextMenu(null);
      
      if (activeTool === 'delete') {
        const updatedNodes = nodes.filter((n) => n.id !== node.id);
        const updatedEdges = edges.filter((e) => e.source !== node.id && e.target !== node.id);
        updatePipelineStates(updatedNodes, updatedEdges, null, false);
      }
    },
    [activeTool, nodes, edges, updatePipelineStates]
  );

  const onEdgeClick = useCallback(
    (_event: React.MouseEvent, edge: any) => {
      setContextMenu(null);
      
      if (activeTool !== 'delete') return;
      const updatedEdges = edges.filter((e) => e.id !== edge.id);
      updatePipelineStates(nodes, updatedEdges, null, false);
    },
    [activeTool, nodes, edges, updatePipelineStates]
  );

  // Handler for right-clicking nodes to invoke a context menu
  const onNodeContextMenu = useCallback(
    (event: React.MouseEvent, node: any) => {
      event.preventDefault();
      // Open Context Menu at cursor coordinates
      setContextMenu({
        x: event.clientX,
        y: event.clientY,
        nodeId: node.id
      });
    },
    []
  );

  // Pipeline execution: real AI inference per node when configured, else timer simulation
  const handleRun = async () => {
    if (isRunning) return;

    const recalculatedNodes = recalculatePipeline(nodes, edges);
    const pipelineNodes = recalculatedNodes
      .filter(n => n.data.inPipeline)
      .sort((a, b) => a.data.index - b.data.index);

    if (pipelineNodes.length === 0) {
      alert('Hãy tạo kết nối giữa các node trên canvas để xây dựng một pipeline trước khi chạy!');
      return;
    }

    // Clear previous run, open console
    setConsoleEntries([]);
    setIsConsoleOpen(true);
    setIsRunning(true);

    const canUseApi = !!(inferenceConfig?.apiEndpoint && inferenceConfig?.accessToken);

    if (canUseApi && inferenceConfig) {
      // ── REAL INFERENCE MODE ──────────────────────────────────────────────
      let prevNodeEndTime: number | null = null;

      for (let i = 0; i < pipelineNodes.length; i++) {
        const currentNode = pipelineNodes[i];
        setRunningNodeId(currentNode.id);
        updatePipelineStates(nodes, edges, currentNode.id, true);

        const rawPrompt = currentNode.data.text as string;
        const prompt = applyWrapper(rawPrompt, inferenceConfig.activeWrapperId);

        // Seed a new entry for this node (output will be built up incrementally)
        const entryBase: ConsoleEntry = {
          nodeId: currentNode.id,
          nodeIndex: currentNode.data.index as number,
          ttsDurationMs: currentNode.data.ttsDuration as number,
          prompt: rawPrompt,
          output: '',
          deltaMs: null,
          streamDurationMs: null,
          streaming: true,
        };
        setConsoleEntries(prev => [...prev, entryBase]);

        const nodeStartTime = performance.now();
        let firstTokenTime: number | null = null;

        try {
          const response = await fetch(`${inferenceConfig.apiEndpoint}/api/ai/generate`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${inferenceConfig.accessToken}`,
            },
            body: JSON.stringify({ prompt, model: inferenceConfig.selectedModel }),
          });

          if (!response.ok || !response.body) {
            setConsoleEntries(prev => prev.map((e, idx) =>
              idx === prev.length - 1
                ? { ...e, streaming: false, error: `HTTP ${response.status}` }
                : e
            ));
            prevNodeEndTime = performance.now();
            continue;
          }

          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';
          let done = false;

          while (!done) {
            const { value, done: streamDone } = await reader.read();
            if (streamDone) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() ?? '';

            for (const line of lines) {
              if (line.includes('[DONE]')) { done = true; break; }
              if (!line.startsWith('data: ')) continue;

              const dataStr = line.slice(6).trim();
              if (dataStr === '[DONE]') { done = true; break; }

              try {
                const parsed = JSON.parse(dataStr);
                if (parsed.token) {
                  // Calculate delta on first token: time since previous node ended
                  if (firstTokenTime === null) {
                    firstTokenTime = performance.now();
                    const delta = prevNodeEndTime !== null
                      ? Math.round(firstTokenTime - prevNodeEndTime)
                      : Math.round(firstTokenTime - nodeStartTime);

                    setConsoleEntries(prev => prev.map((e, idx) =>
                      idx === prev.length - 1 ? { ...e, deltaMs: delta } : e
                    ));
                  }

                  // Append token to this entry's output
                  setConsoleEntries(prev => prev.map((e, idx) =>
                    idx === prev.length - 1
                      ? { ...e, output: e.output + parsed.token }
                      : e
                  ));
                }
              } catch { /* partial line — skip */ }
            }
          }

          // Mark entry as complete, record stream duration
          const streamEnd = performance.now();
          setConsoleEntries(prev => prev.map((e, idx) =>
            idx === prev.length - 1
              ? {
                  ...e,
                  streaming: false,
                  streamDurationMs: firstTokenTime !== null ? Math.round(streamEnd - firstTokenTime) : null,
                }
              : e
          ));
          prevNodeEndTime = streamEnd;

        } catch (err) {
          console.warn(`[Pipeline] Node ${currentNode.id} fetch error:`, err);
          setConsoleEntries(prev => prev.map((e, idx) =>
            idx === prev.length - 1
              ? { ...e, streaming: false, error: String(err) }
              : e
          ));
          prevNodeEndTime = performance.now();
        }
      }

      setRunningNodeId(null);
      setIsRunning(false);
      updatePipelineStates(nodes, edges, null, false);

    } else {
      // ── SIMULATION MODE (no API config) ─────────────────────────────────
      let stepIndex = 0;

      const executeNextStep = () => {
        if (stepIndex >= pipelineNodes.length) {
          setRunningNodeId(null);
          setIsRunning(false);
          updatePipelineStates(nodes, edges, null, false);
          return;
        }

        const currentNode = pipelineNodes[stepIndex];
        setRunningNodeId(currentNode.id);
        updatePipelineStates(nodes, edges, currentNode.id, true);

        // In sim mode: show node text as output placeholder
        setConsoleEntries(prev => [...prev, {
          nodeId: currentNode.id,
          nodeIndex: currentNode.data.index as number,
          ttsDurationMs: currentNode.data.ttsDuration as number,
          prompt: currentNode.data.text as string,
          output: '[Simulation] ' + (currentNode.data.text as string),
          deltaMs: stepIndex === 0 ? 0 : currentNode.data.ttsDuration as number,
          streamDurationMs: null,
          streaming: false,
        }]);

        setTimeout(() => {
          stepIndex++;
          executeNextStep();
        }, currentNode.data.ttsDuration);
      };

      executeNextStep();
    }
  };

  return (
    <div className="relative w-full h-full bg-transparent border-none rounded-none p-0 overflow-hidden select-none font-sans flex flex-col justify-between flex-1 min-h-0">

      {/* Interactive React Flow Space */}
      <div className="absolute inset-0 z-10 w-full h-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onReconnect={onReconnect}
          onPaneClick={onPaneClick}
          onNodeClick={onNodeClick}
          onEdgeClick={onEdgeClick}
          onNodeContextMenu={onNodeContextMenu}
          nodeTypes={nodeTypes}
          nodesDraggable={activeTool === 'select'}
          nodesConnectable={activeTool === 'select' || activeTool === 'link'}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          minZoom={0.4}
          maxZoom={1.8}
          proOptions={{ hideAttribution: true }}
          className="bg-slate-50/80 rounded-3xl border border-slate-100 shadow-inner"
        >
          <Background color="#94a3b8" gap={24} size={1.5} variant={BackgroundVariant.Dots} />

          {/* Run FAB — bottom center */}
          <Panel position="bottom-center" className="m-6">
            <RunAction onRun={handleRun} running={isRunning} />
          </Panel>
        </ReactFlow>
      </div>

      {/* Toolbar — center-left, outside ReactFlow to avoid panel constraints */}
      <div className="absolute left-3 top-1/2 -translate-y-1/2 z-30 pointer-events-auto">
        <CanvasTools activeTool={activeTool} onChange={setActiveTool} />
      </div>

      {/* ── Pipeline Output Console — top, flush, light theme ─────────── */}
      {/* z-20: above ReactFlow (z-10), below context menu / modals (z-9998+) */}
      <div
        className="absolute top-0 left-0 right-0 z-20"
        style={{ pointerEvents: 'none' }}
      >
        <div
          className="overflow-hidden border-b border-slate-200 shadow-sm"
          style={{ pointerEvents: 'auto' }}
        >
          {/* Console Header — always visible, flush top */}
          <button
            type="button"
            onClick={() => setIsConsoleOpen(v => !v)}
            className="w-full flex items-center justify-between px-4 py-1.5 bg-white/95 backdrop-blur-sm cursor-pointer select-none group border-b border-slate-100"
          >
            <div className="flex items-center gap-2">
              <Terminal size={11} className="text-indigo-500" />
              <span className="text-[10px] font-bold text-slate-600 font-mono tracking-wide">Pipeline Console</span>
              {consoleEntries.length > 0 && (
                <span className="text-[8px] font-bold px-1.5 py-0.5 rounded-full bg-slate-100 text-slate-500 font-mono border border-slate-200">
                  {consoleEntries.length} node{consoleEntries.length !== 1 ? 's' : ''}
                </span>
              )}
              {isRunning && (
                <span className="flex items-center gap-1 text-[8px] font-bold text-emerald-600">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  LIVE
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              {consoleEntries.length > 0 && !isRunning && (
                <span
                  role="button"
                  onClick={(e) => { e.stopPropagation(); setConsoleEntries([]); }}
                  className="text-[8px] text-slate-400 hover:text-rose-500 transition-colors cursor-pointer flex items-center gap-0.5 font-bold"
                >
                  <X size={9} /> Clear
                </span>
              )}
              {isConsoleOpen
                ? <ChevronUp size={12} className="text-slate-400 group-hover:text-slate-600 transition-colors" />
                : <ChevronDown size={12} className="text-slate-400 group-hover:text-slate-600 transition-colors" />
              }
            </div>
          </button>

          {/* Console Body — light theme, collapsible */}
          {isConsoleOpen && (
            <div className="bg-slate-50 max-h-[220px] overflow-y-auto p-3 flex flex-col gap-2">
              {consoleEntries.length === 0 ? (
                <p className="text-[10px] font-mono text-slate-400 italic text-center py-3">
                  No output yet — run the pipeline to see results here.
                </p>
              ) : (
                consoleEntries.map((entry, idx) => (
                  <div key={`${entry.nodeId}-${idx}`} className="flex flex-col gap-0.5">
                    {/* Entry header row */}
                    <div className="flex items-center gap-1.5 flex-wrap">
                      {/* Node badge */}
                      <span className="text-[8px] font-bold font-mono px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-600 border border-indigo-200">
                        Node #{entry.nodeIndex}
                      </span>
                      {/* TTFT / inter-node delta */}
                      {entry.deltaMs !== null && (
                        <span className="text-[8px] font-mono px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">
                          {idx === 0 ? 'TTFT' : 'Δ gap'} {entry.deltaMs}ms
                        </span>
                      )}
                      {/* Stream duration */}
                      {entry.streamDurationMs !== null && (
                        <span className="text-[8px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                          stream {entry.streamDurationMs}ms
                        </span>
                      )}
                      {/* Keep-up indicator: did AI finish before next TTS chunk? */}
                      {entry.streamDurationMs !== null && !entry.streaming && (
                        <span className={`text-[8px] font-bold font-mono px-1.5 py-0.5 rounded border ${
                          entry.streamDurationMs < entry.ttsDurationMs
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : 'bg-rose-50 text-rose-600 border-rose-200'
                        }`}>
                          {entry.streamDurationMs < entry.ttsDurationMs ? 'AI kept up' : 'AI lagged'}
                        </span>
                      )}
                      {/* Status */}
                      {entry.streaming
                        ? <span className="text-[8px] font-mono text-indigo-500 animate-pulse ml-auto">streaming...</span>
                        : entry.error
                        ? <span className="text-[8px] font-mono text-rose-500 ml-auto">{entry.error}</span>
                        : <span className="text-[8px] font-mono text-slate-400 ml-auto">done</span>
                      }
                    </div>
                    {/* Prompt preview */}
                    <p className="text-[8px] font-mono text-slate-400 truncate pl-1">
                      &gt; {entry.prompt}
                    </p>
                    {/* Output text */}
                    <div className="text-[11px] font-mono text-slate-700 leading-relaxed pl-1 whitespace-pre-wrap break-words">
                      {entry.output || (
                        entry.streaming
                          ? <span className="inline-block w-1 h-3 bg-indigo-400 animate-pulse rounded-sm" />
                          : <span className="text-slate-400 italic">no output</span>
                      )}
                    </div>
                    {idx < consoleEntries.length - 1 && (
                      <div className="border-t border-slate-200 mt-1" />
                    )}
                  </div>
                ))
              )}
              <div ref={consoleEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Invisible Overlay to close Context Menu on clicking outside */}
      {contextMenu && (
        <div 
          className="fixed inset-0 z-[9998] bg-transparent"
          onClick={() => setContextMenu(null)}
          onContextMenu={(e) => {
            e.preventDefault();
            setContextMenu(null);
          }}
        />
      )}

      {/* Right Click Custom Context Menu */}
      {contextMenu && (
        <div 
          className="fixed z-[9999] bg-white/95 backdrop-blur-md border border-slate-200 rounded-xl shadow-xl p-1.5 w-[160px] font-sans text-left animate-[scaleUp_0.1s_ease-out]"
          style={{ left: contextMenu.x, top: contextMenu.y }}
          onClick={() => setContextMenu(null)}
        >
          <button
            onClick={() => {
              const node = nodes.find(n => n.id === contextMenu.nodeId);
              if (node) setDetailNode(node);
              setContextMenu(null);
            }}
            className="w-full text-left px-2.5 py-1.5 text-[11px] font-bold text-slate-700 hover:bg-indigo-50 hover:text-indigo-650 rounded-lg flex items-center gap-2 cursor-pointer transition-colors duration-100"
          >
            <Search size={12} className="text-slate-500" />
            Inspect Details
          </button>
          <button
            onClick={() => {
              const updatedNodes = nodes.filter((n) => n.id !== contextMenu.nodeId);
              const updatedEdges = edges.filter((e) => e.source !== contextMenu.nodeId && e.target !== contextMenu.nodeId);
              updatePipelineStates(updatedNodes, updatedEdges, null, false);
              setContextMenu(null);
            }}
            className="w-full text-left px-2.5 py-1.5 text-[11px] font-bold text-rose-600 hover:bg-rose-50 rounded-lg flex items-center gap-2 cursor-pointer transition-colors duration-100 mt-0.5 border-t border-slate-100 pt-1.5"
          >
            <Trash2 size={12} className="text-rose-500" />
            Delete Node
          </button>
        </div>
      )}

      {/* Popup Glassmorphic Detail Modal */}
      {detailNode && (
        <div 
          className="absolute inset-0 bg-slate-900/35 backdrop-blur-xs flex items-center justify-center z-[9999] animate-[fadeIn_0.15s_ease-out] p-4"
          onClick={() => setDetailNode(null)}
        >
          <div 
            className="bg-white/95 backdrop-blur-md border border-slate-200/80 rounded-2xl w-[390px] max-w-full shadow-2xl p-5 select-none animate-[scaleUp_0.15s_ease-out] flex flex-col gap-4 font-sans text-left"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-600 font-mono text-xs font-bold border border-indigo-100/60">
                  {detailNode.data.inPipeline ? `Node #${detailNode.data.index}` : 'Draft Node'}
                </span>
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Details</h4>
              </div>
              
              {/* Status Badge */}
              <span className={`px-2 py-0.5 rounded-md uppercase tracking-wider font-extrabold text-[9px] border ${
                !detailNode.data.inPipeline ? 'bg-slate-100 text-slate-500 border-slate-200' :
                detailNode.data.status === 'running' ? 'bg-indigo-100 text-indigo-700 border-indigo-200 animate-pulse' :
                detailNode.data.status === 'stop' ? 'bg-rose-100 text-rose-700 border-rose-200' :
                detailNode.data.status === 'pending' ? 'bg-amber-100 text-amber-700 border-amber-200' : 'bg-slate-150 text-slate-650 border-slate-200'
              }`}>
                {!detailNode.data.inPipeline ? 'OUT' : detailNode.data.status}
              </span>
            </div>

            {/* Modal Body */}
            <div className="flex flex-col gap-3">
              {/* TTS Text Content Scroll Area */}
              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">TTS Text Payload</label>
                <div className="max-h-[150px] overflow-y-auto pr-1.5 text-xs font-bold text-slate-800 leading-relaxed bg-slate-50 border border-slate-150 p-3 rounded-xl select-text scrollbar-thin scrollbar-thumb-slate-200">
                  {detailNode.data.text}
                </div>
              </div>

              {/* TTS Metadata Grid */}
              <div className="grid grid-cols-2 gap-2 mt-1">
                <div className="bg-slate-50/60 border border-slate-150/70 p-2.5 rounded-xl flex flex-col gap-1">
                  <span className="text-[8px] font-bold text-slate-455 uppercase tracking-wider">TTS Duration</span>
                  <span className="text-xs font-mono font-extrabold text-slate-700">
                    {detailNode.data.ttsDuration >= 1000 ? `${(detailNode.data.ttsDuration / 1000).toFixed(2)}s` : `${detailNode.data.ttsDuration}ms`}
                  </span>
                </div>
                <div className="bg-slate-50/60 border border-slate-150/70 p-2.5 rounded-xl flex flex-col gap-1">
                  <span className="text-[8px] font-bold text-slate-455 uppercase tracking-wider">Canvas ID</span>
                  <span className="text-xs font-mono font-extrabold text-slate-700">#{detailNode.id}</span>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex justify-end pt-2 border-t border-slate-100 mt-1">
              <button
                onClick={() => setDetailNode(null)}
                className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-sm shadow-indigo-100 active:scale-98 transition-all duration-150 cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function LiveTab({ inferenceConfig }: { inferenceConfig?: InferenceConfig }) {
  return (
    <ReactFlowProvider>
      <LiveTabContent inferenceConfig={inferenceConfig} />
    </ReactFlowProvider>
  );
}
