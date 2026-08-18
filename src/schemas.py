import os
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

def create_bigquery_tables(project_id: str, dataset_id: str = "pullward_audit") -> None:
    """ Initializing the BigQuery dataset and audit log tables for PullWard AI."""
    print(f"connecting to BigQuery (Project: {project_id}, Dataset: {dataset_id})")

    # Initialize client 
    client = bigquery.Client(project=project_id)
    dataset_reference = bigquery.DatasetReference(project_id, dataset_id)

    # Create dataset if not already exist
    dataset = bigquery.Dataset(dataset_reference)
    dataset.location = "northamerica-northeast2"
    dataset = client.create_dataset(dataset, exists_ok=True)
    print(f"Dataset '{dataset_id}' ready.")

    # Define PR audit logs schema 
    pr_events_schema = [
        bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("repo_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("pr_number", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("author", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("ast_conflicts_count", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("security_findings_count", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("schema_breaking_changes", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
    ]

    # Create Table
    table_reference = dataset_reference.table("pr_audit_logs")
    table = bigquery.Table(table_reference, schema=pr_events_schema)
    table = client.create_table(table, exists_ok=True)
    print(f"Table '{table_reference.dataset_id}.{table_reference.table_id}' initialized successfully.")

if __name__ == "__main__":
    gcp_project = os.getenv("CGP_PROJECT_ID", "pullward-ai")
    create_bigquery_tables(project_id=gcp_project)
    