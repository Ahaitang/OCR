"""
QMG Analysis API Router
"""
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional, List

from app.core.database import get_db
from app.services.qmg_data_query import QmgDataQuery
from app.services.qmg_analyzer import analyze_patient_trend, detect_anomalies


router = APIRouter()


@router.get("/trend/{patient_id}")
def get_trend(
    patient_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get patient score trend analysis"""
    query = QmgDataQuery(db)
    patient = query.get_patient_by_id(patient_id)

    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    records = query.get_patient_records(patient_id, start_date, end_date)
    result = analyze_patient_trend(records, patient['name'])

    return {
        "code": 200,
        "message": "success",
        "data": result.model_dump()
    }


@router.get("/anomaly/{patient_id}")
def get_anomaly(
    patient_id: int,
    recent_records: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Detect anomaly in patient scores"""
    query = QmgDataQuery(db)
    patient = query.get_patient_by_id(patient_id)

    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    records = query.get_patient_records(patient_id, limit=recent_records)
    result = detect_anomalies(records, patient['name'], recent_records)

    return {
        "code": 200,
        "message": "success",
        "data": result.model_dump()
    }


@router.post("/batch-anomaly")
def batch_anomaly(
    patient_ids: List[int],
    recent_records: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Batch anomaly detection for multiple patients"""
    query = QmgDataQuery(db)
    results = []

    for pid in patient_ids:
        patient = query.get_patient_by_id(pid)
        if patient:
            records = query.get_patient_records(pid, limit=recent_records)
            result = detect_anomalies(records, patient['name'], recent_records)
            results.append(result.model_dump())

    return {
        "code": 200,
        "message": "success",
        "data": {"results": results, "total": len(results)}
    }


@router.get("/distribution")
def get_distribution(
    doctor_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get severity distribution statistics"""
    query = QmgDataQuery(db)
    stats = query.get_severity_distribution(doctor_id, start_date, end_date)

    return {
        "code": 200,
        "message": "success",
        "data": stats
    }


@router.post("/compare")
def compare_data(
    params: dict,
    db: Session = Depends(get_db)
):
    """Compare two groups of data"""
    from scipy import stats as scipy_stats
    import numpy as np

    query = QmgDataQuery(db)

    group_a_ids = params.get('group_a_patient_ids', [])
    group_b_ids = params.get('group_b_patient_ids', [])

    scores_a = []
    for pid in group_a_ids:
        records = query.get_patient_records(pid, limit=1)
        if records:
            scores_a.append(records[-1]['total_score'])

    scores_b = []
    for pid in group_b_ids:
        records = query.get_patient_records(pid, limit=1)
        if records:
            scores_b.append(records[-1]['total_score'])

    if not scores_a or not scores_b:
        return {
            "code": 400,
            "message": "数据不足",
            "data": None
        }

    avg_a = np.mean(scores_a)
    avg_b = np.mean(scores_b)
    diff = avg_b - avg_a
    percent_diff = (diff / avg_a * 100) if avg_a > 0 else 0

    p_value = None
    is_significant = False
    if len(scores_a) >= 3 and len(scores_b) >= 3:
        t_stat, p_value = scipy_stats.ttest_ind(scores_a, scores_b)
        is_significant = p_value < 0.05

    direction = "B组较高" if diff > 0 else "A组较高"
    significance_text = "(统计学显著)" if is_significant else "(统计学不显著)"

    interpretation = f"{direction}，平均分差异{abs(round(diff, 2))}分({significance_text})"

    return {
        "code": 200,
        "message": "success",
        "data": {
            "group_a": {"avg_score": round(avg_a, 2), "count": len(scores_a)},
            "group_b": {"avg_score": round(avg_b, 2), "count": len(scores_b)},
            "score_diff": round(diff, 2),
            "percent_diff": round(percent_diff, 2),
            "p_value": round(p_value, 4) if p_value else None,
            "is_significant": is_significant,
            "interpretation": interpretation
        }
    }