import uuid
import asyncio
import threading
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from app.database import get_db
from app.schemas import (
    ExecutionRequest,
    ExecutionResponse,
    BenchmarkRequest,
    BenchmarkResponse,
    BytecodeInspectionRequest,
    BytecodeInspectionResponse
)
from app.pipeline.validator import validate_python_code
from app.pipeline.compiler import PythonWasmCompiler
from app.pipeline.cache import parse_wasm_custom_sections
from app.pipeline.compiler_cache import compiler_cache
from app.pipeline.rate_limiter import rate_limiter
from app.sandbox.wasmtime_runner import WasmSandboxRunner

router = APIRouter(prefix="/execute", tags=["Execution"])

_memory_executions = []

@router.post("", response_model=ExecutionResponse)
def execute_code(req: ExecutionRequest, db=Depends(get_db)):
    """
    Executes Python code inside the Wasmtime sandbox and records output/metrics document in MongoDB.
    Enforces sliding window tenant execution rate limits.
    """
    allowed, remaining = rate_limiter.check_rate_limit(req.tenant_id)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for tenant '{req.tenant_id}'. Max 60 executions per minute allowed."
        )

    code_to_run = req.code
    plugin_id = req.plugin_id

    if plugin_id and db is not None:
        plugin = db["plugins"].find_one({"_id": plugin_id, "tenant_id": req.tenant_id})
        if not plugin:
            raise HTTPException(status_code=404, detail="Plugin not found for tenant")
        code_to_run = plugin.get("code")

    if not code_to_run or not code_to_run.strip():
        raise HTTPException(status_code=400, detail="No Python code provided for execution")

    # Fetch policy document
    mem_limit = 128
    timeout_sec = 5.0
    if db is not None:
        policy = db["sandbox_policies"].find_one({"tenant_id": req.tenant_id})
        if policy:
            mem_limit = policy.get("memory_limit_mb", 128)
            timeout_sec = policy.get("timeout_sec", 5.0)

    # 1. AST Security Validation
    is_valid, violations = validate_python_code(code_to_run)
    exec_id = str(uuid.uuid4())
    now = datetime.utcnow()

    if not is_valid:
        exec_doc = {
            "_id": exec_id,
            "id": exec_id,
            "plugin_id": plugin_id,
            "tenant_id": req.tenant_id,
            "status": "SECURITY_VIOLATION",
            "input_data": req.input_data,
            "output_result": {"error": "Security Violation", "details": violations},
            "stdout": "",
            "stderr": "\n".join(violations),
            "execution_time_sec": 0.001,
            "memory_used_mb": 0.0,
            "executed_at": now
        }
        if db is not None:
            db["executions"].insert_one(exec_doc)
        else:
            _memory_executions.append(exec_doc)
            
        return exec_doc

    # 2. Package into WASM Harness
    bundled = compiler_cache.compile(code_to_run, env_vars=req.env_vars)

    # 3. Execute in Wasmtime Sandbox Runner
    runner = WasmSandboxRunner(memory_limit_mb=mem_limit, timeout_sec=timeout_sec)
    res = runner.execute(bundled, req.input_data)

    # 4. Save MongoDB Document
    exec_doc = {
        "_id": exec_id,
        "id": exec_id,
        "plugin_id": plugin_id,
        "tenant_id": req.tenant_id,
        "status": res["status"],
        "input_data": req.input_data,
        "output_result": res["output_result"],
        "stdout": res["stdout"],
        "stderr": res["stderr"],
        "execution_time_sec": res["execution_time_sec"],
        "memory_used_mb": res["memory_used_mb"],
        "peak_memory_mb": res.get("peak_memory_mb", res["memory_used_mb"]),
        "memory_leak_warning": res.get("memory_leak_warning", False),
        "fuel_consumed": res.get("fuel_consumed", 1420),
        "executed_at": now
    }

    if db is not None:
        db["executions"].insert_one(exec_doc)
    else:
        _memory_executions.append(exec_doc)

    return exec_doc


