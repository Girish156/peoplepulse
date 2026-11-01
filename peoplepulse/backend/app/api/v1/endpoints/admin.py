import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from app.core.permissions import require_role

router = APIRouter(prefix="/admin", tags=["Administration & Data Quality"])

# In-memory job tracker for generation/validation runs
JOBS: Dict[str, Dict[str, Any]] = {}

class GenerateDataRequest(BaseModel):
    mode: str = "small"
    seed: int = 20261022

def run_generate_job(job_id: str, mode: str, seed: int):
    JOBS[job_id]["status"] = "running"
    script_path = Path(__file__).resolve().parents[5] / "scripts" / "generate_data.py"
    try:
        proc = subprocess.run(
            [sys.executable, str(script_path), "--mode", mode, "--seed", str(seed)],
            capture_output=True,
            text=True,
            check=True,
        )
        JOBS[job_id]["status"] = "completed"
        JOBS[job_id]["output"] = proc.stdout
    except subprocess.CalledProcessError as e:
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = e.stderr or e.stdout

@router.get("/validation-report")
def get_validation_report(_user=Depends(require_role(["admin", "hr_partner", "it_operations"]))):
    report_path = Path(__file__).resolve().parents[5] / "data" / "reports" / "validation_report.json"
    if not report_path.exists():
        # Trigger validation if not present
        val_script = Path(__file__).resolve().parents[5] / "scripts" / "validate_data.py"
        try:
            subprocess.run([sys.executable, str(val_script)], capture_output=True, text=True, check=True)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate validation report: {str(e)}")

    if report_path.exists():
        with open(report_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Validation report not found")

@router.post("/generate-data")
def trigger_data_generation(
    payload: GenerateDataRequest,
    background_tasks: BackgroundTasks,
    _user=Depends(require_role(["admin"])),
):
    job_id = f"job-{uuid.uuid4().hex[:8]}"
    JOBS[job_id] = {
        "job_id": job_id,
        "mode": payload.mode,
        "seed": payload.seed,
        "status": "queued",
        "output": None,
        "error": None,
    }
    background_tasks.add_task(run_generate_job, job_id, payload.mode, payload.seed)
    return {"job_id": job_id, "status": "queued", "mode": payload.mode}

@router.get("/jobs/{job_id}")
def get_job_status(job_id: str, _user=Depends(require_role(["admin", "hr_partner", "it_operations"]))):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job ID not found")
    return JOBS[job_id]

