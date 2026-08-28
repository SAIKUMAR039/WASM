import React, { useState } from 'react';
import { Plus, Save, Trash2, FileCode, Check, AlertCircle } from 'lucide-react';

export default function PluginManager({ plugins, selectedPlugin, onSelectPlugin, onSavePlugin, onCreatePlugin, onDeletePlugin }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const handleCreateSubmit = (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    onCreatePlugin({ name, description });
    setName('');
    setDescription('');
    setIsCreating(false);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileCode className="w-5 h-5 text-purple-400" />
          <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">Plugin Library</h2>
        </div>
        <button
          onClick={() => setIsCreating(!isCreating)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-purple-600 hover:bg-purple-500 rounded-xl transition-all shadow-md shadow-purple-600/20"
        >
          <Plus className="w-4 h-4" /> New Plugin
        </button>
      </div>

      {/* New Plugin Form */}
      {isCreating && (
        <form onSubmit={handleCreateSubmit} className="bg-slate-950/70 border border-slate-800 p-3 rounded-xl space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Plugin Name</label>
            <input
              type="text"
              placeholder="e.g. Data Anonymizer"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 text-xs rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-purple-500"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Description</label>
            <input
              type="text"
              placeholder="Brief summary of plugin task"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 text-xs rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-purple-500"
            />
          </div>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setIsCreating(false)}
              className="px-3 py-1 text-xs text-slate-400 hover:text-slate-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-3 py-1 text-xs font-semibold text-white bg-purple-600 hover:bg-purple-500 rounded-lg"
            >
              Create
            </button>
          </div>
        </form>
      )}

      {/* Plugin List */}
      <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
        {plugins.length === 0 ? (
          <div className="text-center py-6 text-xs text-slate-500">No plugins created yet.</div>
        ) : (
          plugins.map((plugin) => {
            const isSelected = selectedPlugin?.id === plugin.id;
            return (
              <div
                key={plugin.id}
                onClick={() => onSelectPlugin(plugin)}
                className={`p-3 rounded-xl border cursor-pointer transition-all flex items-center justify-between ${
                  isSelected
                    ? 'bg-purple-950/40 border-purple-500/50 shadow-md shadow-purple-900/10'
                    : 'bg-slate-950/40 border-slate-800/80 hover:border-slate-700'
                }`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-200">{plugin.name}</span>
                    <span className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded font-mono">
                      v{plugin.version || '1.0.0'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 truncate max-w-[200px]">
                    {plugin.description || 'No description provided.'}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeletePlugin(plugin.id);
                    }}
                    className="p-1 text-slate-500 hover:text-red-400 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
