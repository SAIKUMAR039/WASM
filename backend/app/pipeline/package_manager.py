import os
import re
import shutil
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Set, Any
from app.config import settings

NATIVE_BINARY_EXTENSIONS = {".so", ".pyd", ".dylib", ".dll", ".exe", ".bin"}

class WheelSecurityError(Exception):
    """Raised when a wheel contains unsafe or forbidden contents."""
    pass

@dataclass
class WheelInfo:
    name: str
    version: str
    filename: str
    path: str
    top_level_packages: List[str] = field(default_factory=list)
    is_pure_python: bool = True
    is_safe: bool = True
    files: List[str] = field(default_factory=list)

class WasmPackageManager:
    """
    Manages pre-packaged Python wheels for the WasmBox sandbox.
    Verifies pure-Python safety, prevents unsafe native binaries,
    and exposes allowlisted packages to the compiler and validator.
    """

    def __init__(self, wheels_dir: Optional[str] = None, allowed_wheels: Optional[List[str]] = None):
        self.wheels_dir = Path(wheels_dir) if wheels_dir else Path(settings.WHEELS_DIR)
        if not self.wheels_dir.is_absolute():
            # Resolve relative to project root / current working directory
            self.wheels_dir = Path.cwd() / self.wheels_dir
        self.wheels_dir.mkdir(parents=True, exist_ok=True)

        self._allowed_wheels: Set[str] = set(allowed_wheels or settings.ALLOWED_WHEELS)
        self._registry: Dict[str, WheelInfo] = {}
        self.refresh()

    def refresh(self):
        """Scans the wheels directory and indexes all valid pre-packaged wheels."""
        self._registry.clear()
        if not self.wheels_dir.exists():
            return

        for entry in self.wheels_dir.glob("*.whl"):
            try:
                info = self.inspect_wheel(str(entry))
                self._registry[info.name.lower()] = info
            except Exception:
                # Corrupted or invalid wheels are skipped during scanning
                continue

    @classmethod
    def inspect_wheel(cls, wheel_path: str) -> WheelInfo:
        """
        Inspects a .whl file archive to verify safety, extract metadata,
        and discover top-level package names.
        """
        path = Path(wheel_path)
        if not path.exists():
            raise FileNotFoundError(f"Wheel file not found: {wheel_path}")
        if not path.name.endswith(".whl"):
            raise ValueError(f"File is not a Python wheel (.whl): {path.name}")

        # Parse filename per PEP 427: {distribution}-{version}(-{build tag})?-{python tag}-{abi tag}-{platform tag}.whl
        stem = path.stem
        parts = stem.split("-")
        if len(parts) < 3:
            raise ValueError(f"Invalid wheel filename structure: {path.name}")

        name = parts[0].replace("_", "-")
        version = parts[1]

        # Check pure-python tags (py2.py3-none-any or py3-none-any)
        is_pure_python = "none-any" in stem or "py3-none-any" in stem or "py2.py3-none-any" in stem

        top_level_packages: Set[str] = set()
        file_list: List[str] = []
        is_safe = True

        with zipfile.ZipFile(path, 'r') as zf:
            for item in zf.infolist():
                filename = item.filename
                file_list.append(filename)
                
                # Check for forbidden native binary extensions
                suffix = Path(filename).suffix.lower()
                if suffix in NATIVE_BINARY_EXTENSIONS:
                    is_safe = False
                    raise WheelSecurityError(
                        f"Wheel '{path.name}' contains unsafe native binary: '{filename}'. "
                        "WasmBox only supports pure-Python wheels."
                    )

                # Check top_level.txt if present
                if filename.endswith(".dist-info/top_level.txt"):
                    try:
                        content = zf.read(filename).decode("utf-8")
                        for line in content.splitlines():
                            pkg = line.strip()
                            if pkg and not pkg.startswith("#"):
                                top_level_packages.add(pkg)
                    except Exception:
                        pass

                # Infer top level package from directories/files if top_level.txt not found
                if "/" in filename:
                    root_part = filename.split("/")[0]
                    if not root_part.endswith(".dist-info") and not root_part.endswith(".data"):
                        top_level_packages.add(root_part)
                elif filename.endswith(".py"):
                    top_level_packages.add(Path(filename).stem)

        if not top_level_packages:
            top_level_packages.add(name.replace("-", "_"))

        return WheelInfo(
            name=name,
            version=version,
            filename=path.name,
            path=str(path.resolve()),
            top_level_packages=sorted(list(top_level_packages)),
            is_pure_python=is_pure_python,
            is_safe=is_safe,
            files=file_list
        )

    def register_wheel(self, wheel_path: str, allow: bool = True) -> WheelInfo:
        """
        Validates and copies/registers a wheel into the package manager.
        """
        info = self.inspect_wheel(wheel_path)
        dest = self.wheels_dir / Path(wheel_path).name
        if Path(wheel_path).resolve() != dest.resolve():
            shutil.copy2(wheel_path, dest)
            info.path = str(dest.resolve())

        self._registry[info.name.lower()] = info
        if allow:
            self._allowed_wheels.add(info.name.lower())
        return info

    def get_wheel(self, name: str) -> Optional[WheelInfo]:
        """Fetch indexed wheel information by distribution or package name."""
        k = name.lower()
        if k in self._registry:
            return self._registry[k]
        norm = k.replace("_", "-")
        if norm in self._registry:
            return self._registry[norm]
        norm_us = k.replace("-", "_")
        if norm_us in self._registry:
            return self._registry[norm_us]
        # Check by exported package name
        for info in self._registry.values():
            if name in info.top_level_packages or k in [p.lower() for p in info.top_level_packages]:
                return info
        return None

    def list_available_wheels(self) -> List[WheelInfo]:
        """Return all valid wheels discovered in the wheels directory."""
        return list(self._registry.values())

    def get_allowed_packages(self) -> Set[str]:
        """
        Returns all top-level Python importable module names provided
        by the allowlisted wheels.
        """
        allowed_packages: Set[str] = set()
        for key, info in self._registry.items():
            if not self._allowed_wheels or key in self._allowed_wheels or info.name.lower() in self._allowed_wheels:
                for pkg in info.top_level_packages:
                    allowed_packages.add(pkg)
        return allowed_packages

    def unpack_wheel(self, wheel_name_or_path: str, target_dir: str) -> str:
        """
        Safely extracts a registered wheel into target_dir.
        Guards against directory traversal (zip slip).
        """
        target_path = Path(target_dir).resolve()
        target_path.mkdir(parents=True, exist_ok=True)

        if Path(wheel_name_or_path).exists():
            wheel_file = Path(wheel_name_or_path)
        elif wheel_name_or_path.lower() in self._registry:
            wheel_file = Path(self._registry[wheel_name_or_path.lower()].path)
        else:
            raise FileNotFoundError(f"Wheel '{wheel_name_or_path}' not found")

        with zipfile.ZipFile(wheel_file, 'r') as zf:
            for member in zf.infolist():
                dest_file = (target_path / member.filename).resolve()
                if not str(dest_file).startswith(str(target_path)):
                    raise WheelSecurityError(f"Directory traversal detected in wheel: '{member.filename}'")
                zf.extract(member, target_path)

        return str(target_path)

    def analyze_dependencies(self, code: str) -> Dict[str, Any]:
        """
        Parses Python code to extract all imported modules, then classifies each:
        - 'stdlib_safe': safe standard library module (math, json, datetime, etc.)
        - 'wheel_available': provided by an installed pure-Python wheel
        - 'blocked': explicitly forbidden system module (os, sys, subprocess, etc.)
        - 'unknown': unresolvable external import
        """
        import ast
        from app.config import SAFE_STDLIB_MODULES
        from app.pipeline.validator import DISALLOWED_MODULES

        dependencies = []
        missing = []
        blocked = []

        try:
            tree = ast.parse(code)
        except Exception:
            return {
                "total_imports": 0,
                "is_compatible": False,
                "dependencies": [],
                "missing_dependencies": [],
                "blocked_dependencies": []
            }

        imported_items = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_items.append((alias.name, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_items.append((node.module, node.lineno))

        allowed_wheel_pkgs = self.get_allowed_packages()

        for mod_name, lineno in imported_items:
            root_mod = mod_name.split(".")[0]
            if root_mod in DISALLOWED_MODULES:
                status = "blocked"
                source = "Disallowed system module"
                is_compat = False
                blocked.append(mod_name)
            elif root_mod in SAFE_STDLIB_MODULES:
                status = "stdlib_safe"
                source = f"Standard Library ({root_mod})"
                is_compat = True
            elif root_mod in allowed_wheel_pkgs:
                wheel_info = self.get_wheel(root_mod)
                status = "wheel_available"
                source = f"Wheel: {wheel_info.name} v{wheel_info.version}" if wheel_info else "Wheel package"
                is_compat = True
            else:
                status = "unknown"
                source = "External / Not found"
                is_compat = False
                missing.append(mod_name)

            dependencies.append({
                "module": mod_name,
                "status": status,
                "source": source,
                "line_number": lineno,
                "is_compatible": is_compat
            })

        is_all_compatible = len(blocked) == 0 and len(missing) == 0

        return {
            "total_imports": len(dependencies),
            "is_compatible": is_all_compatible,
            "dependencies": dependencies,
            "missing_dependencies": list(set(missing)),
            "blocked_dependencies": list(set(blocked))
        }

_default_package_manager: Optional[WasmPackageManager] = None

def get_package_manager() -> WasmPackageManager:
    global _default_package_manager
    if _default_package_manager is None:
        _default_package_manager = WasmPackageManager()
    return _default_package_manager
