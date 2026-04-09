import json
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.report import Report

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/report/{job_id}")
def get_report(job_id: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.job_id == job_id).first()

    if not report:
        raise HTTPException(status_code=404, detail="Relatório não encontrado. O processamento pode ainda estar em andamento.")

    try:
        components = json.loads(report.components) if report.components else []
        risks = json.loads(report.risks) if report.risks else []
        recommendations = json.loads(report.recommendations) if report.recommendations else []
    except json.JSONDecodeError:
        components, risks, recommendations = [], [], []

    return {
        "job_id": job_id,
        "report": {
            "components": components,
            "risks": risks,
            "recommendations": recommendations
        },
        "created_at": report.created_at
    }