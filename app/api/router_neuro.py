"""
Neuroimmune Optimization API Router
"""
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

from app.core.database import get_db
from app.services.neuro_data_query import NeuroDataQuery
from app.services.neuro_optimizer import (
    FollowupOptimizer, rank_followup_priority,
    check_overdue_followups, predict_optimal_time
)
from app.schemas.neuro_schemas import (
    FollowupPriorityResult, OptimalTimePrediction, OverdueCheckResult
)


router = APIRouter()


@router.get("/followup-priority")
def get_followup_priority(
    doctor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get intelligent followup priority list"""
    query = NeuroDataQuery(db)
    optimizer = FollowupOptimizer()

    pending = query.get_pending_followups(doctor_id)

    # Get histories for all patients
    histories = {}
    for f in pending:
        pid = f['patient_id']
        histories[pid] = query.get_patient_history(pid)

    result = rank_followup_priority(pending, histories, optimizer)

    return {
        "code": 200,
        "message": "success",
        "data": result.model_dump()
    }


@router.get("/optimal-time/{patient_id}")
def get_optimal_time(
    patient_id: int,
    db: Session = Depends(get_db)
):
    """Predict optimal followup time"""
    query = NeuroDataQuery(db)
    optimizer = FollowupOptimizer()

    patient = query.get_patient_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    history = query.get_patient_history(patient_id)
    history['name'] = patient['name']
    history['patient_id'] = patient_id

    records = query.get_patient_followup_records(patient_id)
    result = optimizer.predict_optimal_time(history, records)

    return {
        "code": 200,
        "message": "success",
        "data": result.model_dump()
    }


@router.get("/overdue-check")
def get_overdue_check(
    doctor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Check overdue and missed followups"""
    query = NeuroDataQuery(db)
    overdue = query.get_overdue_followups(doctor_id)
    result = check_overdue_followups(overdue)

    return {
        "code": 200,
        "message": "success",
        "data": result.model_dump()
    }


@router.get("/effect-evaluate/{patient_id}")
def evaluate_effect(
    patient_id: int,
    medication_name: Optional[str] = Query(None),
    before_start: Optional[date] = Query(None),
    before_end: Optional[date] = Query(None),
    after_start: Optional[date] = Query(None),
    after_end: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Evaluate treatment effect"""
    from app.services.effect_evaluator import evaluate_medication_effect
    from app.services.qmg_data_query import QmgDataQuery

    neuro_query = NeuroDataQuery(db)
    qmg_query = QmgDataQuery(db)

    patient = neuro_query.get_patient_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    # Get QMG records for this patient
    before_records = qmg_query.get_patient_records(patient_id, before_start, before_end)
    after_records = qmg_query.get_patient_records(patient_id, after_start, after_end)

    result = evaluate_medication_effect(
        patient_id, patient['name'],
        before_records, after_records,
        medication_name
    )

    return {
        "code": 200,
        "message": "success",
        "data": result.model_dump()
    }