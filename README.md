# WasmBox — Python WebAssembly Execution Sandbox

WasmBox is a lightweight, secure plugin platform that allows users to upload or write Python code, compiles it into a WebAssembly-compatible format, and executes it inside a restricted **Wasmtime sandbox**. 

The platform isolates plugins from unauthorized host access (server filesystem, network, system commands) and enforces strict CPU and memory resource ceilings.

![WasmBox Architecture](https://raw.githubusercontent.com/SAIKUMAR039/WASM/main/docs/architecture.png)

---

## Key Features

- **Python → WASM Pipeline**: Preprocesses, validates, and packages Python plugins for sandboxed WebAssembly execution.
- **Wasmtime Sandbox**: Enforces strict WASI capabilities, memory limits (128 MB default), execution timeouts (5s default), and system call restrictions.
- **FastAPI Backend**: Provides REST APIs for plugin CRUD operations, code execution, sandbox policy management, and telemetry log retrieval.
- **React + Monaco Developer Portal**: Web-based IDE with live execution controls, performance metrics visualizers, security policy toggles, and audit logs.
- **Multi-Tenancy Support**: Isolates data, plugin state, and execution contexts across tenants.

---

## System Architecture

```
 ┌─────────────────────────────────────────────────────────┐
 │                  React + Monaco Frontend                │
 │  (Dashboard | Plugin Editor | Execution View | Metrics) │
 └────────────────────────────┬────────────────────────────┘
                              │ REST API
 ┌────────────────────────────▼────────────────────────────┐
 │                      FastAPI Backend                    │
 │   (Plugin CRUD | Code Validator | Sandbox Manager)      │
 └────────────────────────────┬────────────────────────────┘
                              │
 ┌────────────────────────────▼────────────────────────────┐
 │                WasmBox Pipeline & Engine                │
 │  1. AST Security Validation & Preprocessing             │
 │  2. Python -> WASM Compilation / Execution Harness      │
 │  3. Wasmtime Sandbox Runner with WASI Controls          │
 └────────────────────────────┬────────────────────────────┘
                              │ Enforces
 ┌────────────────────────────▼────────────────────────────┐
 │                   Security Sandboxing                   │
 │   - Memory Ceiling (128 MB default)                     │
 │   - Execution Timeout (5s default)                      │
 │   - Isolated VFS / Restricted Syscalls                  │
 └─────────────────────────────────────────────────────────┘
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
