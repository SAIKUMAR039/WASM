import ast
from typing import List, Tuple
from app.config import settings

FORBIDDEN_BUILTINS = {"eval", "exec", "__import__", "open", "compile", "globals", "locals", "input"}
DISALLOWED_MODULES = {"os", "sys", "subprocess", "ctypes", "socket", "http", "urllib", "requests", "shutil", "pathlib", "threading", "multiprocessing"}

class SecurityValidationError(Exception):
    pass

class ASTSecurityVisitor(ast.NodeVisitor):
    def __init__(self, allowed_modules: List[str]):
        self.allowed_modules = set(allowed_modules)
        self.violations: List[str] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            mod_name = alias.name.split('.')[0]
            if mod_name in DISALLOWED_MODULES or (self.allowed_modules and mod_name not in self.allowed_modules):
                self.violations.append(f"Forbidden module import: '{alias.name}' (Line {node.lineno})")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            mod_name = node.module.split('.')[0]
            if mod_name in DISALLOWED_MODULES or (self.allowed_modules and mod_name not in self.allowed_modules):
                self.violations.append(f"Forbidden module import from '{node.module}' (Line {node.lineno})")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_BUILTINS:
            self.violations.append(f"Forbidden builtin function call: '{node.func.id}()' (Line {node.lineno})")
        elif isinstance(node.func, ast.Attribute) and node.func.attr in {"system", "popen", "remove", "rmdir", "unlink"}:
            self.violations.append(f"Forbidden system attribute access: '.{node.func.attr}' (Line {node.lineno})")
        self.generic_visit(node)

def validate_python_code(code: str, custom_allowed_modules: List[str] = None) -> Tuple[bool, List[str]]:
    """
    Parses Python source code into an AST and inspects it for security violations.
    Returns (is_valid, list_of_violations).
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, [f"Syntax Error: {e.msg} at line {e.lineno}"]

    allowed = custom_allowed_modules if custom_allowed_modules is not None else settings.ALLOWED_MODULES
    visitor = ASTSecurityVisitor(allowed_modules=allowed)
    visitor.visit(tree)

    if visitor.violations:
        return False, visitor.violations

    return True, []
