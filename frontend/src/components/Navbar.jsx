import React from 'react';

export default function Navbar({ currentUser, onOpenAuth, onLogout }) {
  const getRoleBadge = (role) => {
    switch (role) {
      case 'Admin':
        return 'bg-purple-900/60 text-purple-300 border-purple-500/50';
      case 'Developer':
        return 'bg-emerald-900/60 text-emerald-300 border-emerald-500/50';
      case 'Viewer':
        return 'bg-amber-900/60 text-amber-300 border-amber-500/50';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  return (
    <header className="h-14 border-b border-slate-800 bg-slate-900/80 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/30">
          W
        </div>
        <div>
          <span className="font-bold text-slate-100 text-lg tracking-tight">Wasm</span>
          <span className="text-indigo-400 font-bold text-lg tracking-tight">Box</span>
          <span className="ml-2 text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-indigo-950 text-indigo-400 border border-indigo-800/60">
            v0.1.0 WASI
          </span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {currentUser ? (
          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-xs font-semibold text-slate-200">{currentUser.username}</div>
              <div className="text-[10px] text-slate-400">{currentUser.tenant_id || 'tenant_default'}</div>
            </div>
            <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${getRoleBadge(currentUser.role)}`}>
              {currentUser.role || 'Admin'}
            </span>
            <button
              onClick={onLogout}
              className="text-xs px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            >
              Sign Out
            </button>
          </div>
        ) : (
          <button
            onClick={onOpenAuth}
            className="text-xs px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium shadow transition flex items-center gap-1.5"
          >
            <span>🔐</span> Sign In / Register
          </button>
        )}

        <div className="flex items-center gap-2 pl-3 border-l border-slate-800">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="text-xs font-medium text-slate-400">Wasmtime Runner Active</span>
        </div>
      </div>
    </header>
  );
}
