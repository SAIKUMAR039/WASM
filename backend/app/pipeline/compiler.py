import json
from typing import Dict, Any

class WasmCompilationError(Exception):
    pass

class PythonWasmCompiler:
    """
    Transforms user-provided Python code into an execution harness module.
    Supports top-level scripts (print statements, calculations) as well as 
    structured function entrypoints like process(data) or main(data).
    """
    
    ENTRY_HARNESS_TEMPLATE = """# WasmBox Generated Execution Harness
import json
import sys
import math
import re
import datetime
import random
import hashlib
import collections
import itertools
import functools
import base64
import zlib

# --- USER PLUGIN CODE START ---
{user_code}
# --- USER PLUGIN CODE END ---

def _wasmbox_main(raw_input_json):
    data = None
    if raw_input_json:
        try:
            data = json.loads(raw_input_json)
        except Exception:
            data = raw_input_json

    target_func = None
    if 'process' in globals() and callable(globals()['process']):
        target_func = globals()['process']
    elif 'main' in globals() and callable(globals()['main']):
        target_func = globals()['main']
    elif 'process' in locals() and callable(locals()['process']):
        target_func = locals()['process']
    elif 'main' in locals() and callable(locals()['main']):
        target_func = locals()['main']

    res = None
    if target_func:
        res = target_func(data)

    if res is not None:
        try:
            return json.dumps(res)
        except Exception:
            return str(res)
    return "__WASMBOX_NO_RETURN__"

if __name__ == "__main__":
    input_str = sys.stdin.read() if not sys.stdin.isatty() else ""
    out = _wasmbox_main(input_str)
    print("---WASMSOUTPUT_START---")
    print(out)
    print("---WASMSOUTPUT_END---")
"""

    @classmethod
    def compile_plugin(cls, code: str) -> str:
        """
        Bundles user python code into the Wasm execution harness string.
        """
        if not code or not code.strip():
            raise WasmCompilationError("Code snippet cannot be empty")
        
        return cls.ENTRY_HARNESS_TEMPLATE.format(user_code=code)
