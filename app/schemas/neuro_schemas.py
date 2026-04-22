"""
Neuroimmune Optimization Schemas
"""
from pydantic import BaseModel
from datetime import date
from typing import List, Optional


class PriorityPatient(BaseModel):
    """Patient with priority score"""
    patient_id: int
    patient_name: str
    patient_gender: Optional[str] = None
    patient_age: Optional[int] = None
    last_followup_date: Optional[date] = None
    days_since_last: Optional[int] = None
    priority_score: float
    priority_level: str  # urgent/high/medium/low
    reasons: List[str]
    recommended_date: Optional[date] = None


class FollowupPriorityResult(BaseModel):
    """Followup priority ranking result"""
    doctor_id: Optional[int] = None
    total_pending: int
    urgent_count: int
    high_count: int
    patients: List[PriorityPatient]


class OptimalTimePrediction(BaseModel):
    """Optimal followup time prediction"""
    patient_id: int
    patient_name: str
    recommended_date: date
    confidence: float
    basis: str
    risk_factors: List[str] = []


class OverdueFollowup(BaseModel):
    """Overdue followup item"""
    followup_id: int
    patient_id: int
    patient_name: str
    scheduled_date: date
    days_overdue: int
    urgency: str  # critical/serious/moderate


class OverdueCheckResult(BaseModel):
    """Overdue check result"""
    overdue_list: List[OverdueFollowup]
    missed_list: List[dict]
    total_overdue: int
    total_missed: int


class EffectEvaluation(BaseModel):
    """Treatment effect evaluation"""
    patient_id: int
    patient_name: str
    medication_name: Optional[str] = None
    before_period: dict
    after_period: dict
    score_change: float
    change_percent: float
    statistical_significance: Optional[float] = None
    trend_improved: bool
    interpretation: str