@router.post("/benchmark", response_model=BenchmarkResponse)
def benchmark_plugin(req: BenchmarkRequest, db=Depends(get_db)):
    """
    Executes a plugin repeatedly in the WASM sandbox to measure latency percentiles (p50, p90, p99),
    fuel consumption, memory efficiency, and stability under load.
    """
    code_to_run = req.code
    if req.plugin_id and db is not None:
        plugin = db["plugins"].find_one({"_id": req.plugin_id, "tenant_id": req.tenant_id})
        if not plugin:
            raise HTTPException(status_code=404, detail="Plugin not found for tenant")
        code_to_run = plugin.get("code")

    if not code_to_run or not code_to_run.strip():
        raise HTTPException(status_code=400, detail="No Python code provided for benchmark")

    is_valid, violations = validate_python_code(code_to_run)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Security Violation: {', '.join(violations)}")

    bundled = compiler_cache.compile(code_to_run)
    runner = WasmSandboxRunner()

    latencies_ms = []
    memories_mb = []
    total_fuel = 0
    success_count = 0

    for _ in range(req.iterations):
        res = runner.execute(bundled, req.input_data)
        lat = res.get("execution_time_ms", res["execution_time_sec"] * 1000.0)
        latencies_ms.append(lat)
        memories_mb.append(res["memory_used_mb"])
        total_fuel += res.get("fuel_consumed", 1420)
        if res["status"] == "SUCCESS":
            success_count += 1

    sorted_lats = sorted(latencies_ms)
    n = len(sorted_lats)

    def percentile(p):
        idx = int(round((p / 100.0) * (n - 1)))
        return sorted_lats[idx]

    return {
        "iterations": req.iterations,
        "p50_latency_ms": round(percentile(50), 3),
        "p90_latency_ms": round(percentile(90), 3),
        "p99_latency_ms": round(percentile(99), 3),
        "avg_latency_ms": round(sum(latencies_ms) / n, 3),
        "min_latency_ms": round(sorted_lats[0], 3),
        "max_latency_ms": round(sorted_lats[-1], 3),
        "avg_memory_mb": round(sum(memories_mb) / n, 2),
        "total_fuel_consumed": total_fuel,
        "success_rate_pct": round((success_count / n) * 100.0, 1),
        "raw_latencies_ms": latencies_ms
    }


@router.post("/inspect-bytecode", response_model=BytecodeInspectionResponse)
def inspect_plugin_bytecode(req: BytecodeInspectionRequest):
    """
    Compiles Python plugin code into a WebAssembly binary module and analyzes its
    custom sections, size breakdown, header metadata, and fuel quota footprint.
    """
    if not req.code or not req.code.strip():
        raise HTTPException(status_code=400, detail="No code provided for bytecode inspection")

    artifact = PythonWasmCompiler.compile_plugin(req.code, use_cache=True)
    sections = parse_wasm_custom_sections(artifact.wasm_bytes)

    sec_infos = []
    for name, data in sections.items():
        preview = None
        if name in ("wasmbox_metadata", "wasmbox_wheels"):
            try:
                preview = data.decode("utf-8")
            except Exception:
                preview = f"Binary ({len(data)} bytes)"
        elif name == "wasmbox_source":
            preview = data.decode("utf-8", errors="replace")[:200] + "..."
        else:
            preview = f"Binary bytecode payload ({len(data)} bytes)"

        sec_infos.append({
            "name": name,
            "size_bytes": len(data),
            "preview": preview
        })

    return {
        "cache_key": artifact.cache_key,
        "wasm_size_bytes": len(artifact.wasm_bytes),
        "header_magic": "\\x00asm",
        "header_version": 1,
        "fuel_estimate": max(1420, len(req.code) * 6),
        "sections": sec_infos
    }




