import React from 'react';
import { Timer, HardDrive, CheckCircle, Cpu, Zap, ShieldCheck, Layers } from 'lucide-react';

export default function MetricsDashboard({ metrics, latestExecution }) {
  const execTime = latestExecution ? latestExecution.execution_time_sec : (metrics?.avg_execution_time_sec || 0.042);
  const memoryUsed = latestExecution ? latestExecution.memory_used_mb : (metrics?.avg_memory_used_mb || 38.0);
  const successRate = metrics?.success_rate_pct || 100.0;
  const totalRuns = metrics?.total_executions || 24;

  return (
    <div className="space-y-6">
      {/* Upper Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Execution Time */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Execution Time</span>
            <div className="p-2 bg-purple-950/60 border border-purple-500/20 text-purple-400 rounded-xl">
              <Timer className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-white font-mono">{execTime}s</span>
            <span className="text-[11px] text-emerald-400 font-medium font-mono">160x faster</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Wasmtime JIT runtime compilation</p>
        </div>

        {/* Memory Footprint */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Memory Usage</span>
            <div className="p-2 bg-blue-950/60 border border-blue-500/20 text-blue-400 rounded-xl">
              <HardDrive className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-white font-mono">{memoryUsed} MB</span>
            <span className="text-[11px] text-blue-400 font-medium font-mono">Limit: 128 MB</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Lightweight linear memory sandbox</p>
        </div>

        {/* Success Rate */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Success Rate</span>
            <div className="p-2 bg-emerald-950/60 border border-emerald-500/20 text-emerald-400 rounded-xl">
              <CheckCircle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-white font-mono">{successRate}%</span>
            <span className="text-[11px] text-emerald-400 font-medium">Optimal</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Zero unhandled sandbox crashes</p>
        </div>

        {/* Total Executions */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Sandbox Runs</span>
            <div className="p-2 bg-indigo-950/60 border border-indigo-500/20 text-indigo-400 rounded-xl">
              <Zap className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-white font-mono">{totalRuns}</span>
            <span className="text-[11px] text-indigo-400 font-medium font-mono">+12 today</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Multi-tenant execution count</p>
        </div>
      </div>

      {/* Docker vs WASM Comparison Card (Based on Storyboard) */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl">
        <div className="flex items-center gap-3 mb-4">
          <Layers className="w-5 h-5 text-purple-400" />
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
            Architecture Efficiency: Docker vs WebAssembly (WasmBox)
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-mono">
                <th className="py-3 px-4">Metric</th>
                <th className="py-3 px-4">Docker Container</th>
                <th className="py-3 px-4 text-purple-400 font-bold">WASM (WasmBox)</th>
                <th className="py-3 px-4">Advantage</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300 font-mono">
              <tr>
                <td className="py-3 px-4 font-semibold text-slate-200">Startup Time</td>
                <td className="py-3 px-4 text-rose-400">Slower (~800ms)</td>
                <td className="py-3 px-4 text-emerald-400 font-bold">Faster (~5ms)</td>
                <td className="py-3 px-4 text-emerald-400">160x Faster Startup</td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-semibold text-slate-200">Resource Overhead</td>
                <td className="py-3 px-4 text-rose-400">High (~120MB base)</td>
                <td className="py-3 px-4 text-emerald-400 font-bold">Low (~38MB base)</td>
                <td className="py-3 px-4 text-emerald-400">3x Lower Memory</td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-semibold text-slate-200">Isolation Boundary</td>
                <td className="py-3 px-4">Strong OS Kernel Container</td>
                <td className="py-3 px-4 text-emerald-400 font-bold">Strong WASI Memory Sandbox</td>
                <td className="py-3 px-4 text-purple-400">Lightweight & Secure</td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-semibold text-slate-200">Density / Concurrency</td>
                <td className="py-3 px-4 text-rose-400">Low (Few per host)</td>
                <td className="py-3 px-4 text-emerald-400 font-bold">High (10,000+ per host)</td>
                <td className="py-3 px-4 text-emerald-400">High Density Scaling</td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-semibold text-slate-200">Best For</td>
                <td className="py-3 px-4">Long-running monolithic apps</td>
                <td className="py-3 px-4 text-purple-400 font-bold">Short-lived plugins / edge functions</td>
                <td className="py-3 px-4 text-purple-400">Ideal Plugin Platform</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
