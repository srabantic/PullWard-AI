import ast
import re
from typing import Dict, List, Any

# Code file extension mapping (AST & Contract analysis)
LANGUAGE_MAP = {
    ".py": "python",
    ".cs": "csharp",
    ".ts": "typescript",
    ".js": "javascript",
    ".java": "java",
    ".go": "go"
}

class PythonASTVisitor(ast.NodeVisitor):
    def __init__(self):
        self.functions: Dict[str, List[str]] = {}
        self.classes: set = set()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        args = [arg.arg for arg in node.args.args]
        self.functions[node.name] = args
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Catches Python async functions (async def ...)."""
        args = [arg.arg for arg in node.args.args]
        self.functions[node.name] = args
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.classes.add(node.name)
        self.generic_visit(node)


import textwrap

def _analyze_python(old_code: str, new_code: str) -> List[str]:
    breaking_changes = []

    try:
        # Dedent code snippets so indented diff blocks parse cleanly
        old_clean = textwrap.dedent(old_code)
        new_clean = textwrap.dedent(new_code)
        old_tree = ast.parse(old_clean)
        new_tree = ast.parse(new_clean)

        old_vis, new_vis = PythonASTVisitor(), PythonASTVisitor()
        old_vis.visit(old_tree)
        new_vis.visit(new_tree)

        # Detect removed functions or reduced parameters
        for func, old_args in old_vis.functions.items():
            if func not in new_vis.functions:
                breaking_changes.append(f"Function '{func}' was removed.")
            elif len(new_vis.functions[func]) < len(old_args):
                breaking_changes.append(f"Function '{func}' reduced parameter list from {old_args} to {new_vis.functions[func]}.")

        # Detect removed classes
        for cls in old_vis.classes:
            if cls not in new_vis.classes:
                breaking_changes.append(f"Class '{cls}' was removed.")

    except (SyntaxError, IndentationError):
        # Fallback to robust regex analysis if git diff chunk is a partial snippet
        breaking_changes = _analyze_regex_signatures(old_code, new_code, "python")

    return breaking_changes


def _analyze_regex_signatures(old_code: str, new_code: str, lang: str) -> List[str]:
    """Parses structural method/class definitions for C#, TS, JS, Java, Go, Python snippets."""
    breaking_changes = []
    
    # 1. Class removal check
    class_pattern = r'\bclass\s+(\w+)'
    old_classes = set(re.findall(class_pattern, old_code))
    new_classes = set(re.findall(class_pattern, new_code))
    for cls in (old_classes - new_classes):
        breaking_changes.append(f"[{lang.upper()}] Class '{cls}' was removed.")

    # 2. Function / Method parameter reduction check
    func_param_pattern = r'(?:def|function|func)\s+(\w+)\s*\((.*?)\)'
    old_funcs = dict(re.findall(func_param_pattern, old_code))
    new_funcs = dict(re.findall(func_param_pattern, new_code))
    for func, old_param_str in old_funcs.items():
        if func not in new_funcs:
            breaking_changes.append(f"[{lang.upper()}] Function '{func}' was removed.")
        else:
            old_params = [p.strip() for p in old_param_str.split(',') if p.strip()]
            new_params = [p.strip() for p in new_funcs[func].split(',') if p.strip()]
            if len(new_params) < len(old_params):
                breaking_changes.append(f"[{lang.upper()}] Function '{func}' reduced parameter list from {old_params} to {new_params}.")

    # 3. Signature removal check
    patterns = {
        "python": r'(?:async\s+)?def\s+(\w+)\s*\(',
        "csharp": r'(?:public|private|protected|internal)\b.*?\b(\w+)\s*\(',
        "typescript": r'(?:export\s+)?(?:function|class|const)\s+(\w+)',
        "javascript": r'(?:export\s+)?(?:function|class|const)\s+(\w+)',
        "java": r'(?:public|protected|private)\b.*?\b(\w+)\s*\(',
        "go": r'func\s+(\w+)\s*\('
    }

    pattern = patterns.get(lang)
    if pattern:
        old_symbols = set(re.findall(pattern, old_code))
        new_symbols = set(re.findall(pattern, new_code))
        removed = old_symbols - new_symbols
        for sym in removed:
            if not any(sym in b for b in breaking_changes):
                breaking_changes.append(f"[{lang.upper()}] Definition '{sym}' was removed or renamed.")

    return breaking_changes


def analyze_file_changes(filename: str, old_code: str, new_code: str) -> Dict[str, Any]:
    """Universal entry point to analyze breaking code contract changes across supported programming languages."""
    ext = f".{filename.split('.')[-1].lower()}" if "." in filename else ""
    lang = LANGUAGE_MAP.get(ext, "unknown")

    breaking_changes = []

    if lang == "python":
        breaking_changes = _analyze_python(old_code, new_code)
    elif lang in ["csharp", "typescript", "javascript", "java", "go"]:
        breaking_changes = _analyze_regex_signatures(old_code, new_code, lang)

    return {
        "filename": filename,
        "language": lang,
        "valid": lang != "unknown",
        "breaking_changes": breaking_changes,
        "conflicts_count": len(breaking_changes)
    }


if __name__ == "__main__":
    print("--- Testing Python (Async & Sync) ---")
    py_res = analyze_file_changes("service.py", "async def getUser(id, token): pass", "def getUser(id): pass")
    print(py_res)