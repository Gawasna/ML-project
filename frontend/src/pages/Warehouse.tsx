import { useState } from 'react';
import Sidebar from '../components/Sidebar';
import CanvasHeader from '../components/CanvasHeader';
import TabSelector from '../components/TabSelector';
import CanvasTools from '../components/CanvasTools';
import ChatInput from '../components/ChatInput';
import RunAction from '../components/RunAction';
import LiveTab from '../components/LiveTab';
import ChatTab from '../components/ChatTab';

export default function Warehouse() {
  const [activeTab, setActiveTab] = useState<'live' | 'chat'>('live');
  const [activeTool, setActiveTool] = useState<'select' | 'add' | 'link' | 'delete' | 'zoom'>('select');
  const [chatVal, setChatVal] = useState('');

  return (
    <div className="flex bg-slate-50 min-h-screen font-sans w-full p-4 gap-4 box-border items-start text-left">
      {/* Sidebar Component - Sticky on left */}
      <div className="sticky top-4 shrink-0 h-[calc(100vh-32px)]">
        <Sidebar />
      </div>

      {/* Main plain workspace containing components sequentially - Left-aligned and scroll-free */}
      <main className="flex-1 bg-white border border-slate-200 rounded-2xl p-8 flex flex-col gap-10 shadow-3xs text-left items-start w-full">
        <div className="text-left w-full">
          <h1 className="text-xl font-bold text-slate-900 tracking-tight text-left">Component Warehouse</h1>
          <p className="text-xs text-slate-500 font-medium mt-1 text-left">
            Trang trống chứa toàn bộ các components đã được chuyển đổi từ bản thiết kế Pencil v0.1 (Light Theme).
          </p>
        </div>

        <hr className="border-slate-100 w-full" />

        {/* 1. Tab Selector */}
        <div className="flex flex-col gap-3 w-full text-left items-start">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider text-left">Tab Selector</h3>
          <div className="p-4 bg-slate-50 border border-slate-150 rounded-xl flex justify-start items-center w-full">
            <TabSelector activeTab={activeTab} onChange={setActiveTab} />
          </div>
        </div>

        {/* 2. Run Action Button */}
        <div className="flex flex-col gap-3 w-full text-left items-start">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider text-left">Run Action FAB</h3>
          <div className="p-4 bg-slate-50 border border-slate-150 rounded-xl flex justify-start items-center w-full">
            <RunAction onRun={() => alert('Run pipeline command executed.')} />
          </div>
        </div>

        {/* 3. Chat Input Bar */}
        <div className="flex flex-col gap-3 w-full text-left items-start">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider text-left">Chat Input Action</h3>
          <div className="p-4 bg-slate-50 border border-slate-150 rounded-xl flex justify-start items-center w-full">
            <ChatInput 
              value={chatVal} 
              onChange={setChatVal} 
              onSubmit={(e) => { e.preventDefault(); alert(`Sending: ${chatVal}`); setChatVal(''); }} 
            />
          </div>
        </div>

        {/* 4. Canvas Tools */}
        <div className="flex flex-col gap-3 w-full text-left items-start">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider text-left">Canvas Tools</h3>
          <div className="p-4 bg-slate-50 border border-slate-150 rounded-xl flex justify-start items-center w-full">
            <CanvasTools activeTool={activeTool} onChange={setActiveTool} />
          </div>
        </div>

        {/* 5. Canvas Header */}
        <div className="flex flex-col gap-3 w-full text-left items-start">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider text-left">Canvas Header</h3>
          <div className="p-4 bg-slate-50 border border-slate-150 rounded-xl w-full">
            <CanvasHeader activeTab={activeTab} onTabChange={setActiveTab} />
          </div>
        </div>

        {/* 6. Live Pipeline Canvas Tab */}
        <div className="flex flex-col gap-3 w-full text-left items-start">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider text-left">Live Canvas Tab View</h3>
          <div className="w-full">
            <LiveTab />
          </div>
        </div>

        {/* 7. AI Chat Tab View */}
        <div className="flex flex-col gap-3 w-full text-left items-start">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider text-left">AI Chat Tab View</h3>
          <div className="w-full max-w-3xl">
            <ChatTab hostIp="localhost" />
          </div>
        </div>
      </main>
    </div>
  );
}
