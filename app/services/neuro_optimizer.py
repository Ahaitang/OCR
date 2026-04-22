"""
Neuroimmune Optimizer Service - Followup priority and timing prediction
"""
import numpy as np
from datetime import date, timedelta
from typing import List, Dict, Optional
import os
import pickle

from app.schemas.neuro_schemas import (
    PriorityPatient, FollowupPriorityResult,
    OptimalTimePrediction, OverdueFollowup, OverdueCheckResult
)


PRIORITY_WEIGHTS = {
    'days_since_last': 0.30,
    'disease_severity': 0.25,
    'episode_frequency': 0.20,
    'medication_change': 0.15,
    'ml_risk_factor': 0.10,
}


class FollowupOptimizer:
    """Followup optimization algorithms"""

    def __init__(self):
        self.ml_model = None
        self._load_model()

    def _load_model(self):
        model_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "models", "pretrained", "followup_priority.pkl"
        )
        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    self.ml_model = pickle.load(f)
            except Exception:
                pass

    def calculate_base_priority(self, patient_data: Dict) -> float:
        """Calculate rule-based priority score"""
        score = 0

        # Days since last followup
        days = patient_data.get('days_since_last', 0) or 0
        days_score = min(days / 30 * 100, 100) if days > 0 else 0
        score += days_score * PRIORITY_WEIGHTS['days_since_last']

        # Severity level
        severity = patient_data.get('severity_level', 'mild')
        severity_map = {'mild': 20, 'moderate': 50, 'severe': 100}
        severity_score = severity_map.get(severity, 20)
        score += severity_score * PRIORITY_WEIGHTS['disease_severity']

        # Episode frequency
        episodes = patient_data.get('recent_episodes', 0) or 0
        episode_score = min(episodes * 25, 100)
        score += episode_score * PRIORITY_WEIGHTS['episode_frequency']

        # Medication change
        med_changed = patient_data.get('medication_changed_recently', False)
        med_score = 100 if med_changed else 0
        score += med_score * PRIORITY_WEIGHTS['medication_change']

        return round(score, 2)

    def predict_ml_risk(self, patient_data: Dict) -> float:
        """ML-based risk prediction"""
        if self.ml_model is None:
            return 0.3  # Default moderate risk

        features = [
            patient_data.get('age', 50),
            1 if patient_data.get('gender') == 'male' else 0,
            patient_data.get('days_since_last', 30) or 30,
            patient_data.get('recent_episodes', 0) or 0,
            1 if patient_data.get('medication_changed_recently') else 0,
        ]

        try:
            X = np.array(features).reshape(1, -1)
            prob = self.ml_model.predict_proba(X)[0][1]
            return round(prob, 3)
        except Exception:
            return 0.3

    def calculate_final_priority(self, patient_data: Dict) -> Tuple[float, str, List[str]]:
        """Calculate final priority with ML adjustment"""
        base_score = self.calculate_base_priority(patient_data)
        ml_risk = self.predict_ml_risk(patient_data)
        ml_score = ml_risk * 100

        final_score = base_score + ml_score * PRIORITY_WEIGHTS['ml_risk_factor']

        if final_score >= 70:
            level = 'urgent'
        elif final_score >= 50:
            level = 'high'
        elif final_score >= 30:
            level = 'medium'
        else:
            level = 'low'

        reasons = self._generate_reasons(patient_data, base_score, ml_risk)

        return round(final_score, 2), level, reasons

    def _generate_reasons(self, data: Dict, base: float, ml_risk: float) -> List[str]:
        reasons = []

        days = data.get('days_since_last') or 0
        if days >= 21:
            reasons.append(f"距上次随访已{days}天")

        severity = data.get('severity_level')
        if severity == 'severe':
            reasons.append("病情严重度高")

        episodes = data.get('recent_episodes') or 0
        if episodes >= 2:
            reasons.append(f"近90天发作{episodes}次")

        if data.get('medication_changed_recently'):
            reasons.append("近期用药方案有调整")

        if ml_risk >= 0.5:
            reasons.append(f"模型预测风险{round(ml_risk*100)}%")

        return reasons if reasons else ["常规随访"]

    def predict_optimal_time(self, patient_data: Dict, history: List[Dict]) -> OptimalTimePrediction:
        """Predict optimal followup time"""
        patient_id = patient_data['patient_id']
        patient_name = patient_data.get('name', '')

        # Cold start: use severity-based default
        if len(history) < 3:
            severity = patient_data.get('severity_level', 'mild')
            interval_map = {'mild': 90, 'moderate': 45, 'severe': 21}
            interval_days = interval_map.get(severity, 45)

            last_date = patient_data.get('last_followup_date')
            if last_date:
                recommended = last_date + timedelta(days=interval_days)
            else:
                recommended = date.today() + timedelta(days=7)

            return OptimalTimePrediction(
                patient_id=patient_id,
                patient_name=patient_name,
                recommended_date=recommended,
                confidence=0.5,
                basis=f"基于病情严重度({severity})的标准随访周期",
                risk_factors=[]
            )

        # Trend prediction: analyze followup intervals
        intervals = []
        sorted_history = sorted(history, key=lambda x: x.get('date', date.today()))
        for i in range(1, len(sorted_history)):
            d1 = sorted_history[i-1].get('date')
            d2 = sorted_history[i].get('date')
            if d1 and d2:
                intervals.append((d2 - d1).days)

        avg_interval = np.mean(intervals) if intervals else 45

        last_date = patient_data.get('last_followup_date') or date.today()
        recommended = last_date + timedelta(days=int(avg_interval))

        risk_factors = []
        if patient_data.get('recent_episodes', 0) >= 2:
            risk_factors.append("近期发作频繁")
        if patient_data.get('medication_changed_recently'):
            risk_factors.append("用药方案近期调整")

        return OptimalTimePrediction(
            patient_id=patient_id,
            patient_name=patient_name,
            recommended_date=recommended,
            confidence=0.7,
            basis="基于历史随访间隔平均周期",
            risk_factors=risk_factors
        )


