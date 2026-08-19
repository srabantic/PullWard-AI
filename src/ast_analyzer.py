import ast
import re
from typing import Dict, List, Any

# File extension mapping
LANGUAGE_MAP = {
    ".py": "python",
    ".cs": "csharp",
    ".ts": "typescript",
    ".js": "javascript",
    ".java": "java",
    ".go": "go",
    ".sql": "sql",
    ".json": "config",
    ".yaml": "config",
    ".yml": "config"
}

class PythonASTVisitor(ast.NodeVisitor):
    def __init__(self):
        self.functions: Dict[str, List[str]] = {}
        self.classes: set = set()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        args = [arg.arg for arg in node.args.args]
        self.functions[node.name] = args
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.classes.add(node.name)
        self.generic_visit(node)


def _analyze_python(old_code: str, new_code: str) -> List[str]:
    breaking_changes = []
    try:
        old_tree = ast.parse(old_code)
        new_tree = ast.parse(new_code)
    except SyntaxError as e:
        return [f"Python Syntax Error: {e}"]

    old_vis, new_vis = PythonASTVisitor(), PythonASTVisitor()
    old_vis.visit(old_tree)
    new_vis.visit(new_tree)

    # Detect removed functions or reduced args
    for func, old_args in old_vis.functions.items():
        if func not in new_vis.functions:
            breaking_changes.append(f"Function '{func}' was removed.")
        elif len(new_vis.functions[func]) < len(old_args):
            breaking_changes.append(f"Function '{func}' reduced parameter list from {old_args} to {new_vis.functions[func]}.")

    # Detect removed classes
    for cls in old_vis.classes:
        if cls not in new_vis.classes:
            breaking_changes.append(f"Class '{cls}' was removed.")

    return breaking_changes


def _analyze_regex_signatures(old_code: str, new_code: str, lang: str) -> List[str]:
    """
    Parses structural method/class definitions for C#, TypeScript, JavaScript, Java, Go.
    """
    breaking_changes = []
    
    # Standard function/method definition regex patterns
    patterns = {
        "csharp": r'(?:public|private|protected|internal)\b.*?\b(\w+)\s*\(',
        "typescript": r'(?:export\s+)?(?:function|class|const)\s+(\w+)',
        "javascript": r'(?:export\s+)?(?:function|class|const)\s+(\w+)',
        "java": r'(?:public|protected|private)\b.*?\b(\w+)\s*\(',
        "go": r'func\s+(\w+)\s*\('
    }

    pattern = patterns.get(lang)
    if not pattern:
        return []

    old_symbols = set(re.findall(pattern, old_code))
    new_symbols = set(re.findall(pattern, new_code))

    removed = old_symbols - new_symbols
    for sym in removed:
        breaking_changes.append(f"[{lang.upper()}] Definition '{sym}' was removed or renamed.")

    return breaking_changes


def _analyze_sql_config(old_code: str, new_code: str, lang: str) -> List[str]:
    """
    Checks for high-risk breaking statements in SQL and config files.
    """
    breaking_changes = []
    if lang == "sql":
        drops = re.findall(r'DROP\s+(TABLE|COLUMN|DATABASE)\s+(\w+)', new_code, re.IGNORECASE)
        for target_type, name in drops:
            breaking_changes.append(f"[SQL] High-risk breaking statement: DROP {target_type.upper()} '{name}'.")
    return breaking_changes


def analyze_file_changes(filename: str, old_code: str, new_code: str) -> Dict[str, Any]:
    """
    Universal entry point to analyze breaking changes across ANY file type.
    """
    ext = f".{filename.split('.')[-1].lower()}" if "." in filename else ""
    lang = LANGUAGE_MAP.get(ext, "unknown")

    breaking_changes = []

    if lang == "python":
        breaking_changes = _analyze_python(old_code, new_code)
    elif lang in ["csharp", "typescript", "javascript", "java", "go"]:
        breaking_changes = _analyze_regex_signatures(old_code, new_code, lang)
    elif lang in ["sql", "config"]:
        breaking_changes = _analyze_sql_config(old_code, new_code, lang)

    return {
        "filename": filename,
        "language": lang,
        "valid": True,
        "breaking_changes": breaking_changes,
        "conflicts_count": len(breaking_changes)
    }


if __name__ == "__main__":
    print("--- Testing Python ---")
    py_res = analyze_file_changes("service.py", "def getUser(id, token): pass", "def getUser(id): pass")
    print(py_res)

    print("\n--- Testing C# ---")
    cs_res = analyze_file_changes("UserController.cs", "public async Task GetUser(int id) {}", "public int OldUser() {}")
    print(cs_res)

    print("\n--- Testing TypeScript ---")
    ts_res = analyze_file_changes("api.ts", "export function fetchOrders() {}", "const x = 10;")
    print(ts_res)

    print("\n--- Testing SQL ---")
    sql_res = analyze_file_changes("migration.sql", "SELECT * FROM users;", "DROP TABLE users;")
    print(sql_res)