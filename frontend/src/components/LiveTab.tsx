import { useState } from 'react';
import { Database, Cpu, Settings, Activity, CheckCircle } from 'lucide-react';
import CanvasTools from './CanvasTools';
import type { ToolType } from './CanvasTools';
import RunAction from './RunAction';

interface PipelineNode {
  id: string;
  name: string;
  type: 'dataset' | 'preprocess' | 'train' | 'eval';
  status: 'completed' | 'running' | 'idle' | 'pending';
  x: number;
  y: number;
  icon: any;
  metric?: string;
}

export default function LiveTab() {
  const [activeTool, setActiveTool] = useState<ToolType>('select');
  const [isRunning, setIsRunning] = useState(false);
  const [nodes, setNodes] = useState<PipelineNode[]>([
    { id: '1', name: 'Load Dataset', type: 'dataset', status: 'completed', x: 80, y: 150, icon: Database, metric: '12.4k rows' },
    { id: '2', name: 'Preprocessing', type: 'preprocess', status: 'completed', x: 260, y: 150, icon: Settings, metric: 'Standardized' },
    { id: '3', name: 'Model Training', type: 'train', status: 'idle', x: 440, y: 150, icon: Cpu, metric: 'Epoch 0/10' },
    { id: '4', name: 'Evaluation', type: 'eval', status: 'pending', x: 620, y: 150, icon: Activity, metric: 'ROC-AUC' }
  ]);

  const handleRun = () => {
    setIsRunning(true);
    // Simulate pipeline running execution
    let currentIdx = 2; // Start from Training node
    
    const interval = setInterval(() => {
      setNodes(prev => prev.map((node, idx) => {
        if (idx === currentIdx) {
          return { 
            ...node, 
            status: 'running', 
            metric: idx === 2 ? 'Training (Epoch 5/10)...' : 'Evaluating...' 
          };
        }
        if (idx < currentIdx) {
          return { 
            ...node, 
            status: 'completed', 
            metric: idx === 2 ? 'Val-Loss: 0.24' : node.metric 
          };
        }
        return node;
      }));

      currentIdx++;
      if (currentIdx > 3) {
        clearInterval(interval);
        setTimeout(() => {
          setNodes(prev => prev.map((node, idx) => {
            if (idx === 2) return { ...node, status: 'completed', metric: 'Accuracy: 94.2%' };
            if (idx === 3) return { ...node, status: 'completed', metric: 'AUC: 0.96' };
            return node;
          }));
          setIsRunning(false);
        }, 1500);
      }
    }, 2000);
  };

  return (
    <div className="relative w-full h-full bg-transparent border-none rounded-none p-0 overflow-hidden select-none font-sans flex flex-col justify-between flex-1 min-h-0">

      {/* Main Interactive Canvas Area */}
      <div className="absolute inset-0 flex items-center justify-center p-6">
        {/* SVG connection lines between nodes */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 2 L 8 5 L 0 8 z" fill="#cbd5e1" />
            </marker>
            <marker id="arrow-active" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 2 L 8 5 L 0 8 z" fill="#6366f1" />
            </marker>
          </defs>
          
          {nodes.map((node, idx) => {
            if (idx === nodes.length - 1) return null;
            const nextNode = nodes[idx + 1];
            const isConnectionActive = node.status === 'completed' && nextNode.status === 'running';
            const isCompleted = node.status === 'completed' && nextNode.status === 'completed';
            
            return (
              <line
                key={`line-${node.id}`}
                x1={node.x + 60}
                y1={node.y + 40}
                x2={nextNode.x - 20}
                y2={nextNode.y + 40}
                stroke={isConnectionActive || isCompleted ? '#6366f1' : '#e2e8f0'}
                strokeWidth={isConnectionActive || isCompleted ? 2.5 : 1.5}
                strokeDasharray={isConnectionActive ? '5,5' : '0'}
                className={isConnectionActive ? 'animate-[dash_1s_linear_infinite]' : ''}
                markerEnd={isConnectionActive || isCompleted ? 'url(#arrow-active)' : 'url(#arrow)'}
              />
            );
          })}
        </svg>

        {/* Pipeline Nodes List */}
        <div className="relative w-full h-full z-10 flex items-center justify-between px-12">
          {nodes.map((node) => {
            const Icon = node.icon;
            
            // Define styling based on status
            const statusStyles = {
              completed: {
                bg: 'bg-emerald-50 border-emerald-200 text-emerald-700 shadow-emerald-50',
                badge: 'bg-emerald-500 text-white',
                indicator: '✔'
              },
              running: {
                bg: 'bg-indigo-50 border-indigo-200 text-indigo-700 shadow-indigo-100 animate-pulse',
                badge: 'bg-indigo-500 text-white animate-spin',
                indicator: '⌛'
              },
              idle: {
                bg: 'bg-white border-slate-200 text-slate-700 shadow-slate-100',
                badge: 'bg-slate-400 text-white',
                indicator: '●'
              },
              pending: {
                bg: 'bg-slate-50 border-slate-200/60 text-slate-400 opacity-60 shadow-none',
                badge: 'bg-slate-250 text-white',
                indicator: '○'
              }
            }[node.status];

            return (
              <div
                key={node.id}
                className={`flex flex-col items-center gap-3 p-4 rounded-2xl border-2 w-[130px] shadow-sm select-none transition-all duration-200 bg-white ${statusStyles.bg}`}
              >
                {/* Node icon with custom background */}
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center relative ${
                  node.status === 'completed' ? 'bg-emerald-100 text-emerald-600' :
                  node.status === 'running' ? 'bg-indigo-100 text-indigo-600' :
                  node.status === 'idle' ? 'bg-slate-100 text-slate-500' : 'bg-slate-50 text-slate-300'
                }`}>
                  <Icon size={22} />
                  
                  {/* Status Indicator Badge */}
                  <span className={`absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shadow-xs ${statusStyles.badge}`}>
                    {statusStyles.indicator === '✔' ? <CheckCircle size={12} fill="currentColor" className="text-emerald-500 bg-white rounded-full" /> : statusStyles.indicator}
                  </span>
                </div>

                <div className="text-center w-full">
                  <h3 className="font-bold text-slate-800 text-xs truncate">{node.name}</h3>
                  <p className="text-[10px] font-mono text-slate-400 font-semibold truncate mt-1">
                    {node.metric || '-'}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Floating Canvas Side Tools */}
      <div className="absolute left-6 top-1/2 -translate-y-1/2 z-20">
        <CanvasTools activeTool={activeTool} onChange={setActiveTool} />
      </div>

      {/* Center Bottom Floating Run Action FAB - Absolute positioning at bottom */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-20">
        <RunAction onRun={handleRun} running={isRunning} />
      </div>
    </div>
  );
}
