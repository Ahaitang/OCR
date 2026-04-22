"""
QMG Analyzer Service - Trend analysis and anomaly detection
"""
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import date
import os
import pickle

from app.schemas.qmg_schemas import (
    TrendPoint, CategoryTrend, TrendAnalysisResult,
    AnomalyItem, AnomalyDetectionResult
)
from app.services.qmg_data_query import ITEM_KEYS, ITEM_NAMES


# Anomaly detection rules
ANOMALY_RULES = {
    'sudden_change_threshold': {
        'single_item': 2,  # Single item change >= 2 is sudden
        'total_score': 5,  # Total score change >= 5 is significant
    },
    'critical_threshold': {
        'vitalCapacity': {'warn': 2, 'critical': 3},
        'swallowing': {'warn': 2, 'critical': 3},
    },
    'dangerous_patterns': [
        ['vitalCapacity', 'swallowing'],
        ['ptosis', 'diplopia', 'eyelidClosure'],
    ]
}


class TrendAnalyzer:
    """Trend analysis algorithms"""

    @staticmethod
    def calculate_moving_average(records: List[Dict], window: int = 3) -> List[float]:
        """Calculate moving average"""
        scores = [r['total_score'] for r in records]
        moving_avg = []
        for i in range(len(scores)):
            start = max(0, i - window + 1)
            avg = sum(scores[start:i+1]) / (i - start + 1)
            moving_avg.append(round(avg, 2))
        return moving_avg

    @staticmethod
    def calculate_change_rate(records: List[Dict]) -> List[Optional[float]]:
        """Calculate change rate from previous"""
        rates = [None]
        for i in range(1, len(records)):
            prev = records[i-1]['total_score']
            curr = records[i]['total_score']
            if prev > 0:
                rate = ((curr - prev) / prev) * 100
            else:
                rate = curr * 100 if curr > 0 else 0
            rates.append(round(rate, 2))
        return rates

    @staticmethod
    def determine_trend_direction(records: List[Dict]) -> str:
        """Determine overall trend direction"""
        if len(records) < 2:
            return "stable"

        n = len(records)
        recent = min(3, n)
        recent_avg = sum(r['total_score'] for r in records[-recent:]) / recent
        earlier_avg = sum(r['total_score'] for r in records[:-recent]) / max(1, n - recent)

        diff = recent_avg - earlier_avg
        if diff <= -2:
            return "improving"
        elif diff >= 2:
            return "worsening"
        return "stable"

    @staticmethod
    def generate_summary(direction: str, records: List[Dict]) -> str:
        """Generate Chinese summary"""
        if len(records) < 2:
            return "数据不足，无法判断趋势"

        first_score = records[0]['total_score']
        last_score = records[-1]['total_score']
        change = last_score - first_score

        if direction == "improving":
            return f"评分趋势改善，从{first_score}分降至{last_score}分（改善{abs(change)}分）"
        elif direction == "worsening":
            return f"评分趋势恶化，从{first_score}分升至{last_score}分（恶化{abs(change)}分）"
        return f"评分趋势稳定，当前{last_score}分"


class AnomalyDetector:
    """Anomaly detection algorithms"""

    # 单例实例
    _instance = None
    _model_loaded = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_model()
            cls._model_loaded = True
        return cls._instance

    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_model(self):
        """Load pretrained model"""
        if self._model_loaded:
            return  # 已加载，避免重复
        model_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "models", "pretrained", "anomaly_detector.pkl"
        )
        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
                self._model_loaded = True
            except Exception as e:
                # 使用logger而非print
                from app.core.logger import logger
                logger.warning(f"Failed to load anomaly model: {e}")

    @staticmethod
    def detect_rule_anomalies(
        current: Dict,
        previous: Optional[Dict]
    ) -> List[Dict]:
        """Rule-based anomaly detection"""
        anomalies = []
        item_scores = current.get('item_scores', {})

        # 1. Sudden change detection
        if previous:
            prev_scores = previous.get('item_scores', {})
            for key in ITEM_KEYS:
                curr = item_scores.get(key, 0)
                prev = prev_scores.get(key, 0)
                change = curr - prev
                if change >= ANOMALY_RULES['sudden_change_threshold']['single_item']:
                    anomalies.append({
                        'item_key': key,
                        'item_name': ITEM_NAMES.get(key, key),
                        'current_score': curr,
                        'previous_score': prev,
                        'change': change,
                        'anomaly_type': 'sudden_change',
                        'severity': 'severe' if change >= 3 else 'moderate',
                        'confidence': 0.9
                    })

            # Total score sudden change
            total_change = current['total_score'] - previous['total_score']
            if total_change >= ANOMALY_RULES['sudden_change_threshold']['total_score']:
                anomalies.append({
                    'item_key': 'total',
                    'item_name': '总分',
                    'current_score': current['total_score'],
                    'previous_score': previous['total_score'],
                    'change': total_change,
                    'anomaly_type': 'sudden_change',
                    'severity': 'severe',
                    'confidence': 0.95
                })

        # 2. Critical threshold warning
        for key, thresholds in ANOMALY_RULES['critical_threshold'].items():
            score = item_scores.get(key, 0)
            if score >= thresholds['critical']:
                anomalies.append({
                    'item_key': key,
                    'item_name': ITEM_NAMES.get(key, key),
                    'current_score': score,
                    'anomaly_type': 'threshold_breach',
                    'severity': 'severe',
                    'confidence': 0.85
                })
            elif score >= thresholds['warn']:
                anomalies.append({
                    'item_key': key,
                    'item_name': ITEM_NAMES.get(key, key),
                    'current_score': score,
                    'anomaly_type': 'threshold_breach',
                    'severity': 'moderate',
                    'confidence': 0.7
                })

        # 3. Dangerous pattern detection
        for pattern in ANOMALY_RULES['dangerous_patterns']:
            if all(item_scores.get(k, 0) >= 2 for k in pattern):
                anomalies.append({
                    'item_key': 'pattern',
                    'item_name': ', '.join([ITEM_NAMES.get(k, k) for k in pattern]),
                    'current_score': sum(item_scores.get(k, 0) for k in pattern),
                    'anomaly_type': 'dangerous_pattern',
                    'severity': 'severe',
                    'confidence': 0.8
                })

        return anomalies

    def detect_ml_anomalies(self, records: List[Dict]) -> List[Dict]:
        """ML-based anomaly detection"""
        if self.model is None or len(records) < 5:
            return []

        features = []
        for r in records:
            item_scores = r.get('item_scores', {})
            vec = [item_scores.get(k, 0) for k in ITEM_KEYS] + [r.get('total_score', 0)]
            features.append(vec)

        X = np.array(features)
        predictions = self.model.predict(X)
        scores = self.model.score_samples(X)

        anomalies = []
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            if pred == -1:
                anomalies.append({
                    'record_index': i,
                    'assessment_date': records[i]['assessment_date'],
                    'anomaly_type': 'ml_detected',
                    'severity': 'moderate',
                    'confidence': min(0.95, max(0.5, -score / 10))
                })

        return anomalies


