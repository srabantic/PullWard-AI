import os
import sys

# Ensure src directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from agents.security_agent import SecurityAgent
from agents.schema_agent import SchemaAgent
from agents.ast_agent import ASTGovernanceAgent
from agents.orchestrator import PullWardOrchestrator


def test_security_agent_detects_secrets():
    agent = SecurityAgent(api_key="")  # Run deterministic checks without Gemini API call
    diff_with_secret = 'api_key = "AIzaSySecretKey123456789012345678901"'
    result = agent.run(diff_with_secret)

    assert result["security_findings_count"] > 0
    assert any("Potential Hardcoded Secret" in f or "Exposed Google API Key" in f for f in result["findings"])


def test_security_agent_detects_dangerous_eval():
    agent = SecurityAgent(api_key="")
    diff_with_eval = 'user_input = "2 + 2"; eval(user_input)'
    result = agent.run(diff_with_eval)

    assert result["security_findings_count"] > 0
    assert any("eval()" in f for f in result["findings"])


def test_schema_agent_detects_drop_table():
    agent = SchemaAgent(api_key="")
    diff_sql = "DROP TABLE audit_logs;"
    result = agent.run(diff_sql)

    assert result["schema_breaking_changes"] is True
    assert any("DROP TABLE 'audit_logs'" in f for f in result["findings"])


def test_ast_agent_finds_conflicts():
    agent = ASTGovernanceAgent(api_key="")
    diff_files = [{
        "filename": "auth.py",
        "old_code": "def login(username, password): pass",
        "new_code": "def login(username): pass"
    }]
    result = agent.run(diff_files)

    assert result["conflicts_count"] > 0
    assert len(result["findings"]) > 0


def test_orchestrator_decision_approved():
    orchestrator = PullWardOrchestrator()
    # Mock clean diff
    diff_files = [{
        "filename": "utils.py",
        "old_code": "def add(a, b): return a + b",
        "new_code": "def add(a, b): return a + b # add comment"
    }]
    res = orchestrator.evaluate_pull_request("Clean PR", "diff content", diff_files)

    assert res["decision"] == "APPROVED"
    assert "Overall Status" in res["comment_markdown"]


def test_orchestrator_decision_blocked_on_security():
    orchestrator = PullWardOrchestrator()
    diff_text = 'api_key = "AIzaSySecretKey123456789012345678901"'
    diff_files = []

    res = orchestrator.evaluate_pull_request("Insecure PR", diff_text, diff_files)
    assert res["decision"] == "BLOCKED"
