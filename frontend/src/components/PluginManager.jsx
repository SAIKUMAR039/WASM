import React, { useState } from 'react';
import { Plus, Save, Trash2, FileCode, Check, AlertCircle } from 'lucide-react';

export default function PluginManager({ plugins, selectedPlugin, onSelectPlugin, onSavePlugin, onCreatePlugin, onDeletePlugin }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('general');
  const [tagInput, setTagInput] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreating, setIsCreating] = useState(false);

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
        <button
          onClick={() => setIsCreating(!isCreating)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-purple-600 hover:bg-purple-500 rounded-xl transition-all shadow-md shadow-purple-600/20"
        >
          <Plus className="w-4 h-4" /> New Plugin
        </button>
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
    </div>
  );
}
