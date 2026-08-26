import React from 'react';
import { LayoutDashboard, Code2, PlaySquare, ScrollText, ShieldAlert, Cpu } from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'plugins', label: 'Plugin Editor', icon: Code2 },
    { id: 'executions', label: 'Executions', icon: PlaySquare },
    { id: 'logs', label: 'Audit Logs', icon: ScrollText },
    { id: 'settings', label: 'Security & Limits', icon: ShieldAlert },
  ];

  return (
    <aside className="w-64 bg-slate-900/50 border-r border-slate-800 flex flex-col justify-between p-4 min-h-[calc(100vh-4rem)]">
      <div className="space-y-1">
        <div className="px-3 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
          Platform Menu
        </div>
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium text-sm transition-all ${
                isActive
                  ? 'bg-purple-600/10 text-purple-400 border border-purple-500/20 font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-purple-400' : 'text-slate-400'}`} />
              {item.label}
            </button>
          );
        })}
      </div>

      <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
        <div className="flex items-center gap-2 text-xs text-slate-300 font-semibold">
          <Cpu className="w-4 h-4 text-purple-400" /> Wasmtime WASI
        </div>
        <p className="text-[11px] text-slate-400 leading-tight">
          WebAssembly bytecode runtime with memory boundary isolation.
        </p>
      </div>
    </aside>
  );
}
