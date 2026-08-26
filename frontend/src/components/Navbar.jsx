import React from 'react';
import { Box, Cpu, ShieldCheck, Activity } from 'lucide-react';

export default function Navbar({ tenantId, setTenantId }) {
  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-50">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-500 to-blue-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
          <Box className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold bg-gradient-to-r from-white via-slate-200 to-purple-400 bg-clip-text text-transparent">
            WasmBox
          </h1>
          <p className="text-xs text-slate-400 font-mono">Python WebAssembly Sandbox</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Wasmtime Sandbox Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-emerald-400 text-xs font-medium">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Wasmtime Engine Active</span>
        </div>

        {/* Tenant Selector */}
        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-400 font-medium">Tenant:</span>
          <select 
            value={tenantId}
            onChange={(e) => setTenantId(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 focus:ring-2 focus:ring-purple-500 focus:outline-none"
          >
            <option value="tenant_default">Tenant A (Production)</option>
            <option value="tenant_b">Tenant B (Staging)</option>
            <option value="tenant_c">Tenant C (Sandbox)</option>
          </select>
        </div>
      </div>
    </header>
  );
}
