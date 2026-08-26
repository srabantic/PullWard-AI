import os
from typing import Dict, Any, List
from google.genai import Client
from ast_analyzer import analyze_file_changes

class ASTGovernanceAgent:
    """Agent focused on code structure, AST shifts, and breaking API contract changes."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.client = Client(api_key=self.api_key) if self.api_key else None

    def run(self, diff_files: List[Dict[str, str]]) -> Dict[str, Any]:
        findings = []
        conflicts_count = 0

        # 1. Run deterministic static AST analysis across all modified files
        for f in diff_files:
            filename = f.get("filename", "")
            old_code = f.get("old_code", "")
            new_code = f.get("new_code", "")

            analysis = analyze_file_changes(filename, old_code, new_code)
            breaking = analysis.get("breaking_changes", [])

            if breaking:
                for b in breaking:
                    findings.append(f"`{filename}`: {b}")
                    conflicts_count += 1

        # 2. AI assessment of structural changes
        ai_insight = "Static AST analysis completed cleanly."
        if self.client and findings:
            prompt = f"""
You are the AST & API Governance Sub-Agent for PullWard AI.
Review the following list of detected breaking AST changes:
{findings}

Summarize in 2 sentences the architectural risk of these removed/altered definitions for downstream callers.
"""
            try:
                response = self.client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt
                )
                ai_insight = response.text.strip()
            except Exception as e:
                ai_insight = f"AI AST analysis fallback: {str(e)}"

        return {
            "agent": "ASTGovernanceAgent",
            "conflicts_count": conflicts_count,
            "findings": findings,
            "summary": ai_insight
        }


def analyze_ast_governance(diff_files: List[Dict[str, str]]) -> Dict[str, Any]:
    agent = ASTGovernanceAgent()
    return agent.run(diff_files)