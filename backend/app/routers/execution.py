import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.schemas import ExecutionRequest, ExecutionResponse
from app.pipeline.validator import validate_python_code
from app.pipeline.compiler_cache import compiler_cache
from app.sandbox.wasmtime_runner import WasmSandboxRunner


router = APIRouter(prefix="/execute", tags=["Execution"])

_memory_executions = []


@router.post("", response_model=ExecutionResponse)
def execute_code(req: ExecutionRequest, db=Depends(get_db)):
    """
    Executes Python code inside the Wasmtime sandbox
    and records output/metrics in MongoDB.
    """

    code_to_run = req.code
    plugin_id = req.plugin_id

    # 1. Load plugin code if plugin_id is provided
    if plugin_id and db is not None:
        plugin = db["plugins"].find_one(
            {
                "_id": plugin_id,
                "tenant_id": req.tenant_id
            }
        )

        if not plugin:
            raise HTTPException(
                status_code=404,
                detail="Plugin not found for tenant"
            )

        code_to_run = plugin.get("code")

    if not code_to_run or not code_to_run.strip():
        raise HTTPException(
            status_code=400,
            detail="No Python code provided for execution"
        )

    # 2. Fetch sandbox policy
    mem_limit = 128
    timeout_sec = 5.0

    if db is not None:
        policy = db["sandbox_policies"].find_one(
            {
                "tenant_id": req.tenant_id
            }
        )

        if policy:
            mem_limit = policy.get(
                "memory_limit_mb",
                128
            )

            timeout_sec = policy.get(
                "timeout_sec",
                5.0
            )

    # 3. Security validation
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
            "output_result": {
                "error": "Security Violation",
                "details": violations
            },
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

    # 4. Compiler Cache
    #
    # If the same Python code was compiled before,
    # the cached harness is reused.
    #
    # If it is new, CompilerCache compiles it and
    # stores the result for future executions.
    bundled = compiler_cache.compile(code_to_run)

    # 5. Execute inside Wasmtime sandbox
    runner = WasmSandboxRunner(
        memory_limit_mb=mem_limit,
        timeout_sec=timeout_sec
    )

    res = runner.execute(
        bundled,
        req.input_data
    )

    # 6. Save execution result
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