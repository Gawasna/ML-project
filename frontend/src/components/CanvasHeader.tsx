import TabSelector from './TabSelector';
import { Cpu, WrapText } from 'lucide-react';
import { AVAILABLE_WRAPPERS } from '../utils/promptWrapper';

interface CanvasHeaderProps {
  activeTab: 'live' | 'chat';
  onTabChange: (tab: 'live' | 'chat') => void;
  selectedModel?: string;
  setSelectedModel?: (model: string) => void;
  models?: string[];
  activeWrapperId: string | null;
  onWrapperChange: (id: string | null) => void;
}

export default function CanvasHeader({
  activeTab,
  onTabChange,
  selectedModel,
  setSelectedModel,
  models,
  activeWrapperId,
  onWrapperChange,
}: CanvasHeaderProps) {
  return (
    <div className="w-full border-b border-slate-100 flex items-center justify-between px-4 bg-white shrink-0 font-sans py-2 gap-3 flex-wrap">
      <div className="flex items-center gap-2 flex-wrap">
        <h2 className="text-base font-bold text-slate-800 tracking-tight mr-1">
          Playground
        </h2>

        {/* Model Selector */}
        {models && models.length > 0 && selectedModel && setSelectedModel && (
          <div className="bg-[#f8fafc] border border-slate-200 rounded-lg px-2.5 py-1.5 flex items-center gap-1.5 shadow-2xs select-none">
            <Cpu size={12} className="text-indigo-600 shrink-0" />
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="bg-transparent border-none text-[11px] font-extrabold text-slate-700 outline-none cursor-pointer pr-1 leading-none h-4"
            >
              {models.map((model) => (
                <option key={model} value={model} className="font-sans font-semibold text-slate-700 text-xs">
                  {model}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Prompt Wrapper Chips */}
        <div className="flex items-center gap-1.5">
          <WrapText size={11} className="text-slate-400 shrink-0" />
          {AVAILABLE_WRAPPERS.map(wrapper => {
            const active = activeWrapperId === wrapper.id;
            return (
              <button
                key={wrapper.id}
                type="button"
                title={wrapper.description}
                onClick={() => onWrapperChange(active ? null : wrapper.id)}
                className={`px-2 py-0.5 rounded-md text-[10px] font-bold border transition-all duration-100 cursor-pointer select-none ${
                  active
                    ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm shadow-indigo-200'
                    : 'bg-[#f8fafc] text-slate-500 border-slate-200 hover:border-indigo-300 hover:text-indigo-600'
                }`}
              >
                {wrapper.label}
              </button>
            );
          })}
        </div>
      </div>

      <TabSelector activeTab={activeTab} onChange={onTabChange} />
    </div>
  );
}
