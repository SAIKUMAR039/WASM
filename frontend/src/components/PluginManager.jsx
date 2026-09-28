import React, { useState, useEffect } from 'react';
import { Plus, Save, Trash2, FileCode, Check, AlertCircle, Sparkles, BookOpen, X, Package } from 'lucide-react';
import { api } from '../services/api';

export default function PluginManager({ plugins, selectedPlugin, onSelectPlugin, onSavePlugin, onCreatePlugin, onDeletePlugin }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('general');
  const [tagInput, setTagInput] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [showWheels, setShowWheels] = useState(false);
  const [wheels, setWheels] = useState([]);
  const [depAnalysis, setDepAnalysis] = useState(null);
  const [depLoading, setDepLoading] = useState(false);

  useEffect(() => {
    api.getTemplates()
      .then(res => { if (res) setTemplates(res); })
      .catch(() => {});
  }, []);

  const handleOpenWheels = () => {
    setShowWheels(true);
    api.getAvailableWheels()
      .then(res => { if (res) setWheels(res); })
      .catch(() => {});
    if (selectedPlugin && selectedPlugin.code) {
      setDepLoading(true);
      api.inspectDependencies(selectedPlugin.code)
        .then(res => { setDepAnalysis(res); setDepLoading(false); })
        .catch(() => setDepLoading(false));
    }
  };

  const categories = ['all', 'general', 'data', 'security', 'utility', 'math'];

  const handleCreateSubmit = (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    const tags = tagInput.split(',').map(t => t.trim()).filter(Boolean);
    onCreatePlugin({ name, description, category, tags });
    setName('');
    setDescription('');
    setCategory('general');
    setTagInput('');
    setIsCreating(false);
  };

  const filteredPlugins = plugins.filter(plugin => {
    const matchesCat = selectedCategory === 'all' || plugin.category === selectedCategory;
    const matchesSearch = !searchQuery || 
      plugin.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (plugin.description && plugin.description.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (plugin.tags && plugin.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase())));
    return matchesCat && matchesSearch;
  });

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileCode className="w-5 h-5 text-purple-400" />
          <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">Plugin Library</h2>
          <span className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full font-mono">
            {filteredPlugins.length}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleOpenWheels}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-blue-300 bg-blue-950/60 hover:bg-blue-900/60 border border-blue-500/30 rounded-xl transition-all shadow-sm"
          >
            <Package className="w-3.5 h-3.5 text-blue-400" /> Packages
          </button>
          <button
            onClick={() => setShowTemplates(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-purple-300 bg-purple-950/60 hover:bg-purple-900/60 border border-purple-500/30 rounded-xl transition-all shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5 text-purple-400" /> Templates
          </button>
          <button
            onClick={() => setIsCreating(!isCreating)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-purple-600 hover:bg-purple-500 rounded-xl transition-all shadow-md shadow-purple-600/20"
          >
            <Plus className="w-4 h-4" /> New Plugin
          </button>
        </div>
      </div>

      {/* Category Pills & Search */}
      <div className="space-y-2">
        <div className="flex items-center gap-1 overflow-x-auto pb-1">
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-2.5 py-0.5 text-[11px] font-medium rounded-lg capitalize transition-all shrink-0 ${
                selectedCategory === cat
                  ? 'bg-purple-600/20 text-purple-300 border border-purple-500/40 font-semibold'
                  : 'text-slate-400 hover:text-slate-200 bg-slate-950/60'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
        <input
          type="text"
          placeholder="Filter plugins by name, description, or tag..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full bg-slate-950/80 border border-slate-800 text-xs rounded-xl px-3 py-1.5 text-slate-200 focus:outline-none focus:border-purple-500 font-mono"
        />
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
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 text-xs rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-purple-500 capitalize"
              >
                {categories.filter(c => c !== 'all').map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Tags (comma-separated)</label>
              <input
                type="text"
                placeholder="crypto, hash, utils"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 text-xs rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-purple-500"
              />
            </div>
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
        {filteredPlugins.length === 0 ? (
          <div className="text-center py-6 text-xs text-slate-500">No plugins match your filter.</div>
        ) : (
          filteredPlugins.map((plugin) => {
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
                    {plugin.category && (
                      <span className="text-[9px] bg-purple-950/60 border border-purple-800/40 text-purple-300 px-1.5 py-0.5 rounded uppercase font-semibold">
                        {plugin.category}
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400 truncate max-w-[220px]">
                    {plugin.description || 'No description provided.'}
                  </p>
                  {plugin.tags && plugin.tags.length > 0 && (
                    <div className="flex items-center gap-1 mt-1 flex-wrap">
                      {plugin.tags.map((t) => (
                        <span key={t} className="text-[9px] bg-slate-800/80 text-slate-400 px-1 rounded font-mono">
                          #{t}
                        </span>
                      ))}
                    </div>
                  )}
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

      {/* Template Gallery Modal */}
      {showTemplates && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-purple-400" />
                <h3 className="text-base font-bold text-slate-100">WasmBox Plugin Template Gallery</h3>
              </div>
              <button
                onClick={() => setShowTemplates(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-400">
              Pre-audited, WASM-optimized Python scaffolds for rapid edge execution. Click "Instantiate" to copy into your workspace.
            </p>

            <div className="space-y-3 overflow-y-auto flex-1 pr-1">
              {templates.map(tpl => (
                <div key={tpl.id} className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-200">{tpl.name}</span>
                      <span className="text-[10px] bg-purple-950 border border-purple-800/40 text-purple-300 px-2 py-0.5 rounded font-mono uppercase">
                        {tpl.category}
                      </span>
                    </div>
                    <button
                      onClick={() => {
                        onCreatePlugin({
                          name: tpl.name,
                          description: tpl.description,
                          category: tpl.category,
                          tags: tpl.tags,
                          code: tpl.code
                        });
                        setShowTemplates(false);
                      }}
                      className="px-3 py-1 bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold rounded-lg shadow-sm transition-all"
                    >
                      Instantiate Plugin
                    </button>
                  </div>
                  <p className="text-[11px] text-slate-400">{tpl.description}</p>
                  <pre className="text-[10px] bg-slate-900 border border-slate-800/60 p-2 rounded text-slate-400 font-mono line-clamp-3 overflow-hidden">
                    {tpl.code}
                  </pre>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Packages & Dependency Inspector Modal */}
      {showWheels && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Package className="w-5 h-5 text-blue-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Packages & Dependency Inspector</h3>
              </div>
              <button
                onClick={() => setShowWheels(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-400">
              Audit sandbox pure-Python wheels and import dependencies for safe execution inside the WebAssembly runner.
            </p>

            <div className="space-y-4 overflow-y-auto flex-1 pr-1">
              <div>
                <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Installed Pure-Python Wheels</h4>
                {wheels.length === 0 ? (
                  <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-xl text-xs text-slate-500">
                    No custom wheel packages installed in wheels/ directory. Standard library safe modules are enabled.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {wheels.map((w, idx) => (
                      <div key={idx} className="p-3 bg-slate-950/60 border border-slate-800 rounded-xl space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-blue-300">{w.name}</span>
                          <span className="text-[10px] bg-blue-950 text-blue-400 border border-blue-800/40 px-1.5 py-0.5 rounded font-mono">v{w.version}</span>
                        </div>
                        <p className="text-[10px] text-slate-500 font-mono truncate">{w.filename}</p>
                        <div className="flex items-center gap-1 text-[10px] text-emerald-400">
                          <Check className="w-3 h-3" /> Pure-Python WASM Safe
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {selectedPlugin && (
                <div className="border-t border-slate-800 pt-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                      Dependency Audit: <span className="text-purple-300 normal-case">{selectedPlugin.name}</span>
                    </h4>
                    {depLoading && <span className="text-xs text-purple-400 animate-pulse">Inspecting imports...</span>}
                  </div>

                  {depAnalysis && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <span className={`text-xs px-2.5 py-1 rounded-lg font-semibold flex items-center gap-1.5 ${
                          depAnalysis.is_compatible
                            ? 'bg-emerald-950/70 border border-emerald-700/50 text-emerald-300'
                            : 'bg-rose-950/70 border border-rose-700/50 text-rose-300'
                        }`}>
                          {depAnalysis.is_compatible ? <Check className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
                          {depAnalysis.is_compatible ? 'All Imports Compatible' : 'Incompatible Imports Detected'}
                        </span>
                        <span className="text-xs text-slate-400 font-mono">
                          {depAnalysis.total_imports} total {depAnalysis.total_imports === 1 ? 'import' : 'imports'}
                        </span>
                      </div>

                      <div className="space-y-1.5 max-h-48 overflow-y-auto">
                        {depAnalysis.dependencies.map((dep, idx) => (
                          <div key={idx} className="flex items-center justify-between p-2 bg-slate-950/50 border border-slate-800 rounded-lg text-xs">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-slate-200">{dep.module}</span>
                              <span className="text-[10px] text-slate-500 font-mono">Line {dep.line_number}</span>
                            </div>
                            <span className={`text-[10px] px-2 py-0.5 rounded font-mono ${
                              dep.status === 'stdlib_safe' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/40' :
                              dep.status === 'wheel_available' ? 'bg-blue-950 text-blue-400 border border-blue-800/40' :
                              dep.status === 'blocked' ? 'bg-rose-950 text-rose-400 border border-rose-800/40' :
                              'bg-amber-950 text-amber-400 border border-amber-800/40'
                            }`}>
                              {dep.source}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

