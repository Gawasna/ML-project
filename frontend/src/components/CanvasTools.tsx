import { MousePointer, Plus, Link as LinkIcon, Trash2, Search } from 'lucide-react';

export type ToolType = 'select' | 'add' | 'link' | 'delete' | 'zoom';

interface CanvasToolsProps {
  activeTool: ToolType;
  onChange: (tool: ToolType) => void;
}

export default function CanvasTools({ activeTool, onChange }: CanvasToolsProps) {
  const tools = [
    { id: 'select' as ToolType, icon: MousePointer, tooltip: 'Select Tool' },
    { id: 'add' as ToolType, icon: Plus, tooltip: 'Add Node Tool' },
    { id: 'link' as ToolType, icon: LinkIcon, tooltip: 'Link Tool' },
    { id: 'delete' as ToolType, icon: Trash2, tooltip: 'Delete Tool' },
    { id: 'zoom' as ToolType, icon: Search, tooltip: 'Zoom Tool' },
  ];

  return (
    <div className="flex flex-col gap-2 p-1.5 bg-white border border-slate-200 rounded-2xl w-12 shadow-sm font-sans">
      {tools.map((tool) => {
        const isActive = activeTool === tool.id;
        const Icon = tool.icon;
        return (
          <button
            key={tool.id}
            onClick={() => onChange(tool.id)}
            title={tool.tooltip}
            className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-150 relative group ${
              isActive
                ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-100'
                : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
            }`}
          >
            <Icon size={16} />
            
            {/* Simple CSS Tooltip */}
            <span className="absolute left-14 bg-slate-800 text-white text-[10px] font-bold px-2 py-1 rounded-md opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity duration-150 whitespace-nowrap z-55 shadow-sm">
              {tool.tooltip}
            </span>
          </button>
        );
      })}
    </div>
  );
}
