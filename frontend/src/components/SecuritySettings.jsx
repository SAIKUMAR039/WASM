import React, { useState } from 'react';
import { Shield, HardDrive, Timer, Wifi, FolderLock, Check, Save } from 'lucide-react';

export default function SecuritySettings({ policy, onSavePolicy }) {
  const [memoryLimit, setMemoryLimit] = useState(policy?.memory_limit_mb || 128);
  const [timeoutSec, setTimeoutSec] = useState(policy?.timeout_sec || 5.0);
  const [allowNetwork, setAllowNetwork] = useState(policy?.allow_network || false);
  const [allowFilesystem, setAllowFilesystem] = useState(policy?.allow_filesystem || false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSavePolicy({
      memory_limit_mb: Number(memoryLimit),
      timeout_sec: Number(timeoutSec),
      allow_network: allowNetwork,
      allow_filesystem: allowFilesystem,
    });
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl max-w-3xl space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-purple-950/60 border border-purple-500/30 text-purple-400 rounded-xl">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100">Sandbox Security Restrictions</h2>
            <p className="text-xs text-slate-400">Configure Wasmtime WASI capabilities & resource ceilings</p>
          </div>
        </div>

        {savedSuccess && (
          <span className="flex items-center gap-1 text-xs text-emerald-400 bg-emerald-950/60 border border-emerald-500/30 px-3 py-1.5 rounded-xl font-medium animate-pulse">
            <Check className="w-4 h-4" /> Policy Saved
          </span>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Memory Limit Slider */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 text-xs font-semibold text-slate-300">
              <HardDrive className="w-4 h-4 text-purple-400" /> Linear Memory Limit (RAM)
            </label>
            <span className="text-xs font-mono font-bold text-purple-400 bg-purple-950/50 px-2.5 py-1 rounded-lg border border-purple-800/40">
              {memoryLimit} MB
            </span>
          </div>
          <input
            type="range"
            min="32"
            max="512"
            step="16"
            value={memoryLimit}
            onChange={(e) => setMemoryLimit(e.target.value)}
            className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
          />
          <div className="flex justify-between text-[10px] text-slate-500 font-mono">
            <span>32 MB (Strict)</span>
            <span>128 MB (Default)</span>
            <span>512 MB (High)</span>
          </div>
        </div>

        {/* Timeout Slider */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 text-xs font-semibold text-slate-300">
              <Timer className="w-4 h-4 text-purple-400" /> Execution Timeout Watchdog
            </label>
            <span className="text-xs font-mono font-bold text-purple-400 bg-purple-950/50 px-2.5 py-1 rounded-lg border border-purple-800/40">
              {timeoutSec} sec
            </span>
          </div>
          <input
            type="range"
            min="1"
            max="30"
            step="1"
            value={timeoutSec}
            onChange={(e) => setTimeoutSec(e.target.value)}
            className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
          />
          <div className="flex justify-between text-[10px] text-slate-500 font-mono">
            <span>1s (Ultra Short)</span>
            <span>5s (Default)</span>
            <span>30s (Extended)</span>
          </div>
        </div>

        {/* Toggles Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Network Access Switch */}
          <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl flex items-center justify-between">
            <div className="space-y-0.5">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
                <Wifi className="w-4 h-4 text-blue-400" /> Network Access
              </div>
              <p className="text-[11px] text-slate-400">Allow outbound socket connections</p>
            </div>
            <input
              type="checkbox"
              checked={allowNetwork}
              onChange={(e) => setAllowNetwork(e.target.checked)}
              className="w-4 h-4 accent-purple-500 rounded cursor-pointer"
            />
          </div>

          {/* Filesystem Access Switch */}
          <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl flex items-center justify-between">
            <div className="space-y-0.5">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
                <FolderLock className="w-4 h-4 text-amber-400" /> Filesystem Access
              </div>
              <p className="text-[11px] text-slate-400">Grant virtual directory access</p>
            </div>
            <input
              type="checkbox"
              checked={allowFilesystem}
              onChange={(e) => setAllowFilesystem(e.target.checked)}
              className="w-4 h-4 accent-purple-500 rounded cursor-pointer"
            />
          </div>
        </div>

        {/* Restricted AST Modules Info */}
        <div className="p-4 bg-purple-950/20 border border-purple-500/20 rounded-xl space-y-2">
          <h4 className="text-xs font-bold text-purple-300">Enforced Static Security Policies (AST Visitor)</h4>
          <p className="text-[11px] text-purple-200/70">
            Disallowed modules: <code className="font-mono text-purple-300">os, sys, subprocess, ctypes, socket, http, urllib</code><br />
            Disallowed functions: <code className="font-mono text-purple-300">eval(), exec(), open(), __import__()</code>
          </p>
        </div>

        <button
          type="submit"
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-purple-600/20 transition-all"
        >
          <Save className="w-4 h-4" /> Save Security Policies
        </button>
      </form>
    </div>
  );
}