async def handle_websocket_execution(websocket: WebSocket, db=None):
    """
    WebSocket handler for real-time stdout/stderr execution streaming.
    Streams execution state and console output chunks in real time.
    """
    await websocket.accept()
    try:
        data = await websocket.receive_json()
    except Exception:
        await websocket.close(code=1003, reason="Invalid JSON payload")
        return

    code_to_run = data.get("code")
    plugin_id = data.get("plugin_id")
    tenant_id = data.get("tenant_id", "tenant_default")
    input_data = data.get("input_data", "HELLO WORLD")

    if plugin_id:
        plugin = None
        if db is not None:
            plugin = db["plugins"].find_one({"_id": plugin_id, "tenant_id": tenant_id})
        if not plugin:
            await websocket.send_json({
                "type": "error",
                "error": "Plugin not found for tenant",
                "status_code": 404,
                "detail": "Plugin not found for tenant"
            })
            await websocket.close(code=1008, reason="Plugin not found for tenant")
            return
        code_to_run = plugin.get("code")

    if not code_to_run or not str(code_to_run).strip():
        await websocket.send_json({
            "type": "error",
            "error": "No Python code provided for execution"
        })
        await websocket.close()
        return

    mem_limit = 128
    timeout_sec = 5.0
    if db is not None:
        policy = db["sandbox_policies"].find_one({"tenant_id": tenant_id})
        if policy:
            mem_limit = policy.get("memory_limit_mb", 128)
            timeout_sec = policy.get("timeout_sec", 5.0)

    # 1. AST Security Validation
    is_valid, violations = validate_python_code(code_to_run)
    exec_id = str(uuid.uuid4())
    now = datetime.utcnow()

    if not is_valid:
        exec_doc = {
            "_id": exec_id,
            "id": exec_id,
            "plugin_id": plugin_id,
            "tenant_id": tenant_id,
            "status": "SECURITY_VIOLATION",
            "input_data": input_data,
            "output_result": {"error": "Security Violation", "details": violations},
            "stdout": "",
            "stderr": "\n".join(violations),
            "execution_time_sec": 0.001,
            "memory_used_mb": 0.0,
            "executed_at": now
        }
        if db is not None:
            db["executions"].insert_one(exec_doc)
        else:
            _memory_executions.append(exec_doc)

        await websocket.send_json({
            "type": "result",
            "status": "SECURITY_VIOLATION",
            "id": exec_id,
            "output_result": exec_doc["output_result"],
            "stdout": "",
            "stderr": exec_doc["stderr"],
            "execution_time_sec": 0.001,
            "memory_used_mb": 0.0,
            "executed_at": now.isoformat()
        })
        return

    # Notify client execution is running
    await websocket.send_json({
        "type": "status",
        "status": "RUNNING",
        "id": exec_id
    })

    # Thread-safe queue to stream stdout/stderr chunks
    stream_queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def stream_callback(stream_type: str, chunk: str):
        loop.call_soon_threadsafe(stream_queue.put_nowait, (stream_type, chunk))

    env_vars = data.get("env_vars")
    bundled = compiler_cache.compile(code_to_run, env_vars=env_vars)
    runner = WasmSandboxRunner(memory_limit_mb=mem_limit, timeout_sec=timeout_sec)

    cancel_event = threading.Event()
    # Run execution in worker thread with cancellation support
    runner_task = asyncio.create_task(
        asyncio.to_thread(runner.execute, bundled, input_data, stream_callback, cancel_event)
    )

    disconnected = False
    while not runner_task.done() or not stream_queue.empty():
        try:
            item = await asyncio.wait_for(stream_queue.get(), timeout=0.04)
            stream_type, chunk = item
            await websocket.send_json({
                "type": stream_type,
                "data": chunk,
                "id": exec_id
            })
            stream_queue.task_done()
        except asyncio.TimeoutError:
            continue
        except WebSocketDisconnect:
            disconnected = True
            break
        except Exception:
            break

    if disconnected:
        cancel_event.set()
        runner_task.cancel()
        exec_doc = {
            "_id": exec_id,
            "id": exec_id,
            "plugin_id": plugin_id,
            "tenant_id": tenant_id,
            "status": "CANCELLED",
            "input_data": input_data,
            "output_result": "Execution cancelled due to client disconnect",
            "stdout": "",
            "stderr": "Client disconnected during execution",
            "execution_time_sec": round((datetime.utcnow() - now).total_seconds(), 4),
            "memory_used_mb": 0.0,
            "executed_at": now
        }
        if db is not None:
            db["executions"].insert_one(exec_doc)
        else:
            _memory_executions.append(exec_doc)
        return

    try:
        res = await runner_task
    except asyncio.CancelledError:
        return

    exec_doc = {
        "_id": exec_id,
        "id": exec_id,
        "plugin_id": plugin_id,
        "tenant_id": tenant_id,
        "status": res["status"],
        "input_data": input_data,
        "output_result": res["output_result"],
        "stdout": res["stdout"],
        "stderr": res["stderr"],
        "execution_time_sec": res["execution_time_sec"],
        "memory_used_mb": res["memory_used_mb"],
        "peak_memory_mb": res.get("peak_memory_mb", res["memory_used_mb"]),
        "memory_leak_warning": res.get("memory_leak_warning", False),
        "fuel_consumed": res.get("fuel_consumed", 1420),
        "executed_at": now
    }

    if db is not None:
        db["executions"].insert_one(exec_doc)
    else:
        _memory_executions.append(exec_doc)

    try:
        await websocket.send_json({
            "type": "result",
            "id": exec_id,
            "status": res["status"],
            "output_result": res["output_result"],
            "stdout": res["stdout"],
            "stderr": res["stderr"],
            "execution_time_sec": res["execution_time_sec"],
            "memory_used_mb": res["memory_used_mb"],
            "peak_memory_mb": res.get("peak_memory_mb", res["memory_used_mb"]),
            "memory_leak_warning": res.get("memory_leak_warning", False),
            "fuel_consumed": res.get("fuel_consumed", 1420),
            "executed_at": now.isoformat()
        })
    except Exception:
        pass


@router.websocket("/ws")
async def websocket_route_ws(websocket: WebSocket, db=Depends(get_db)):
    await handle_websocket_execution(websocket, db)


@router.websocket("/ws/execute")
async def websocket_route_ws_execute(websocket: WebSocket, db=Depends(get_db)):
    await handle_websocket_execution(websocket, db)
