import { Play } from 'lucide-react';

interface RunActionProps {
  onRun: () => void;
  disabled?: boolean;
  running?: boolean;
}

export default function RunAction({ onRun, disabled = false, running = false }: RunActionProps) {
  return (
    <div className="flex items-center justify-center p-1.5 bg-white border border-slate-200 rounded-full w-40 h-14 shadow-sm font-sans shrink-0">
      <button
        onClick={onRun}
        disabled={disabled || running}
        className="w-full h-10 flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-200 text-white disabled:text-slate-400 rounded-full text-xs font-bold transition-all duration-150 shadow-sm shadow-emerald-100 disabled:shadow-none cursor-pointer"
      >
        <span>{running ? 'Running...' : 'Run'}</span>
        <Play size={12} fill="currentColor" />
      </button>
    </div>
  );
}
