#!/usr/bin/env python3
import sys
from pathlib import Path
import importlib.util

_root_dir = Path(__file__).resolve().parent.parent
_cli_path = _root_dir / "build_plugin.py"

if not _cli_path.exists():
    sys.stderr.write("Root build_plugin.py not found.\n")
    sys.exit(1)

_spec = importlib.util.spec_from_file_location("_root_build_plugin", str(_cli_path))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

main = _mod.main
parse_args = _mod.parse_args

if __name__ == "__main__":
    sys.exit(main())


