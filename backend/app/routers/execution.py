import uuid
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db
from app.schemas import ExecutionRequest, ExecutionResponse
from app.pipeline.validator import validate_python_code
from app.pipeline.compiler import PythonWasmCompiler
from app.sandbox.wasmtime_runner import WasmSandboxRunner
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/execute", tags=["Execution"])

_memory_executions = []

@router.post("", response_model=ExecutionResponse)
def execute_code(
    req: ExecutionRequest,
    user=Depends(require_roles(["Admin", "Developer"])),
    db=Depends(get_db)
):
    """
    Executes Python code inside the Wasmtime sandbox and records execution in MongoDB.
    Restricted to Admin and Developer roles (Viewer denied).
    """
    code_to_run = req.code
    plugin_id = req.plugin_id
    tenant_id = user.get("tenant_id") or req.tenant_id or "tenant_default"

    if plugin_id and db is not None:
        plugin = db["plugins"].find_one({"_id": plugin_id, "tenant_id": tenant_id})
        if not plugin:
            plugin = db["plugins"].find_one({"_id": plugin_id})
        if not plugin:
            raise HTTPException(status_code=404, detail="Plugin not found for tenant")
        code_to_run = plugin.get("code")

    if not code_to_run or not code_to_run.strip():
        raise HTTPException(status_code=400, detail="No Python code provided for execution")

    # Fetch tenant policy document
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
        "tenant_id": tenant_id,
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
