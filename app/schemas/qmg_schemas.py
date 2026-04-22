"""
QMG Analysis Schemas - Pydantic models
"""
from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Optional


class TrendPoint(BaseModel):
    """Single trend data point"""
    assessment_date: date
    total_score: int
    moving_avg: Optional[float] = None
    change_rate: Optional[float] = None


class CategoryTrend(BaseModel):
    """Trend by category"""
    category: str
    category_name: str
    trend_points: List[TrendPoint]


class TrendAnalysisResult(BaseModel):
    """Full trend analysis result"""
    patient_id: int
    patient_name: str
    total_trend: List[TrendPoint]
    category_trends: Optional[List[CategoryTrend]] = None
    trend_direction: str  # improving/stable/worsening
    summary: str
    record_count: int


class AnomalyItem(BaseModel):
    """Single anomaly item"""
    item_key: str
    item_name: str
    current_score: int
    previous_score: Optional[int] = None
    change: Optional[int] = None
    anomaly_type: str  # sudden_change/threshold_breach/dangerous_pattern/ml_detected
    severity: str  # mild/moderate/severe
    confidence: Optional[float] = None


class AnomalyDetectionResult(BaseModel):
    """Anomaly detection result"""
    patient_id: int
    patient_name: str
    has_anomaly: bool
    anomaly_items: List[AnomalyItem]
    overall_risk_level: str  # low/medium/high
    recommendation: Optional[str] = None


class DistributionStats(BaseModel):
    """Severity distribution statistics"""
    mild_count: int
    mild_percent: float
    moderate_count: int
    moderate_percent: float
    severe_count: int
    severe_percent: float
    total_count: int


class CompareResult(BaseModel):
    """Comparison result"""
    group_a: dict
    group_b: dict
    score_diff: float
    percent_diff: float
    p_value: Optional[float] = None
    is_significant: bool
    interpretation: str