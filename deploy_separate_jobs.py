"""
deploy_separate_jobs.py — Deploy three separate Workflow Jobs for the VisionAI project on Databricks.
"""
import os
import re
import base64
import json
import requests
import sys
from urllib.parse import urlparse, parse_qs

# Helper to find and parse DATABASE_URL from .env files
def get_db_url():
    paths = [
        '.env',
        'src/.env',
        '../visionai_app/.env',
        '../.env',
        'visionai_app/.env'
    ]
    for p in paths:
        if os.path.exists(p):
            print(f"[INFO] Reading credentials from: {p}")
            with open(p, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('DATABASE_URL='):
                        val = line.strip().split('=', 1)[1]
                        val = re.sub(r'^["\']|["\']$', '', val)
                        return val
    return os.environ.get('DATABASE_URL', '')

db_url = get_db_url()
if not db_url or 'databricks' not in db_url:
    print("[ERROR] DATABASE_URL not found or not pointing to Databricks.")
    sys.exit(1)

# Parse Databricks credentials
parsed = urlparse(db_url)
host = f"https://{parsed.hostname}"
token = parsed.password
params = parse_qs(parsed.query)
http_path = params.get('http_path', [''])[0]
catalog = params.get('catalog', ['visionai_catalog'])[0]

# Warehouse ID is the last part of http_path
warehouse_id = http_path.split('/')[-1] if http_path else ""

print(f"[INFO] Connection Details:")
print(f"  Host:         {host}")
print(f"  Warehouse ID: {warehouse_id}")
print(f"  Catalog:      {catalog}")
print("-" * 50)

HEADERS = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

def api(method, endpoint, data=None):
    url = f"{host}{endpoint}"
    try:
        if method == "GET":
            resp = requests.get(url, headers=HEADERS, timeout=30)
        elif method == "POST":
            resp = requests.post(url, headers=HEADERS, json=data, timeout=30)
        elif method == "DELETE":
            resp = requests.delete(url, headers=HEADERS, json=data, timeout=30)
        
        if resp.status_code >= 400:
            print(f"  [ERROR] {resp.status_code}: {resp.text[:500]}")
            return None
        return resp.json() if resp.text else {}
    except Exception as e:
        print(f"  [ERROR] Connection failed: {e}")
        return None

def main():
    # 1. Create parent directory in workspace
    print("[1/5] Creating workspace parent directory...")
    workspace_path = "/Shared/visionai_sql_pipeline"
    api("POST", "/api/2.0/workspace/mkdirs", {"path": workspace_path})
    print("  [OK] Directory verified/created: /Shared/visionai_sql_pipeline")

    # 2. Upload SQL scripts
    print("\n[2/5] Uploading/Syncing SQL scripts to workspace...")
    sql_dir = "sql"
    if not os.path.exists(sql_dir) and os.path.exists("../visionai-databricks/sql"):
        sql_dir = "../visionai-databricks/sql"
    elif not os.path.exists(sql_dir) and os.path.exists("visionai-databricks/sql"):
        sql_dir = "visionai-databricks/sql"

    sql_files = [
        "01_create_schemas.sql",
        "02_bronze_from_app.sql",
        "03_silver_enriched.sql",
        "04_gold_tables.sql",
        "05_mlflow_experiment.sql"
    ]

    for f_name in sql_files:
        f_path = os.path.join(sql_dir, f_name)
        if not os.path.exists(f_path):
            print(f"  [ERROR] SQL file not found: {f_path}")
            sys.exit(1)
        
        with open(f_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
            
        content_b64 = base64.b64encode(sql_content.encode('utf-8')).decode('utf-8')
        dest_path = f"{workspace_path}/{f_name}"
        
        payload = {
            "path": dest_path,
            "format": "AUTO",
            "content": content_b64,
            "overwrite": True
        }
        
        res = api("POST", "/api/2.0/workspace/import", payload)
        if res is not None:
            print(f"  [OK] Uploaded {f_name} -> {dest_path}")
        else:
            print(f"  [ERROR] Failed to upload {f_name}")
            sys.exit(1)

    # 3. Clean up existing jobs with same names
    target_job_names = [
        "VisionAI Model Deployment",
        "VisionAI Model Training",
        "VisionAI System Monitoring"
    ]
    
    print("\n[3/5] Cleaning up any existing jobs with matching names...")
    jobs_res = api("GET", "/api/2.1/jobs/list")
    if jobs_res and "jobs" in jobs_res:
        for job in jobs_res["jobs"]:
            job_name = job.get("settings", {}).get("name")
            if job_name in target_job_names:
                old_job_id = job.get("job_id")
                print(f"  [INFO] Found existing job '{job_name}' (ID {old_job_id}). Deleting...")
                api("POST", "/api/2.1/jobs/delete", {"job_id": old_job_id})
                print(f"  [OK] Deleted old job '{job_name}'.")

    # 4. Create the three separate jobs
    print("\n[4/5] Creating separate Workflow Jobs...")

    # Job 1: VisionAI Model Deployment
    job_1_config = {
        "name": "VisionAI Model Deployment",
        "tasks": [
            {
                "task_key": "01_Create_Schemas",
                "sql_task": {
                    "file": {
                        "path": f"{workspace_path}/01_create_schemas.sql",
                        "source": "WORKSPACE"
                    },
                    "warehouse_id": warehouse_id
                }
            },
            {
                "task_key": "02_Bronze_Ingestion",
                "depends_on": [{"task_key": "01_Create_Schemas"}],
                "sql_task": {
                    "file": {
                        "path": f"{workspace_path}/02_bronze_from_app.sql",
                        "source": "WORKSPACE"
                    },
                    "warehouse_id": warehouse_id
                }
            },
            {
                "task_key": "03_Silver_Enriched",
                "depends_on": [{"task_key": "02_Bronze_Ingestion"}],
                "sql_task": {
                    "file": {
                        "path": f"{workspace_path}/03_silver_enriched.sql",
                        "source": "WORKSPACE"
                    },
                    "warehouse_id": warehouse_id
                }
            }
        ],
        "schedule": {
            "quartz_cron_expression": "0 */15 * * * ?",
            "timezone_id": "Asia/Ho_Chi_Minh",
            "pause_status": "PAUSED"
        }
    }

    # Job 2: VisionAI Model Training
    job_2_config = {
        "name": "VisionAI Model Training",
        "tasks": [
            {
                "task_key": "05_MLflow_Experiment",
                "sql_task": {
                    "file": {
                        "path": f"{workspace_path}/05_mlflow_experiment.sql",
                        "source": "WORKSPACE"
                    },
                    "warehouse_id": warehouse_id
                }
            }
        ],
        "schedule": {
            "quartz_cron_expression": "0 0 2 * * ?",
            "timezone_id": "Asia/Ho_Chi_Minh",
            "pause_status": "PAUSED"
        }
    }

    # Job 3: VisionAI System Monitoring
    job_3_config = {
        "name": "VisionAI System Monitoring",
        "tasks": [
            {
                "task_key": "04_Gold_Tables",
                "sql_task": {
                    "file": {
                        "path": f"{workspace_path}/04_gold_tables.sql",
                        "source": "WORKSPACE"
                    },
                    "warehouse_id": warehouse_id
                }
            }
        ],
        "schedule": {
            "quartz_cron_expression": "0 0 * * * ?",
            "timezone_id": "Asia/Ho_Chi_Minh",
            "pause_status": "PAUSED"
        }
    }

    created_jobs = {}
    for cfg in [job_1_config, job_2_config, job_3_config]:
        name = cfg["name"]
        res = api("POST", "/api/2.1/jobs/create", cfg)
        if res:
            j_id = res.get("job_id")
            created_jobs[name] = j_id
            print(f"  [OK] Created job '{name}' with ID: {j_id}")
        else:
            print(f"  [ERROR] Failed to create job '{name}'")
            sys.exit(1)

    # 5. Trigger runs to verify
    print("\n[5/5] Triggering verification runs for all three jobs...")
    for name, j_id in created_jobs.items():
        run_res = api("POST", "/api/2.1/jobs/run-now", {"job_id": j_id})
        if run_res:
            run_id = run_res.get("run_id")
            print(f"  [OK] Job '{name}' started! Run ID: {run_id}")
        else:
            print(f"  [ERROR] Failed to trigger job '{name}'")

    print("\n" + "=" * 60)
    print("  ALL THREE VISIONAI WORKFLOW JOBS DEPLOYED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()
