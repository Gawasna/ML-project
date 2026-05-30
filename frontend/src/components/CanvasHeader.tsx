import TabSelector from './TabSelector';

interface CanvasHeaderProps {
  activeTab: 'live' | 'chat';
  onTabChange: (tab: 'live' | 'chat') => void;
}

export default function CanvasHeader({ activeTab, onTabChange }: CanvasHeaderProps) {
  return (
    <div className="w-full h-12 border-b border-slate-100 flex items-center justify-between px-6 bg-white shrink-0 font-sans">
      <h2 className="text-base font-bold text-slate-850 tracking-tight">
        Playground
      </h2>
      <TabSelector activeTab={activeTab} onChange={onTabChange} />
    </div>
  );
}
