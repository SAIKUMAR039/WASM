import React from 'react';
import Editor from '@monaco-editor/react';
import { Code, RotateCcw, Sparkles } from 'lucide-react';

const DEFAULT_PYTHON_SNIPPET = `def process(data):
    """
    WasmBox Plugin Entrypoint: process(data)
    Receives JSON-serializable input data, returns processed result.
    """
    text = str(data.get("text", data) if isinstance(data, dict) else data)
    
    return {
        "status": "success",
        "result": text.upper(),
        "length": len(text)
    }
`;

export default function MonacoEditor({ code, setCode }) {
  const handleReset = () => {
    setCode(DEFAULT_PYTHON_SNIPPET);
  };

  return (
    <div className="flex flex-col h-full bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
      {/* Editor Header */}
      <div className="bg-slate-900/90 px-4 py-2.5 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Code className="w-4 h-4 text-purple-400" />
          <span className="text-xs font-mono font-semibold text-slate-300">plugin_script.py</span>
          <span className="text-[10px] bg-purple-950 text-purple-300 border border-purple-800/50 px-2 py-0.5 rounded-full font-mono">
            Python 3.12 (WASM Target)
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-slate-400 hover:text-slate-200 bg-slate-800 hover:bg-slate-700/60 rounded-lg transition-all"
          >
            <RotateCcw className="w-3 h-3" /> Reset Template
          </button>
        </div>
      </div>

      {/* Monaco Editor Container */}
      <div className="flex-1 min-h-[350px]">
        <Editor
          height="100%"
          defaultLanguage="python"
          theme="vs-dark"
          value={code}
          onChange={(val) => setCode(val || '')}
          options={{
            fontSize: 13,
            fontFamily: "'JetBrains Mono', monospace",
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 4,
            padding: { top: 12, bottom: 12 },
            lineNumbersMinChars: 3,
          }}
        />
      </div>
    </div>
  );
}
