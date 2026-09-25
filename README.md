# WasmBox — Python WebAssembly Execution Sandbox (v0.2.0)

WasmBox is a lightweight, secure plugin platform that allows users to write or upload Python code, compiles it into WebAssembly-compatible binary artifacts, and executes it inside a restricted **Wasmtime sandbox**. 

The platform isolates plugins from unauthorized host access (server filesystem, network, system commands), enforces strict CPU fuel and linear memory ceilings, and streams real-time stdout/stderr telemetry over WebSockets.

![WasmBox Architecture](https://raw.githubusercontent.com/SAIKUMAR039/WASM/main/docs/architecture.png)

---

## Key Features

- **Python → WASM Compilation Pipeline**: Preprocesses, validates, and packages Python plugins into pre-compiled `.wasm` binaries with embedded bytecode and custom metadata sections.
- **Wasmtime Sandbox Runner**: Enforces strict WASI capabilities, memory limits (128 MB default), execution timeout watchdogs (5s default), and system call restrictions.
- **Dynamic Memory Leak Detection**: Tracks memory allocation deltas, peak memory, and triggers automatic threshold alerts for long-running or leaky plugins.
- **Sandboxed Environment Variables**: Vault allowing tenant configurations and secrets to be injected safely into plugins via `wasmbox_getenv()`.
- **Pre-Built Plugin Template Gallery**: Ready-to-instantiate scaffolds including PII data masking, SHA-256 hashing, CSV parsing, regex entity extraction, and statistical calculation.
- **Live AST Pre-Validation**: Real-time syntax and security linting in Monaco Editor that warns users about forbidden imports before code is executed.
- **Automated Latency & Fuel Benchmarking**: Microsecond benchmark suite reporting p50, p90, p99 latency percentiles, jitter, and fuel quota footprint.
- **WebAssembly Bytecode Inspector**: Inspect binary headers, custom section breakdowns (`wasmbox_metadata`, `wasmbox_bytecode`, `wasmbox_source`, `wasmbox_wheels`), and size distribution.
- **Real-Time WebSockets Streaming (`/ws/execute`)**: Bidirectional stdout/stderr streaming from the sandbox runner to the web terminal.
- **Telemetry & Prometheus Exposition (`/metrics`)**: Standard Prometheus metrics exporter and CSV audit log downloader for enterprise observability.
- **Multi-Tenancy & Tier Quotas**: Sliding-window rate limiting (60 req/min) and tier-based daily execution quotas (Starter, Pro, Enterprise).
- **Offline CLI Tool (`build_plugin.py`)**: Standalone binary builder with LRU cache pruning and dependency wheel bundling.

---

## System Architecture

```
 ┌─────────────────────────────────────────────────────────┐
 │                  React + Monaco Frontend                │
 │  (Dashboard | Plugin Editor | Execution View | Metrics) │
 └────────────────────────────┬────────────────────────────┘
                              │ REST API & WebSockets (/ws/execute)
 ┌────────────────────────────▼────────────────────────────┐
 │                      FastAPI Backend                    │
 │  (Plugin CRUD | Code Validator | Sandbox Manager | API) │
 └────────────────────────────┬────────────────────────────┘
                              │
 ┌────────────────────────────▼────────────────────────────┐
 │                WasmBox Pipeline & Engine                │
 │  1. AST Security Validation & Preprocessing             │
 │  2. Bytecode Harness Compiler & LRU Binary Cache        │
 │  3. Wasmtime Sandbox Runner with WASI Controls          │
 │  4. Memory Leak Watchdog & Fuel Allocation Engine       │
 └────────────────────────────┬────────────────────────────┘
                              │ Enforces
 ┌────────────────────────────▼────────────────────────────┐
 │                   Security Sandboxing                   │
 │   - Linear Memory Ceiling (128 MB default)              │
 │   - Execution Timeout Watchdog (5s default)             │
 │   - CPU Fuel Quota Interceptor                          │
 │   - Isolated Virtual Filesystem / No Host Network       │
 └─────────────────────────────────────────────────────────┘
```

---

## API Reference

### Core Execution Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/execute` | Execute Python plugin inside Wasmtime sandbox and return result & telemetry |
| `WS` | `/ws/execute` | Real-time WebSocket streaming of stdout, stderr, and execution state |
| `POST` | `/api/execute/benchmark` | Run batch execution to compute p50, p90, p99 latency percentiles & fuel stats |
| `POST` | `/api/execute/inspect-bytecode` | Inspect WebAssembly custom sections, headers, and artifact size |

### Plugin Management Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/plugins` | List active plugins for a tenant (supports `category`, `tag`, `search`) |
| `POST` | `/api/plugins` | Create a new plugin document |
| `GET` | `/api/plugins/templates` | Retrieve standard pre-audited plugin templates library |
| `POST` | `/api/plugins/validate` | On-the-fly AST security and syntax validation with line numbers |
| `GET` | `/api/plugins/{id}` | Fetch a specific plugin by ID |
| `PUT` | `/api/plugins/{id}` | Update plugin name, description, code, or tags |
| `DELETE` | `/api/plugins/{id}` | Soft delete a plugin document |

### Telemetry, Metrics & Observability

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/metrics` | Root Prometheus metrics exposition endpoint for scraper discovery |
| `GET` | `/api/metrics/summary` | Aggregate platform statistics (success rate, average latency, memory) |
| `GET` | `/api/metrics/executions` | Fetch recent execution audit records |
| `GET` | `/api/metrics/trends` | Time-series telemetry points for Recharts dashboards |
| `GET` | `/api/metrics/export/csv` | Download execution audit history as CSV spreadsheet |

---

## CLI Usage (`build_plugin.py`)

Compile Python plugins into WebAssembly (`.wasm`) binary artifacts offline:

```bash
# Build a plugin to WebAssembly
python build_plugin.py my_plugin.py -o my_plugin.wasm

# Inspect an existing .wasm artifact
python build_plugin.py --inspect my_plugin.wasm

# Display compiler cache metrics
python build_plugin.py --cache-stats

# Prune cache to maintain maximum disk limit (e.g., 100 MB)
python build_plugin.py --prune 100
```

---

## Getting Started

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

## License
MIT
