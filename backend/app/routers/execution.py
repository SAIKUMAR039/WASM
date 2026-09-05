import uuid
import json
import asyncio
import threading
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from app.database import get_db
from app.schemas import ExecutionRequest, ExecutionResponse
from app.pipeline.validator import validate_python_code
from app.pipeline.compiler import PythonWasmCompiler
from app.sandbox.wasmtime_runner import WasmSandboxRunner

router = APIRouter(prefix="/execute", tags=["Execution"])

_memory_executions = []

@router.post("", response_model=ExecutionResponse)
def execute_code(req: ExecutionRequest, db=Depends(get_db)):
    """
    Executes Python code inside the Wasmtime sandbox and records output/metrics document in MongoDB.
    """
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
    bundled = PythonWasmCompiler.compile_plugin(code_to_run)

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
        "executed_at": now
    }

    if db is not None:
        db["executions"].insert_one(exec_doc)
    else:
        _memory_executions.append(exec_doc)

    return exec_doc


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

    bundled = PythonWasmCompiler.compile_plugin(code_to_run)
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

