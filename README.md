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

## Authentication, Multi-Tenancy & RBAC

WasmBox provides enterprise-grade multi-tenancy and role-based access control:

- **JWT Authentication**:
  - `POST /api/auth/register`: Register user and provision organization tenant.
  - `POST /api/auth/login`: Authenticate with username/email and receive signed JWT.
  - `GET /api/auth/me`: Retrieve current profile, permissions, and tenant details.
- **Tenant & API Key Management**:
  - `POST /api/tenants`: Create a tenant organization.
  - `GET /api/tenants`: List tenant organizations.
  - `POST /api/tenants/{tenant_id}/api-keys`: Generate high-entropy API key with SHA-256 hashed storage.
  - `GET /api/tenants/{tenant_id}/api-keys`: List active API keys.
  - `DELETE /api/tenants/{tenant_id}/api-keys/{key_id}`: Revoke an API key.
- **Role-Based Access Control (RBAC)**:
  - **Admin**: Full control across tenant management, API key generation, sandbox security settings, plugin CRUD, and execution.
  - **Developer**: Manage plugins, execute code in Wasmtime sandbox, and inspect metrics/logs. Forbidden from altering system security settings.
  - **Viewer**: Read-only access to plugins, execution history, and metrics. Forbidden from creating plugins or executing code.
