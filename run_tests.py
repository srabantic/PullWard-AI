import unittest
import sys
import os

# Ensure src and tests directories are on sys.path
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base_dir, "src"))
sys.path.insert(0, base_dir)

from ast_analyzer import analyze_file_changes
from agents.security_agent import SecurityAgent
from agents.schema_agent import SchemaAgent
from agents.ast_agent import ASTGovernanceAgent
from agents.orchestrator import PullWardOrchestrator


class TestASTAnalyzer(unittest.TestCase):
    def test_python_ast_function_removed(self):
        old_code = "def existing_function(a, b):\n    return a + b"
        new_code = "# Function removed"
        res = analyze_file_changes("service.py", old_code, new_code)
        self.assertTrue(res["valid"])
        self.assertEqual(res["language"], "python")
        self.assertGreater(res["conflicts_count"], 0)
        self.assertTrue(any("Function 'existing_function' was removed" in b for b in res["breaking_changes"]))

    def test_python_ast_parameter_reduced(self):
        old_code = "def calculate_tax(amount, rate, discount):\n    return amount * rate - discount"
        new_code = "def calculate_tax(amount, rate):\n    return amount * rate"
        res = analyze_file_changes("tax.py", old_code, new_code)
        self.assertGreater(res["conflicts_count"], 0)
        self.assertTrue(any("reduced parameter list" in b for b in res["breaking_changes"]))

    def test_python_ast_class_removed(self):
        old_code = "class UserSession:\n    pass"
        new_code = "# Class removed"
        res = analyze_file_changes("session.py", old_code, new_code)
        self.assertGreater(res["conflicts_count"], 0)
        self.assertTrue(any("Class 'UserSession' was removed" in b for b in res["breaking_changes"]))

    def test_async_python_function(self):
        old_code = "async def fetch_data(url, timeout):\n    pass"
        new_code = "async def fetch_data(url):\n    pass"
        res = analyze_file_changes("async_service.py", old_code, new_code)
        self.assertGreater(res["conflicts_count"], 0)
        self.assertTrue(any("reduced parameter list" in b for b in res["breaking_changes"]))

    def test_regex_signature_typescript_removed(self):
        old_code = "export function processOrder(orderId: string) {}"
        new_code = "// Function removed"
        res = analyze_file_changes("order.ts", old_code, new_code)
        self.assertEqual(res["language"], "typescript")
        self.assertGreater(res["conflicts_count"], 0)
        self.assertTrue(any("processOrder" in b for b in res["breaking_changes"]))

    def test_sql_drop_table(self):
        old_code = "SELECT * FROM users;"
        new_code = "DROP TABLE users;"
        res = analyze_file_changes("migration.sql", old_code, new_code)
        self.assertEqual(res["language"], "sql")
        self.assertGreater(res["conflicts_count"], 0)
        self.assertTrue(any("DROP TABLE 'users'" in b for b in res["breaking_changes"]))


class TestAgents(unittest.TestCase):
    def test_security_agent_detects_secrets(self):
        agent = SecurityAgent(api_key="")
        diff_with_secret = 'api_key = "AIzaSySecretKey123456789012345678901"'
        result = agent.run(diff_with_secret)
        self.assertGreater(result["security_findings_count"], 0)

    def test_security_agent_detects_dangerous_eval(self):
        agent = SecurityAgent(api_key="")
        diff_with_eval = 'user_input = "2 + 2"; eval(user_input)'
        result = agent.run(diff_with_eval)
        self.assertGreater(result["security_findings_count"], 0)

    def test_schema_agent_detects_drop_table(self):
        agent = SchemaAgent(api_key="")
        diff_sql = "DROP TABLE audit_logs;"
        result = agent.run(diff_sql)
        self.assertTrue(result["schema_breaking_changes"])

    def test_orchestrator_decision_approved(self):
        orchestrator = PullWardOrchestrator()
        diff_files = [{
            "filename": "utils.py",
            "old_code": "def add(a, b): return a + b",
            "new_code": "def add(a, b): return a + b # comment"
        }]
        res = orchestrator.evaluate_pull_request("Clean PR", "diff content", diff_files)
        self.assertEqual(res["decision"], "APPROVED")


if __name__ == "__main__":
    unittest.main()
