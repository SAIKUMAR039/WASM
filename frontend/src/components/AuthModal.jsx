import React, { useState } from 'react';
import { api } from '../services/api';

export default function AuthModal({ isOpen, onClose, onAuthSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Developer');
  const [orgName, setOrgName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (isLogin) {
        const res = await api.login({ username, password });
        api.setToken(res.access_token);
        api.setTenant(res.user.tenant_id);
        onAuthSuccess(res.user);
        onClose();
      } else {
        const res = await api.register({
          username,
          email,
          password,
          organization_name: orgName || undefined,
          role,
        });
        api.setToken(res.access_token);
        api.setTenant(res.user.tenant_id);
        onAuthSuccess(res.user);
        onClose();
      }
    } catch (err) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const setDemoUser = (demoRole) => {
    setIsLogin(false);
    const demoId = Math.floor(100 + Math.random() * 900);
    setUsername(`${demoRole.toLowerCase()}_${demoId}`);
    setEmail(`${demoRole.toLowerCase()}_${demoId}@wasmbox.dev`);
    setPassword('DemoPass123!');
    setRole(demoRole);
    setOrgName(`${demoRole} Workspace`);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-md w-full p-6 shadow-2xl relative text-white">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white text-xl"
        >
          &times;
        </button>

        <h2 className="text-xl font-bold mb-2">
          {isLogin ? 'Sign In to WasmBox' : 'Create WasmBox Account'}
        </h2>
        <p className="text-sm text-slate-400 mb-4">
          Enterprise Multi-Tenancy & Role-Based Access Control
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-900/40 border border-red-500/50 rounded text-red-200 text-xs">
            {error}
          </div>
        )}

        {/* Quick Demo Role Fill */}
        <div className="mb-4 bg-slate-800/60 p-2.5 rounded-lg border border-slate-700">
          <div className="text-xs font-semibold text-slate-400 mb-1.5">⚡ Quick Switch Demo Role:</div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setDemoUser('Admin')}
              className="flex-1 text-xs py-1 px-2 rounded bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 hover:bg-indigo-600/50 transition"
            >
              👑 Admin
            </button>
            <button
              type="button"
              onClick={() => setDemoUser('Developer')}
              className="flex-1 text-xs py-1 px-2 rounded bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 hover:bg-emerald-600/50 transition"
            >
              ⚡ Dev
            </button>
            <button
              type="button"
              onClick={() => setDemoUser('Viewer')}
              className="flex-1 text-xs py-1 px-2 rounded bg-amber-600/30 text-amber-300 border border-amber-500/40 hover:bg-amber-600/50 transition"
            >
              👁️ Viewer
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Username {isLogin && 'or Email'}
            </label>
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
              placeholder="e.g. alice"
            />
          </div>

          {!isLogin && (
            <>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Email</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                  placeholder="alice@wasmbox.dev"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Organization / Tenant</label>
                <input
                  type="text"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                  placeholder="Acme Corp"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Assigned Role</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="Admin">Admin (Full Control)</option>
                  <option value="Developer">Developer (Manage Plugins & Execute)</option>
                  <option value="Viewer">Viewer (Read-Only Access)</option>
                </select>
              </div>
            </>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-4 bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2 rounded-lg transition disabled:opacity-50 text-sm"
          >
            {loading ? 'Processing...' : isLogin ? 'Sign In' : 'Create Account'}
          </button>
        </form>

        <div className="mt-4 text-center text-xs text-slate-400">
          {isLogin ? "Don't have an account?" : 'Already have an account?'}{' '}
          <button
            type="button"
            onClick={() => {
              setIsLogin(!isLogin);
              setError('');
            }}
            className="text-indigo-400 hover:underline font-medium ml-1"
          >
            {isLogin ? 'Register now' : 'Sign In'}
          </button>
        </div>
      </div>
    </div>
  );
}
