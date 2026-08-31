import React, { useRef, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { Code, RotateCcw, Save, AlertTriangle, CheckCircle2 } from 'lucide-react';

const DEFAULT_PYTHON_SNIPPET = `def process(data):
    """
    WasmBox Plugin Entrypoint: process(data)
    Receives input data, returns processed result.
    """
    text = str(data.get("text", data) if isinstance(data, dict) else data)
    
    return {
        "status": "success",
        "result": text.upper(),
        "length": len(text)
    }
`;

export default function MonacoEditor({ code, setCode, onSaveCode, errorDetails, selectedPlugin }) {
  const editorRef = useRef(null);
  const monacoRef = useRef(null);

  // Handle Monaco Editor Mounting
  const handleEditorDidMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;

    // Register WasmBox Python Completion Item Provider
    if (!window._wasmboxPythonCompletionsRegistered) {
      monaco.languages.registerCompletionItemProvider('python', {
        provideCompletionItems: (model, position) => {
          const word = model.getWordUntilPosition(position);
          const range = {
            startLineNumber: position.lineNumber,
            endLineNumber: position.lineNumber,
            startColumn: word.startColumn,
            endColumn: word.endColumn,
          };

          const suggestions = [
            {
              label: 'process',
              kind: monaco.languages.CompletionItemKind.Function,
              documentation: 'WasmBox Plugin Entrypoint: process(data)\nReceives execution input and returns processed dictionary.',
              insertText: 'def process(data):\n    """WasmBox Plugin Entrypoint"""\n    return {\n        "status": "success",\n        "result": data\n    }',
              range,
            },
            {
              label: 'wasm_get_input',
              kind: monaco.languages.CompletionItemKind.Function,
              documentation: 'Retrieve raw input data passed to WasmBox sandbox.',
              insertText: 'wasm_get_input()',
              range,
            },
            {
              label: 'wasm_emit_output',
              kind: monaco.languages.CompletionItemKind.Function,
              documentation: 'Emit structured result dictionary from WASM sandbox.',
              insertText: 'wasm_emit_output({"status": "success", "result": ${1:value}})',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              range,
            },
            {
              label: 'wasm_memory_limit',
              kind: monaco.languages.CompletionItemKind.Variable,
              documentation: 'Query maximum memory allocation configured for this sandbox execution.',
              insertText: 'wasm_memory_limit',
              range,
            },
            // Pre-built Intelligent Snippets
            {
              label: 'snippet_json_transform',
              kind: monaco.languages.CompletionItemKind.Snippet,
              documentation: 'Transform incoming dictionary by uppercasing string keys and values.',
              insertText: [
                'def process(data):',
                '    """Transform and sanitize dictionary payload"""',
                '    if isinstance(data, str):',
                '        import json',
                '        try:',
                '            data = json.loads(data)',
                '        except Exception:',
                '            data = {"raw": data}',
                '    ',
                '    result = {str(k).lower(): str(v).strip() for k, v in data.items()} if isinstance(data, dict) else data',
                '    return {',
                '        "status": "success",',
                '        "transformed": result',
                '    }'
              ].join('\n'),
              range,
            },
            {
              label: 'snippet_regex_extractor',
              kind: monaco.languages.CompletionItemKind.Snippet,
              documentation: 'Extract email addresses or matching patterns from input text.',
              insertText: [
                'import re',
                '',
                'def process(data):',
                '    text = str(data.get("text", data) if isinstance(data, dict) else data)',
                '    tokens = re.findall(r\'[\\w\\.-]+@[\\w\\.-]+\\.\\w+\', text)',
                '    return {',
                '        "status": "success",',
                '        "matches": tokens,',
                '        "count": len(tokens)',
                '    }'
              ].join('\n'),
              range,
            },
            {
              label: 'snippet_numeric_stats',
              kind: monaco.languages.CompletionItemKind.Snippet,
              documentation: 'Calculate sum, mean, min, max on a list of numbers.',
              insertText: [
                'def process(data):',
                '    nums = data if isinstance(data, list) else data.get("numbers", [])',
                '    nums = [float(x) for x in nums if isinstance(x, (int, float))]',
                '    if not nums:',
                '        return {"status": "empty", "count": 0}',
                '    return {',
                '        "status": "success",',
                '        "count": len(nums),',
                '        "sum": sum(nums),',
                '        "min": min(nums),',
                '        "max": max(nums),',
                '        "avg": round(sum(nums) / len(nums), 4)',
                '    }'
              ].join('\n'),
              range,
            },
            // Standard Library Completions
            {
              label: 'json.loads',
              kind: monaco.languages.CompletionItemKind.Method,
              documentation: 'Deserialize string or byte/bytearray to a Python object.',
              insertText: 'json.loads(${1:string_data})',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              range,
            },
            {
              label: 'json.dumps',
              kind: monaco.languages.CompletionItemKind.Method,
              documentation: 'Serialize obj to a JSON formatted str.',
              insertText: 'json.dumps(${1:obj}, indent=2)',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              range,
            },
            {
              label: 'hashlib.sha256',
              kind: monaco.languages.CompletionItemKind.Method,
              documentation: 'Return a sha256 hash object.',
              insertText: 'hashlib.sha256(${1:data}.encode("utf-8")).hexdigest()',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              range,
            },
          ];

          return { suggestions };
        },
      });
      window._wasmboxPythonCompletionsRegistered = true;
    }
  };

  // Update error markers in Monaco editor when errorDetails changes
  useEffect(() => {
    if (!editorRef.current || !monacoRef.current) return;
    const editor = editorRef.current;
    const monaco = monacoRef.current;
    const model = editor.getModel();
    if (!model) return;

    if (errorDetails) {
      let lineNo = 1;
      // Extract line number from traceback e.g. "line 5" or "Line 12"
      const match = errorDetails.match(/line (\d+)/i) || errorDetails.match(/Line (\d+)/i);
      if (match) {
        lineNo = parseInt(match[1], 10);
      }

      monaco.editor.setModelMarkers(model, 'python-error', [
        {
          startLineNumber: lineNo,
          startColumn: 1,
          endLineNumber: lineNo,
          endColumn: 100,
          message: errorDetails,
          severity: monaco.MarkerSeverity.Error,
        },
      ]);
    } else {
      monaco.editor.setModelMarkers(model, 'python-error', []);
    }
  }, [errorDetails, code]);

  const handleReset = () => {
    setCode(DEFAULT_PYTHON_SNIPPET);
  };

  return (
    <div className="flex flex-col h-full bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
      {/* Editor Header */}
      <div className="bg-slate-900/90 px-4 py-2.5 border-b border-slate-800 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Code className="w-4 h-4 text-purple-400" />
          <span className="text-xs font-mono font-semibold text-slate-300">
            {selectedPlugin ? `${selectedPlugin.name}.py` : 'plugin_script.py'}
          </span>
          <span className="text-[10px] bg-purple-950 text-purple-300 border border-purple-800/50 px-2 py-0.5 rounded-full font-mono">
            Python 3.12 (WASM Target)
          </span>
        </div>

        <div className="flex items-center gap-2">
          {onSaveCode && (
            <button
              onClick={onSaveCode}
              className="flex items-center gap-1.5 px-3 py-1 text-xs font-semibold text-white bg-purple-600 hover:bg-purple-500 rounded-lg shadow-sm transition-all active:scale-95"
            >
              <Save className="w-3.5 h-3.5" /> Save Changes
            </button>
          )}
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-slate-400 hover:text-slate-200 bg-slate-800 hover:bg-slate-700/60 rounded-lg transition-all"
          >
            <RotateCcw className="w-3 h-3" /> Reset Template
          </button>
        </div>
      </div>

      {/* Code Error Warning Banner */}
      {errorDetails && (
        <div className="bg-rose-950/80 border-b border-rose-800/60 px-4 py-2 flex items-center justify-between text-xs text-rose-300 font-mono">
          <div className="flex items-center gap-2 truncate">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            <span className="truncate font-semibold">{errorDetails}</span>
          </div>
          <span className="text-[11px] bg-rose-900/60 px-2 py-0.5 rounded text-rose-200 shrink-0 ml-2">
            See Squiggle Error in Code
          </span>
        </div>
      )}

      {/* Monaco Editor Container */}
      <div className="flex-1 min-h-[350px]">
        <Editor
          height="100%"
          defaultLanguage="python"
          theme="vs-dark"
          value={code}
          onChange={(val) => setCode(val || '')}
          onMount={handleEditorDidMount}
          options={{
            fontSize: 13,
            fontFamily: "'JetBrains Mono', monospace",
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 4,
            padding: { top: 12, bottom: 12 },
            lineNumbersMinChars: 3,
            glyphMargin: true,
          }}
        />
      </div>
    </div>
  );
}