def analyze_patient_trend(
    records: List[Dict],
    patient_name: str
) -> TrendAnalysisResult:
    """Full trend analysis for a patient"""
    if not records:
        return TrendAnalysisResult(
            patient_id=0,
            patient_name=patient_name,
            total_trend=[],
            trend_direction="stable",
            summary="无评分记录",
            record_count=0
        )

    patient_id = records[0]['patient_id']
    moving_avg = TrendAnalyzer.calculate_moving_average(records)
    change_rates = TrendAnalyzer.calculate_change_rate(records)
    direction = TrendAnalyzer.determine_trend_direction(records)
    summary = TrendAnalyzer.generate_summary(direction, records)

    total_trend = [
        TrendPoint(
            assessment_date=r['assessment_date'],
            total_score=r['total_score'],
            moving_avg=moving_avg[i],
            change_rate=change_rates[i]
        )
        for i, r in enumerate(records)
    ]

    return TrendAnalysisResult(
        patient_id=patient_id,
        patient_name=patient_name,
        total_trend=total_trend,
        trend_direction=direction,
        summary=summary,
        record_count=len(records)
    )


def detect_anomalies(
    records: List[Dict],
    patient_name: str,
    recent_n: int = 5
) -> AnomalyDetectionResult:
    """Full anomaly detection"""
    if not records:
        return AnomalyDetectionResult(
            patient_id=0,
            patient_name=patient_name,
            has_anomaly=False,
            anomaly_items=[],
            overall_risk_level="low"
        )

    patient_id = records[0]['patient_id']
    # 使用单例实例，避免重复加载模型
    detector = AnomalyDetector.get_instance()

    # Use recent records
    recent = records[-recent_n:] if len(records) >= recent_n else records

    # Rule-based detection
    rule_anomalies = []
    for i in range(len(recent)):
        current = recent[i]
        previous = recent[i-1] if i > 0 else None
        rule_anomalies.extend(detector.detect_rule_anomalies(current, previous))

    # ML detection
    ml_anomalies = detector.detect_ml_anomalies(recent)

    # Combine and deduplicate
    all_anomalies = []
    seen = set()
    for a in rule_anomalies:
        key = (a['item_key'], a['anomaly_type'])
        if key not in seen:
            seen.add(key)
            all_anomalies.append(AnomalyItem(**a))

    # Calculate risk level
    severe_count = sum(1 for a in all_anomalies if a.severity == 'severe')
    if severe_count >= 2:
        risk_level = "high"
    elif severe_count >= 1 or len(all_anomalies) >= 3:
        risk_level = "medium"
    else:
        risk_level = "low"

    recommendation = None
    if risk_level == "high":
        recommendation = "建议立即安排复查，重点关注异常指标"
    elif risk_level == "medium":
        recommendation = "建议近期安排随访，观察异常指标变化"

    return AnomalyDetectionResult(
        patient_id=patient_id,
        patient_name=patient_name,
        has_anomaly=len(all_anomalies) > 0,
        anomaly_items=all_anomalies,
        overall_risk_level=risk_level,
        recommendation=recommendation
    )