def rank_followup_priority(
    pending_followups: List[Dict],
    patient_histories: Dict[int, Dict],
    optimizer: FollowupOptimizer
) -> FollowupPriorityResult:
    """Rank followups by priority"""
    ranked = []

    for f in pending_followups:
        patient_id = f['patient_id']
        history = patient_histories.get(patient_id, {})
        history['patient_id'] = patient_id

        # Calculate days since last
        last_date = history.get('last_followup_date')
        if last_date:
            history['days_since_last'] = (date.today() - last_date).days
        else:
            history['days_since_last'] = 90  # Never followed

        score, level, reasons = optimizer.calculate_final_priority(history)

        # Recommended date
        last = last_date or date.today()
        rec_days = 7 if level == 'urgent' else 14 if level == 'high' else 30
        recommended = last + timedelta(days=rec_days)

        ranked.append(PriorityPatient(
            patient_id=patient_id,
            patient_name=f['patient_name'],
            patient_gender=f.get('patient_gender'),
            days_since_last=history.get('days_since_last'),
            priority_score=score,
            priority_level=level,
            reasons=reasons,
            recommended_date=recommended
        ))

    # Sort by priority score descending
    ranked.sort(key=lambda x: x.priority_score, reverse=True)

    urgent = sum(1 for p in ranked if p.priority_level == 'urgent')
    high = sum(1 for p in ranked if p.priority_level == 'high')

    return FollowupPriorityResult(
        total_pending=len(ranked),
        urgent_count=urgent,
        high_count=high,
        patients=ranked
    )


def check_overdue_followups(overdue_list: List[Dict]) -> OverdueCheckResult:
    """Check overdue and missed followups"""
    overdue_items = []

    for f in overdue_list:
        days = f.get('days_overdue', 0)
        if days >= 30:
            urgency = 'critical'
        elif days >= 14:
            urgency = 'serious'
        else:
            urgency = 'moderate'

        overdue_items.append(OverdueFollowup(
            followup_id=f['id'],
            patient_id=f['patient_id'],
            patient_name=f['patient_name'],
            scheduled_date=f['scheduled_date'],
            days_overdue=days,
            urgency=urgency
        ))

    return OverdueCheckResult(
        overdue_list=overdue_items,
        missed_list=[],  # Would need additional query
        total_overdue=len(overdue_items),
        total_missed=0
    )