import json
from typing import Dict, Any

class WasmCompilationError(Exception):
    pass

class PythonWasmCompiler:
    """
    Transforms user-provided Python plugin code into a WebAssembly-compatible 
    executable module harness. Standardizes entry point `process(data)` execution.
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
    try:
        data = json.loads(raw_input_json) if raw_input_json else None
    except Exception as e:
        data = raw_input_json

    if 'process' in globals() and callable(globals()['process']):
        res = process(data)
    elif 'main' in globals() and callable(globals()['main']):
        res = main(data)
    else:
        res = {{"error": "No process(data) or main(data) function defined in plugin"}}
    
    return json.dumps(res)

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
