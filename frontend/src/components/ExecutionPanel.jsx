import React, { useState, useEffect, useRef } from 'react';
import { Play, Terminal, CheckCircle2, AlertTriangle, Clock, ShieldX, Loader2, Radio } from 'lucide-react';

export default function ExecutionPanel({
  onExecute,
  isRunning,
  executionResult,
  inputData,
  setInputData,
  streamingStdout = '',
  isStreaming = false,
  useStreaming = true,
  setUseStreaming = null,
}) {
  const [activeTab, setActiveTab] = useState('output'); // 'output' | 'stdout' | 'stderr'
  const consoleBottomRef = useRef(null);

  // Automatically switch tab on execution complete or streaming start
  useEffect(() => {
    if (isStreaming) {
      setActiveTab('stdout');
    } else if (executionResult) {
      if (executionResult.status === 'ERROR' || executionResult.status === 'SECURITY_VIOLATION') {
        setActiveTab('stderr');
      } else {
        setActiveTab('output');
      }
    }
  }, [executionResult, isStreaming]);

  // Auto-scroll terminal when streaming stdout updates
  useEffect(() => {
    if (isStreaming && consoleBottomRef.current) {
      consoleBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [streamingStdout, isStreaming]);

  const loadPresetInput = (type) => {
    switch (type) {
      case 'json':
        setInputData('{\n  "text": "hello wasmbox",\n  "count": 42\n}');
        break;
      case 'text':
        setInputData('Hello WasmBox Python Sandbox');
        break;
      case 'numbers':
        setInputData('[10, 20, 30, 40, 50]');
        break;
      case 'clear':
        setInputData('');
        break;
      default:
        break;
    }
  };

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
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-purple-400" />
          <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">Execution Console</h2>
          {isStreaming && (
            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-500/40 text-[10px] text-emerald-400 font-mono font-semibold">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              LIVE WS STREAM
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {setUseStreaming && (
            <button
              onClick={() => setUseStreaming(!useStreaming)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono transition-all border ${
                useStreaming
                  ? 'bg-purple-950/60 border-purple-500/40 text-purple-300'
                  : 'bg-slate-800/60 border-slate-700 text-slate-400 hover:text-slate-200'
              }`}
              title="Toggle WebSocket real-time stdout streaming"
            >
              <Radio className={`w-3.5 h-3.5 ${useStreaming ? 'text-purple-400' : 'text-slate-400'}`} />
              <span>WS Stream</span>
            </button>
          )}

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
                <span>{isStreaming ? 'Streaming Output...' : 'Running WASM Sandbox...'}</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>Run Code (Wasmtime)</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Input Presets & Input Textarea */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <label className="block text-xs font-medium text-slate-400">
            Execution Input (Passed to <code className="text-purple-300">process(data)</code> / <code className="text-purple-300">sys.stdin</code>)
          </label>
          <div className="flex items-center gap-1 text-[11px]">
            <span className="text-slate-500 font-semibold mr-1">Presets:</span>
            <button
              onClick={() => loadPresetInput('json')}
              className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded font-mono"
            >
              JSON
            </button>
            <button
              onClick={() => loadPresetInput('text')}
              className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded font-mono"
            >
              String
            </button>
            <button
              onClick={() => loadPresetInput('numbers')}
              className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded font-mono"
            >
              Array
            </button>
            <button
              onClick={() => loadPresetInput('clear')}
              className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 rounded font-mono"
            >
              Clear
            </button>
          </div>
        </div>

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
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                activeTab === 'stdout' ? 'bg-slate-800 text-slate-100 font-semibold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>Stdout</span>
              {isStreaming && (
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('stderr')}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'stderr'
                  ? 'bg-rose-950/60 text-rose-300 border border-rose-500/30 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Stderr / Traceback
            </button>
          </div>

          {executionResult && getStatusBadge(executionResult.status)}
        </div>

        {/* Content Box */}
        <div className="flex-1 p-4 font-mono text-xs overflow-auto">
          {!executionResult && !isStreaming ? (
            <div className="h-full flex items-center justify-center text-slate-600 font-mono text-xs">
              Click 'Run Code' to execute Python script inside Wasmtime sandbox.
            </div>
          ) : activeTab === 'output' ? (
            <pre className={`whitespace-pre-wrap ${executionResult?.status === 'ERROR' ? 'text-rose-400' : 'text-emerald-400'}`}>
              {typeof executionResult?.output_result === 'object'
                ? JSON.stringify(executionResult.output_result, null, 2)
                : executionResult?.output_result || (isStreaming ? 'Streaming output in progress...' : 'No output produced.')}
            </pre>
          ) : activeTab === 'stdout' ? (
            <div className="text-slate-300 font-mono text-xs whitespace-pre-wrap">
              {streamingStdout || executionResult?.stdout || (isStreaming ? 'Connecting to stdout stream...' : '(Empty stdout)')}
              <div ref={consoleBottomRef} />
            </div>
          ) : (
            <pre className="text-rose-400 whitespace-pre-wrap">
              {executionResult?.stderr || executionResult?.output_result || '(No error logs)'}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
