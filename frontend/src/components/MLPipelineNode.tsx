import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import { Clock } from 'lucide-react';

export type PipelineNodeStatus = 'idle' | 'running' | 'pending' | 'stop';

export interface MLPipelineNodeData {
  text: string;
  ttsDuration: number; // in milliseconds
  status: PipelineNodeStatus;
  inPipeline: boolean;
  index: number;
}

const MLPipelineNode = ({ data, selected }: { data: MLPipelineNodeData; selected?: boolean }) => {
  // Define styling based on status and pipeline inclusion
  const getStatusStyles = () => {
    if (!data.inPipeline) {
      return {
        bg: 'bg-slate-50/70 border-slate-200 text-slate-400 opacity-60 shadow-none',
        badge: 'bg-slate-200 text-slate-500 border border-slate-300',
        indicator: 'OUT',
        glow: '',
      };
    }

    switch (data.status) {
      case 'running':
        return {
          bg: 'bg-indigo-50/95 border-indigo-400 text-indigo-700 shadow-indigo-100 shadow-lg animate-[pulse_2s_infinite]',
          badge: 'bg-indigo-600 text-white font-bold',
          indicator: 'RUN',
          glow: 'shadow-[0_0_20px_rgba(99,102,241,0.35)]',
        };
      case 'stop':
        return {
          bg: 'bg-rose-50/95 border-rose-350 text-rose-700 shadow-rose-100/50 shadow-md',
          badge: 'bg-rose-600 text-white font-bold',
          indicator: 'STOP',
          glow: 'shadow-[0_0_15px_rgba(239,68,68,0.15)]',
        };
      case 'pending':
        return {
          bg: 'bg-amber-50/90 border-amber-250 text-amber-700 shadow-amber-50/50 shadow-sm',
          badge: 'bg-amber-500 text-white font-bold',
          indicator: 'WAIT',
          glow: '',
        };
      case 'idle':
      default:
        return {
          bg: 'bg-white border-slate-250 text-slate-700 shadow-slate-100 shadow-sm',
          badge: 'bg-slate-500 text-white font-bold',
          indicator: 'IDLE',
          glow: '',
        };
    }
  };

  const statusStyles = getStatusStyles();

  // Helper to format TTS duration to human-readable seconds or milliseconds
  const formatTTS = (ms: number) => {
    if (ms >= 1000) {
      return `${(ms / 1000).toFixed(1)}s`;
    }
    return `${ms}ms`;
  };

  return (
    <div
      className={`flex flex-col items-center gap-2 p-3.5 rounded-2xl border-2 w-[160px] select-none transition-all duration-250 hover:scale-102 bg-white ${
        selected ? 'border-indigo-600 ring-3 ring-indigo-100 scale-102 z-50' : statusStyles.bg
      } ${statusStyles.glow}`}
    >
      {/* Target handle on left */}
      <Handle
        type="target"
        position={Position.Left}
        className={`!w-3 !h-3 !bg-white !border-2 ${
          selected ? '!border-indigo-600' : data.inPipeline ? '!border-indigo-500' : '!border-slate-300'
        } hover:!scale-120 hover:!bg-indigo-500 transition-all duration-150`}
      />

      {/* Top Meta Details (Index & Status Badge) */}
      <div className="flex items-center justify-between w-full text-[9px] font-sans font-semibold">
        {/* Index Badge */}
        {data.inPipeline ? (
          <span className="px-1.5 py-0.5 rounded-md bg-indigo-50 text-indigo-600 border border-indigo-100/60 font-mono">
            Node #{data.index}
          </span>
        ) : (
          <span className="px-1.5 py-0.5 rounded-md bg-slate-100 text-slate-400 border border-slate-200">
            Unlinked
          </span>
        )}

        {/* Status Indicator */}
        <span className={`px-1.5 py-0.5 rounded-md uppercase tracking-wider font-bold text-[8px] ${
          !data.inPipeline ? 'bg-slate-200 text-slate-500' :
          data.status === 'running' ? 'bg-indigo-100 text-indigo-700 animate-pulse' :
          data.status === 'stop' ? 'bg-rose-100 text-rose-700' :
          data.status === 'pending' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-500'
        }`}>
          {statusStyles.indicator}
        </span>
      </div>

      {/* Main Content Area (No Icon - Text takes full width) */}
      <div className="w-full mt-1.5 min-h-[36px] flex items-center">
        <p 
          title={data.text} 
          className="text-[10px] font-bold text-slate-800 line-clamp-2 leading-snug break-words w-full text-left"
        >
          {data.text}
        </p>
      </div>

      {/* Bottom Duration Badge */}
      <div className="flex justify-start w-full mt-1">
        <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-50 text-slate-400 border border-slate-150 text-[9px] font-mono font-medium">
          <Clock size={10} />
          {formatTTS(data.ttsDuration)}
        </span>
      </div>

      {/* Source handle on right */}
      <Handle
        type="source"
        position={Position.Right}
        className={`!w-3 !h-3 !bg-white !border-2 ${
          selected ? '!border-indigo-600' : data.inPipeline ? '!border-indigo-500' : '!border-slate-300'
        } hover:!scale-120 hover:!bg-indigo-500 transition-all duration-150`}
      />
    </div>
  );
};

export default memo(MLPipelineNode);
