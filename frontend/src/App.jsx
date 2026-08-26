import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [tenantId, setTenantId] = useState('tenant_default');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar tenantId={tenantId} setTenantId={setTenantId} />
      <div className="flex flex-1">
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
        <main className="flex-1 p-6">
          <div className="text-xl font-bold text-purple-400">
            WasmBox Platform — Tab: {activeTab}
          </div>
        </main>
      </div>
    </div>
  );
}
