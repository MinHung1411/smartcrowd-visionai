# Databricks Deployment & Lakehouse Scripts

This folder contains utilities for automating Databricks Unity Catalog, Workflows, and Secret scopes:

- `deploy_separate_jobs.py`: Deploys individual Databricks Workflow Jobs (Bronze ingestion, Silver enrichment, Gold KPIs).
- `set_secrets.py`: Configures Databricks CLI secret scopes for storage and database connection credentials.
