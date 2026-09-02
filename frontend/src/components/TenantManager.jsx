import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function TenantManager({ currentUser }) {
  const [tenants, setTenants] = useState([]);
  const [apiKeys, setApiKeys] = useState([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyRole, setNewKeyRole] = useState('Developer');
  const [generatedKey, setGeneratedKey] = useState(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');

  const activeTenantId = currentUser?.tenant_id || api.getTenant() || 'tenant_default';

  useEffect(() => {
    loadData();
  }, [activeTenantId]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [tList, kList] = await Promise.all([
        api.getTenants().catch(() => []),
        api.getApiKeys(activeTenantId).catch(() => []),
      ]);
      setTenants(tList);
      setApiKeys(kList);
    } catch (err) {
      console.warn('Failed to load tenants or keys:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateKey = async (e) => {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    try {
      const res = await api.createApiKey(activeTenantId, {
        name: newKeyName,
        role: newKeyRole,
      });
      setGeneratedKey(res.raw_key);
      setNewKeyName('');
      loadData();
    } catch (err) {
      alert(err.message || 'Failed to generate API Key');
    }
  };

  const handleRevokeKey = async (keyId) => {
    if (!confirm('Are you sure you want to revoke this API Key?')) return;
    try {
      await api.deleteApiKey(activeTenantId, keyId);
      loadData();
    } catch (err) {
      alert(err.message || 'Failed to revoke key');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100">Multi-Tenancy & API Keys</h2>
          <p className="text-xs text-slate-400">
            Manage organization tenant isolation, cryptographic API keys, and RBAC permissions.
          </p>
        </div>
      </div>

      {/* Tenant Metadata Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
        <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
          🏢 Active Tenant Organization
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
          <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700/50">
            <span className="text-slate-400 block mb-1">Tenant ID</span>
            <span className="font-mono text-indigo-400 font-semibold">{activeTenantId}</span>
          </div>
          <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700/50">
            <span className="text-slate-400 block mb-1">Organization</span>
            <span className="text-slate-200 font-semibold">{currentUser?.tenant_name || 'Primary Workspace'}</span>
          </div>
          <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700/50">
            <span className="text-slate-400 block mb-1">Current User Role</span>
            <span className="font-semibold text-purple-400">{currentUser?.role || 'Admin'}</span>
          </div>
          <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700/50">
            <span className="text-slate-400 block mb-1">Database Engine</span>
            <span className="text-emerald-400 font-semibold">MongoDB NoSQL</span>
          </div>
        </div>
      </div>

      {/* Generated Key Alert */}
      {generatedKey && (
        <div className="p-4 bg-emerald-950/60 border border-emerald-500/50 rounded-xl text-emerald-200 text-xs">
          <div className="font-bold flex items-center justify-between mb-1">
            <span>🔑 New API Key Created! Copy it now (it will not be shown again):</span>
            <button
              onClick={() => {
                navigator.clipboard.writeText(generatedKey);
                alert('Copied to clipboard!');
              }}
              className="px-2 py-0.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[11px]"
            >
              Copy
            </button>
          </div>
          <div className="font-mono bg-slate-950 p-2 rounded text-emerald-300 break-all select-all">
            {generatedKey}
          </div>
        </div>
      )}

      {/* API Key Generation Form */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
        <h3 className="text-sm font-semibold text-slate-200 mb-3">Generate New API Key</h3>
        <form onSubmit={handleGenerateKey} className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs text-slate-400 mb-1">Key Description / Name</label>
            <input
              type="text"
              required
              placeholder="e.g. GitHub Action Runner"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
            />
          </div>
          <div className="w-36">
            <label className="block text-xs text-slate-400 mb-1">Scoped Role</label>
            <select
              value={newKeyRole}
              onChange={(e) => setNewKeyRole(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="Admin">Admin</option>
              <option value="Developer">Developer</option>
              <option value="Viewer">Viewer</option>
            </select>
          </div>
          <button
            type="submit"
            className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs rounded-lg transition"
          >
            + Generate Key
          </button>
        </form>
      </div>

      {/* Active API Keys Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
        <h3 className="text-sm font-semibold text-slate-200 mb-3">Active API Keys</h3>
        {apiKeys.length === 0 ? (
          <p className="text-xs text-slate-500 py-4 text-center">No active API keys found for this tenant.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400">
                  <th className="pb-2">Name</th>
                  <th className="pb-2">Prefix</th>
                  <th className="pb-2">Role</th>
                  <th className="pb-2">Created</th>
                  <th className="pb-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {apiKeys.map((k) => (
                  <tr key={k.id} className="hover:bg-slate-800/30 transition">
                    <td className="py-2.5 font-medium text-slate-200">{k.name}</td>
                    <td className="py-2.5 font-mono text-slate-400">{k.key_prefix}</td>
                    <td className="py-2.5">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-950 text-indigo-300 border border-indigo-800">
                        {k.role}
                      </span>
                    </td>
                    <td className="py-2.5 text-slate-400">
                      {new Date(k.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-2.5 text-right">
                      <button
                        onClick={() => handleRevokeKey(k.id)}
                        className="text-red-400 hover:text-red-300 text-xs px-2 py-0.5 rounded hover:bg-red-950/40 border border-transparent hover:border-red-800 transition"
                      >
                        Revoke
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
