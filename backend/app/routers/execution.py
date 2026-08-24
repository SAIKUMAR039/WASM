import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Plugin, Execution, SandboxPolicy
from app.schemas import ExecutionRequest, ExecutionResponse
from app.pipeline.validator import validate_python_code
from app.pipeline.compiler import PythonWasmCompiler
from app.sandbox.wasmtime_runner import WasmSandboxRunner

router = APIRouter(prefix="/execute", tags=["Execution"])

@router.post("", response_model=ExecutionResponse)
def execute_code(req: ExecutionRequest, db: Session = Depends(get_db)):
    """
    Executes Python code or a saved plugin inside the Wasmtime sandbox environment.
    Runs static security validation, WASM packaging, and returns metrics & execution output.
    """
    code_to_run = req.code
    plugin_id = req.plugin_id

    # If plugin_id provided, fetch plugin from database
    if plugin_id:
        plugin = db.query(Plugin).filter(Plugin.id == plugin_id, Plugin.tenant_id == req.tenant_id).first()
        if not plugin:
            raise HTTPException(status_code=404, detail="Plugin not found for tenant")
        code_to_run = plugin.code

    if not code_to_run or not code_to_run.strip():
        raise HTTPException(status_code=400, detail="No Python code provided for execution")

    # Fetch tenant sandbox policy
    policy = db.query(SandboxPolicy).filter(SandboxPolicy.tenant_id == req.tenant_id).first()
    mem_limit = policy.memory_limit_mb if policy else 128
    timeout_sec = policy.timeout_sec if policy else 5.0

    # 1. AST Security Validation
    is_valid, violations = validate_python_code(code_to_run)
    if not is_valid:
        exec_record = Execution(
            plugin_id=plugin_id,
            tenant_id=req.tenant_id,
            status="SECURITY_VIOLATION",
            input_data=json.dumps(req.input_data),
            output_result=json.dumps({"error": "Security Violation", "details": violations}),
            stdout="",
            stderr="\n".join(violations),
            execution_time_sec=0.001,
            memory_used_mb=0.0
        )
        db.add(exec_record)
        db.commit()
        db.refresh(exec_record)
        
        return ExecutionResponse(
            id=exec_record.id,
            plugin_id=plugin_id,
            status="SECURITY_VIOLATION",
            output_result={"error": "Security Violation", "details": violations},
            stdout="",
            stderr="\n".join(violations),
            execution_time_sec=0.001,
            memory_used_mb=0.0,
            executed_at=exec_record.executed_at
        )

    # 2. Package / Compile into WASM Harness
    bundled = PythonWasmCompiler.compile_plugin(code_to_run)

    # 3. Execute in Wasmtime Sandbox Runner
    runner = WasmSandboxRunner(memory_limit_mb=mem_limit, timeout_sec=timeout_sec)
    res = runner.execute(bundled, req.input_data)

    # 4. Save Execution Record & Metrics
    exec_record = Execution(
        plugin_id=plugin_id,
        tenant_id=req.tenant_id,
        status=res["status"],
        input_data=json.dumps(req.input_data),
        output_result=json.dumps(res["output_result"]) if not isinstance(res["output_result"], str) else res["output_result"],
        stdout=res["stdout"],
        stderr=res["stderr"],
        execution_time_sec=res["execution_time_sec"],
        memory_used_mb=res["memory_used_mb"]
    )
    db.add(exec_record)
    db.commit()
    db.refresh(exec_record)

    return ExecutionResponse(
        id=exec_record.id,
        plugin_id=plugin_id,
        status=res["status"],
        output_result=res["output_result"],
        stdout=res["stdout"],
        stderr=res["stderr"],
        execution_time_sec=res["execution_time_sec"],
        memory_used_mb=res["memory_used_mb"],
        executed_at=exec_record.executed_at
    )
