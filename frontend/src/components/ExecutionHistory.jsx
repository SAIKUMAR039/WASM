import React, { useState } from 'react';
import { ScrollText, CheckCircle2, AlertTriangle, Clock, ShieldX, ChevronRight, ChevronDown } from 'lucide-react';

export default function ExecutionHistory({ executions = [] }) {
  const [expandedId, setExpandedId] = useState(null);

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'SUCCESS':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-950/60 border border-emerald-500/30 text-emerald-400">
            <CheckCircle2 className="w-3 h-3" /> SUCCESS
          </span>
        );
      case 'ERROR':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-950/60 border border-rose-500/30 text-rose-400">
            <AlertTriangle className="w-3 h-3" /> ERROR
          </span>
        );
      case 'TIMEOUT':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-950/60 border border-amber-500/30 text-amber-400">
            <Clock className="w-3 h-3" /> TIMEOUT
          </span>
        );
      case 'SECURITY_VIOLATION':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-red-950/60 border border-red-500/30 text-red-400">
            <ShieldX className="w-3 h-3" /> SECURITY_VIOLATION
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ScrollText className="w-5 h-5 text-purple-400" />
          <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">Execution Audit Logs</h2>
        </div>
        <span className="text-xs font-mono text-slate-400">Showing last {executions.length} runs</span>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-950 text-slate-400 font-mono uppercase">
            <tr className="border-b border-slate-800">
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Execution ID</th>
              <th className="py-3 px-4">Runtime</th>
              <th className="py-3 px-4">Memory</th>
              <th className="py-3 px-4">Timestamp</th>
              <th className="py-3 px-4 text-right">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
            {executions.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-8 text-slate-500">
                  No execution logs available yet.
                </td>
              </tr>
            ) : (
              executions.map((item) => {
                const isExpanded = expandedId === item.id;
                return (
                  <React.Fragment key={item.id}>
                    <tr className="hover:bg-slate-800/40 cursor-pointer" onClick={() => toggleExpand(item.id)}>
                      <td className="py-3 px-4">{getStatusBadge(item.status)}</td>
                      <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">{item.id.slice(0, 8)}...</td>
                      <td className="py-3 px-4 text-purple-300 font-bold">{item.execution_time_sec}s</td>
                      <td className="py-3 px-4 text-blue-300">{item.memory_used_mb} MB</td>
                      <td className="py-3 px-4 text-slate-400">
                        {new Date(item.executed_at).toLocaleTimeString()}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button className="text-slate-400 hover:text-white">
                          {isExpanded ? <ChevronDown className="w-4 h-4 inline" /> : <ChevronRight className="w-4 h-4 inline" />}
                        </button>
                      </td>
                    </tr>

                    {isExpanded && (
                      <tr className="bg-slate-950/80">
                        <td colSpan={6} className="p-4 space-y-2 text-xs">
                          <div>
                            <span className="text-slate-500 font-semibold block mb-1">Output Payload / Result:</span>
                            <pre className="p-3 bg-slate-900 border border-slate-800 rounded-lg text-emerald-400 text-[11px]">
                              {typeof item.output_result === 'object'
                                ? JSON.stringify(item.output_result, null, 2)
                                : item.output_result || '(None)'}
                            </pre>
                          </div>
                          {item.stderr && (
                            <div>
                              <span className="text-rose-400 font-semibold block mb-1">Error Traceback / Security Violation Log:</span>
                              <pre className="p-3 bg-rose-950/40 border border-rose-900/50 rounded-lg text-rose-300 text-[11px]">
                                {item.stderr}
                              </pre>
                            </div>
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
