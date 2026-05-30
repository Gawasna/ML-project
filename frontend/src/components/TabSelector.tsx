import { Activity, MessageSquare } from 'lucide-react';

interface TabSelectorProps {
  activeTab: 'live' | 'chat';
  onChange: (tab: 'live' | 'chat') => void;
}

export default function TabSelector({ activeTab, onChange }: TabSelectorProps) {
  return (
    <div className="flex items-center gap-1.5 p-1 bg-white border border-slate-200 rounded-full h-11 w-24 justify-center shadow-xs font-sans shrink-0">
      <button
        onClick={() => onChange('live')}
        title="Live Canvas"
        className={`w-9 h-9 rounded-full flex items-center justify-center transition-all duration-150 cursor-pointer shrink-0 ${
          activeTab === 'live'
            ? 'bg-indigo-600 text-white shadow-xs shadow-indigo-100'
            : 'text-slate-650 hover:bg-slate-50'
        }`}
      >
        <Activity size={16} />
      </button>

      <button
        onClick={() => onChange('chat')}
        title="AI Chat"
        className={`w-9 h-9 rounded-full flex items-center justify-center transition-all duration-150 cursor-pointer shrink-0 ${
          activeTab === 'chat'
            ? 'bg-indigo-600 text-white shadow-xs shadow-indigo-100'
            : 'text-slate-650 hover:bg-slate-50'
        }`}
      >
        <MessageSquare size={16} />
      </button>
    </div>
  );
}
