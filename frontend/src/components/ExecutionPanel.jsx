import React, { useState } from 'react';
import { Play, Terminal, CheckCircle2, AlertTriangle, Clock, ShieldX, Loader2 } from 'lucide-react';

export default function ExecutionPanel({ onExecute, isRunning, executionResult, inputData, setInputData }) {
  const [activeTab, setActiveTab] = useState('output'); // 'output' | 'stdout' | 'stderr'

  const getStatusBadge = (status) => {
    switch (status) {
      case 'SUCCESS':
        return (
          <span className="flex items-center gap-1 text-emerald-400 bg-emerald-950/60 border border-emerald-500/30 px-2.5 py-1 rounded-full text-xs font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5" /> Success
          </span>
        );
      case 'ERROR':
        return (
          <span className="flex items-center gap-1 text-rose-400 bg-rose-950/60 border border-rose-500/30 px-2.5 py-1 rounded-full text-xs font-semibold">
            <AlertTriangle className="w-3.5 h-3.5" /> Execution Error
          </span>
        );
      case 'TIMEOUT':
        return (
          <span className="flex items-center gap-1 text-amber-400 bg-amber-950/60 border border-amber-500/30 px-2.5 py-1 rounded-full text-xs font-semibold">
            <Clock className="w-3.5 h-3.5" /> Timeout Exceeded
          </span>
        );
      case 'SECURITY_VIOLATION':
        return (
          <span className="flex items-center gap-1 text-red-400 bg-red-950/60 border border-red-500/30 px-2.5 py-1 rounded-full text-xs font-semibold">
            <ShieldX className="w-3.5 h-3.5" /> Security Violation
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col h-full space-y-4">
      {/* Top Bar with Run Controls */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-purple-400" />
          <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">Execution Console</h2>
        </div>

        <button
          onClick={onExecute}
          disabled={isRunning}
          className={`flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-bold text-white transition-all shadow-lg ${
            isRunning
              ? 'bg-purple-900/50 cursor-not-allowed opacity-75'
              : 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-600/20 active:scale-95'
          }`}
        >
          {isRunning ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin text-white" />
              <span>Running WASM Sandbox...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              <span>Run Code (Wasmtime)</span>
            </>
          )}
        </button>
      </div>

      {/* Input JSON Data Editor */}
      <div>
        <label className="block text-xs font-medium text-slate-400 mb-1">
          Input Payload (JSON / Plain Text)
        </label>
        <textarea
          rows={3}
          value={inputData}
          onChange={(e) => setInputData(e.target.value)}
          placeholder='{"text": "sample input"}'
          className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 font-mono text-xs text-purple-300 focus:outline-none focus:border-purple-500/50"
        />
      </div>

      {/* Output Console Section */}
      <div className="flex-1 flex flex-col bg-slate-950 border border-slate-800 rounded-xl overflow-hidden min-h-[220px]">
        {/* Output Header Tabs & Status Badge */}
        <div className="bg-slate-900/70 px-3 py-2 border-b border-slate-800 flex items-center justify-between">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('output')}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'output' ? 'bg-slate-800 text-slate-100 font-semibold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Output Result
            </button>
            <button
              onClick={() => setActiveTab('stdout')}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'stdout' ? 'bg-slate-800 text-slate-100 font-semibold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Stdout
            </button>
            <button
              onClick={() => setActiveTab('stderr')}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'stderr' ? 'bg-slate-800 text-slate-100 font-semibold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Stderr
            </button>
          </div>

          {executionResult && getStatusBadge(executionResult.status)}
        </div>

        {/* Content Box */}
        <div className="flex-1 p-4 font-mono text-xs overflow-auto">
          {!executionResult ? (
            <div className="h-full flex items-center justify-center text-slate-600 font-mono text-xs">
              Click 'Run Code' to execute plugin inside Wasmtime sandbox.
            </div>
          ) : activeTab === 'output' ? (
            <pre className="text-emerald-400 whitespace-pre-wrap">
              {typeof executionResult.output_result === 'object'
                ? JSON.stringify(executionResult.output_result, null, 2)
                : executionResult.output_result || 'No output produced.'}
            </pre>
          ) : activeTab === 'stdout' ? (
            <pre className="text-slate-300 whitespace-pre-wrap">
              {executionResult.stdout || '(Empty stdout)'}
            </pre>
          ) : (
            <pre className="text-rose-400 whitespace-pre-wrap">
              {executionResult.stderr || '(No error logs)'}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
