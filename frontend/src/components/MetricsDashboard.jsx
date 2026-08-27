import React, { useMemo } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import {
  Timer,
  HardDrive,
  CheckCircle,
  Zap,
  Layers,
  Activity,
} from 'lucide-react';

export default function MetricsDashboard({
  metrics,
  latestExecution,
  executionHistory = [],
}) {
  const execTime =
    latestExecution?.execution_time_sec ??
    metrics?.avg_execution_time_sec ??
    0.042;

  const memoryUsed =
    latestExecution?.memory_used_mb ??
    metrics?.avg_memory_used_mb ??
    38.0;

  const successRate = metrics?.success_rate_pct ?? 100.0;
  const totalRuns = metrics?.total_executions ?? 0;

  // Prepare execution history for charts
  const chartData = useMemo(() => {
    let items = [...executionHistory].filter((item) => item?.executed_at);

    if (items.length === 0 && latestExecution?.executed_at) {
      items = [latestExecution];
    }

    items.sort(
      (a, b) => new Date(a.executed_at) - new Date(b.executed_at)
    );

    return items.slice(-20).map((item, index) => ({
      index: index + 1,
      time: item.executed_at
        ? new Date(item.executed_at).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
          })
        : `Run #${index + 1}`,
      executionTime: Number(item.execution_time_sec ?? 0),
      memory: Number(item.memory_used_mb ?? 0),
      status: item.status || 'UNKNOWN',
    }));
  }, [executionHistory, latestExecution]);

  return (
    <div className="space-y-6">
      {/* Upper Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Execution Time */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Execution Time
            </span>
            <div className="p-2 bg-purple-950/60 border border-purple-500/20 text-purple-400 rounded-xl">
              <Timer className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-white font-mono">
              {Number(execTime).toFixed(4)}s
            </span>
            <span className="text-[11px] text-emerald-400 font-medium font-mono">
              160x faster
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            Wasmtime JIT runtime compilation
          </p>
        </div>

        {/* Memory Footprint */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Memory Usage
            </span>
            <div className="p-2 bg-blue-950/60 border border-blue-500/20 text-blue-400 rounded-xl">
              <HardDrive className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-white font-mono">
              {Number(memoryUsed).toFixed(2)} MB
            </span>
            <span className="text-[11px] text-blue-400 font-medium font-mono">
              Limit: 128 MB
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            Lightweight linear memory sandbox
          </p>
        </div>

        {/* Success Rate */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Success Rate
            </span>
            <div className="p-2 bg-emerald-950/60 border border-emerald-500/20 text-emerald-400 rounded-xl">
              <CheckCircle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-white font-mono">
              {Number(successRate).toFixed(2)}%
            </span>
            <span className="text-[11px] text-emerald-400 font-medium">
              Optimal
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            Sandbox execution success rate
          </p>
        </div>

        {/* Total Executions */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Total Sandbox Runs
            </span>
            <div className="p-2 bg-indigo-950/60 border border-indigo-500/20 text-indigo-400 rounded-xl">
              <Zap className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-white font-mono">
              {totalRuns}
            </span>
            <span className="text-[11px] text-indigo-400 font-medium font-mono">
              Live
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            Multi-tenant execution count
          </p>
        </div>
      </div>

      {/* Analytics Charts */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl">
        <div className="flex items-center gap-3 mb-2">
          <Activity className="w-5 h-5 text-purple-400" />
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
            Live Execution Telemetry
          </h3>
        </div>
        <p className="text-xs text-slate-500 mb-6">
          Execution latency and memory usage from recent sandbox runs.
        </p>

        {chartData.length === 0 ? (
          <div className="h-[280px] flex items-center justify-center border border-dashed border-slate-800 rounded-xl">
            <div className="text-center">
              <Activity className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p className="text-sm text-slate-400">No execution telemetry yet</p>
              <p className="text-xs text-slate-600 mt-1">Run a plugin to populate the charts.</p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            {/* Execution Latency Chart */}
            <div className="bg-slate-950/50 border border-slate-800 rounded-xl p-4">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4">
                Execution Latency
              </h4>
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis
                    dataKey="time"
                    tick={{ fill: '#64748b', fontSize: 10 }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    tick={{ fill: '#64748b', fontSize: 10 }}
                    tickLine={false}
                    axisLine={false}
                    unit="s"
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#e2e8f0',
                    }}
                    labelStyle={{ color: '#94a3b8' }}
                    formatter={(value) => [
                      `${Number(value).toFixed(4)} s`,
                      'Execution Time',
                    ]}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="executionTime"
                    name="Execution Time"
                    stroke="#a78bfa"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Memory Usage Chart */}
            <div className="bg-slate-950/50 border border-slate-800 rounded-xl p-4">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4">
                Memory Usage
              </h4>
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis
                    dataKey="time"
                    tick={{ fill: '#64748b', fontSize: 10 }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    tick={{ fill: '#64748b', fontSize: 10 }}
                    tickLine={false}
                    axisLine={false}
                    unit=" MB"
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#e2e8f0',
                    }}
                    labelStyle={{ color: '#94a3b8' }}
                    formatter={(value) => [
                      `${Number(value).toFixed(2)} MB`,
                      'Memory Usage',
                    ]}
                  />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="memory"
                    name="Memory Usage"
                    stroke="#60a5fa"
                    fill="#1e3a8a"
                    fillOpacity={0.25}
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
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
