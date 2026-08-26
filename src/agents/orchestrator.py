import os
from typing import Dict, Any, List
from google.adk import Agent
from google.genai import Client

from .ast_agent import ASTGovernanceAgent
from .security_agent import SecurityAgent
from .schema_agent import SchemaAgent

class PullWardOrchestrator:
    """Supervisor Agent that coordinates specialized domain agents for PR governance."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.adk_agent = Agent(
            name="pullward_orchestrator",
            model="gemini-3.6-flash",
            instruction="You are the lead PullWard AI Orchestrator coordinating security, AST, and schema agents."
        )
        self.ast_agent = ASTGovernanceAgent(api_key=self.api_key)
        self.security_agent = SecurityAgent(api_key=self.api_key)
        self.schema_agent = SchemaAgent(api_key=self.api_key)

    def evaluate_pull_request(self, pr_title: str, diff_text: str, diff_files: List[Dict[str, str]]) -> Dict[str, Any]:
        # 1. Execute Sub-Agents
        ast_result = self.ast_agent.run(diff_files)
        security_result = self.security_agent.run(diff_text)
        schema_result = self.schema_agent.run(diff_text)

        total_conflicts = ast_result["conflicts_count"]
        total_security_issues = security_result["security_findings_count"]
        has_schema_break = schema_result["schema_breaking_changes"]

        # 2. Determine Decision Status
        if total_security_issues > 0 or has_schema_break:
            decision = "BLOCKED"
        elif total_conflicts > 0:
            decision = "NEEDS_REVIEW"
        else:
            decision = "APPROVED"

        # 3. Consolidated Markdown Comment for GitHub PR
        comment_markdown = f"### 🛡️ PullWard AI Multi-Agent Governance Report\n\n"
        comment_markdown += f"**Overall Status**: `{decision}`\n\n"

        # AST Section
        if ast_result["findings"]:
            comment_markdown += "#### ⚠️ AST Breaking Changes:\n"
            for f in ast_result["findings"]:
                comment_markdown += f"* {f}\n"
            comment_markdown += f"\n*AST Agent Summary:* {ast_result['summary']}\n\n"
        else:
            comment_markdown += "✅ **AST Analysis**: No breaking signature changes.\n\n"

        # Security Section
        if security_result["findings"]:
            comment_markdown += "#### 🚨 Security & Secret Warnings:\n"
            for f in security_result["findings"]:
                comment_markdown += f"* {f}\n"
            comment_markdown += f"\n*Security Agent Summary:* {security_result['summary']}\n\n"
        else:
            comment_markdown += "✅ **Security Audit**: No secrets or unsafe patterns detected.\n\n"

        # Schema Section
        if schema_result["findings"]:
            comment_markdown += "#### 🗄️ Database & Schema Warnings:\n"
            for f in schema_result["findings"]:
                comment_markdown += f"* {f}\n"
            comment_markdown += f"\n*Schema Agent Summary:* {schema_result['summary']}\n\n"

        return {
            "decision": decision,
            "ast_conflicts_count": total_conflicts,
            "security_findings_count": total_security_issues,
            "schema_breaking_changes": has_schema_break,
            "comment_markdown": comment_markdown,
            "details": {
                "ast": ast_result,
                "security": security_result,
                "schema": schema_result
            }
        }


def run_pullward_governance_orchestrator(pr_title: str, diff_text: str, diff_files: List[Dict[str, str]]) -> Dict[str, Any]:
    orchestrator = PullWardOrchestrator()
    return orchestrator.evaluate_pull_request(pr_title, diff_text, diff_files)