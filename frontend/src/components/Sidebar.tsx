import { Play, Cpu, Database, Settings } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { id: 'playground', label: 'Playground', icon: Play, path: '/' },
    { id: 'warehouse', label: 'Warehouse', icon: Database, path: '/warehouse' },
    { id: 'models', label: 'Models', icon: Cpu, path: '#' },
    { id: 'settings', label: 'Settings', icon: Settings, path: '#' },
  ];

  return (
    <aside className="w-60 h-full bg-white border-r border-slate-200 flex flex-col gap-8 p-6 select-none shrink-0 font-sans">
      {/* Brand Header */}
      <div 
        className="flex items-center gap-3 cursor-pointer" 
        onClick={() => navigate('/')}
      >
        <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center font-extrabold text-white text-lg shadow-sm shadow-indigo-100">
          M
        </div>
        <div>
          <h1 className="font-bold text-slate-900 text-base leading-none">ML Studio</h1>
          <p className="text-[9px] text-slate-400 font-bold uppercase tracking-wider mt-1">Local Sandbox</p>
        </div>
      </div>

      {/* Menu Navigation */}
      <nav className="flex flex-col gap-1.5 w-full">
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => item.path !== '#' && navigate(item.path)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-semibold transition-all duration-150 ${
                isActive
                  ? 'bg-indigo-50 text-indigo-600'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <Icon size={18} className={isActive ? 'text-indigo-600' : 'text-slate-400'} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
