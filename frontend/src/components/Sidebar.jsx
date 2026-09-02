import React from 'react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'plugins', label: 'Plugin Manager', icon: '🧩' },
    { id: 'execute', label: 'Execution Panel', icon: '⚡' },
    { id: 'metrics', label: 'Metrics Dashboard', icon: '📊' },
    { id: 'history', label: 'Execution History', icon: '📜' },
    { id: 'tenants', label: 'Tenants & API Keys', icon: '🏢' },
    { id: 'settings', label: 'Security Settings', icon: '🛡️' },
  ];

  return (
    <aside className="w-56 border-r border-slate-800 bg-slate-900/40 flex flex-col p-4 shrink-0">
      <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-3 px-2">
        Platform Menu
      </div>
      <nav className="space-y-1">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition ${
              activeTab === item.id
                ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
    </aside>
  );
}
