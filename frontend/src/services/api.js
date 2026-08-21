const BASE_URL = 'http://localhost:8000/api';

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const config = {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  };
  try {
    const res = await fetch(url, config);
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP Error ${res.status}`);
    }
    if (res.status === 204) return null;
    return await res.json();
  } catch (err) {
    console.warn(`API call failed for ${endpoint}:`, err.message);
    throw err;
  }
}

export const api = {
  // Plugin Endpoints
  getPlugins: (tenantId = 'tenant_default') => request(`/plugins?tenant_id=${tenantId}`),
  createPlugin: (data) => request('/plugins', { method: 'POST', body: JSON.stringify(data) }),
  updatePlugin: (id, data) => request(`/plugins/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deletePlugin: (id) => request(`/plugins/${id}`, { method: 'DELETE' }),

  // Execution Endpoints
  executeCode: (payload) => request('/execute', { method: 'POST', body: JSON.stringify(payload) }),

  executeStream: (payload, { onChunk, onStatus, onResult, onError } = {}) => {
    return new Promise((resolve, reject) => {
      const isHttps = typeof window !== 'undefined' && window.location.protocol === 'https:';
      const wsProtocol = isHttps ? 'wss:' : 'ws:';
      const host = typeof window !== 'undefined' && window.location.hostname === 'localhost'
        ? 'localhost:8000'
        : (typeof window !== 'undefined' && window.location.host ? window.location.host : 'localhost:8000');
      const wsUrl = `${wsProtocol}//${host}/ws/execute`;

      let socket;
      let isSettled = false;

      try {
        socket = new WebSocket(wsUrl);
      } catch (err) {
        console.warn('WebSocket initialization failed, falling back to HTTP:', err);
        return api.executeCode(payload)
          .then((res) => {
            if (onResult) onResult(res);
            resolve(res);
          })
          .catch((e) => {
            if (onError) onError(e);
            reject(e);
          });
      }

      socket.onopen = () => {
        if (onStatus) onStatus('RUNNING');
        socket.send(JSON.stringify(payload));
      };

      socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'stdout' || msg.type === 'stderr') {
            if (onChunk) onChunk(msg.data, msg.type);
          } else if (msg.type === 'status') {
            if (onStatus) onStatus(msg.status);
          } else if (msg.type === 'result') {
            isSettled = true;
            if (onResult) onResult(msg);
            resolve(msg);
            try { socket.close(); } catch (e) {}
          } else if (msg.type === 'error') {
            isSettled = true;
            const err = new Error(msg.error || 'Execution failed');
            if (onError) onError(err);
            reject(err);
            try { socket.close(); } catch (e) {}
          }
        } catch (e) {
          if (onChunk) onChunk(event.data, 'stdout');
        }
      };

      socket.onerror = (err) => {
        if (!isSettled) {
          console.warn('WebSocket stream error, fallback to REST execute:', err);
          api.executeCode(payload)
            .then((res) => {
              isSettled = true;
              if (onResult) onResult(res);
              resolve(res);
            })
            .catch((e) => {
              isSettled = true;
              if (onError) onError(e);
              reject(e);
            });
        }
      };

      socket.onclose = () => {
        if (!isSettled) {
          if (onStatus) onStatus('DISCONNECTED');
        }
      };
    });
  },

  // Metrics & Logs
  getMetricsSummary: (tenantId = 'tenant_default') => request(`/metrics/summary?tenant_id=${tenantId}`),
  getExecutions: (tenantId = 'tenant_default') => request(`/metrics/executions?tenant_id=${tenantId}`),

  // Security Settings
  getPolicy: (tenantId = 'tenant_default') => request(`/settings?tenant_id=${tenantId}`),
  updatePolicy: (policy) => request('/settings', { method: 'PUT', body: JSON.stringify(policy) }),
};
