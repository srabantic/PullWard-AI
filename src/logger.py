import os
import uuid
from datetime import datetime, timezone
from google.cloud import bigquery
from typing import Dict, Any

def log_pr_audit_event(
    repo_name: str,
    pr_number: int,
    author: str,
    ast_conflicts_count: int,
    security_findings_count: int,
    schema_breaking_changes: bool,
    project_id: str = None
) -> Dict[str, Any]:
    """
    Streams a PullWard AI audit log entry directly into BigQuery.
    Falls back gracefully to local console logging if BigQuery is unavailable.
    """
    if not project_id:
        project_id = os.getenv("GCP_PROJECT_ID", "pullward-ai")

    event_id = str(uuid.uuid4())
    row_to_insert = {
        "event_id": event_id,
        "repo_name": repo_name,
        "pr_number": pr_number,
        "author": author,
        "ast_conflicts_count": ast_conflicts_count,
        "security_findings_count": security_findings_count,
        "schema_breaking_changes": schema_breaking_changes,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        client = bigquery.Client(project=project_id)
        dataset_id = f"{project_id}.pullward_audit"
        table_id = f"{dataset_id}.pr_audit_logs"

        errors = client.insert_rows_json(table_id, [row_to_insert])

        if not errors:
            print(f"Successfully streamed audit log for PR #{pr_number} in {repo_name} to BigQuery.")
            return {"status": "success", "event_id": event_id}
        else:
            print(f"Failed to stream audit log to BigQuery: {errors}")
            return {"status": "error", "details": errors, "event_id": event_id}

    except Exception as e:
        # Fallback to local console log if GCP/BigQuery authentication is missing
        print(f"[LOCAL AUDIT LOG] GCP BigQuery stream skipped ({e}). Event payload: {row_to_insert}")
        return {"status": "local_fallback", "event_id": event_id}


if __name__ == "__main__":
    test_result = log_pr_audit_event(
        repo_name="Google-Patchamomma/PullWard-AI",
        pr_number=42,
        author="srabantichakraborty",
        ast_conflicts_count=1,
        security_findings_count=0,
        schema_breaking_changes=True
    )
    print("Test Log Streaming Output:", test_result)