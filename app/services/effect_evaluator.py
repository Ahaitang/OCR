"""
Treatment Effect Evaluation Service
"""
import numpy as np
from scipy import stats
from typing import List, Dict, Optional

from app.schemas.neuro_schemas import EffectEvaluation


def evaluate_medication_effect(
    patient_id: int,
    patient_name: str,
    before_records: List[Dict],
    after_records: List[Dict],
    medication_name: Optional[str] = None
) -> EffectEvaluation:
    """Evaluate treatment effect based on QMG scores"""

    if not before_records or not after_records:
        return EffectEvaluation(
            patient_id=patient_id,
            patient_name=patient_name,
            medication_name=medication_name,
            before_period={},
            after_period={},
            score_change=0,
            change_percent=0,
            trend_improved=False,
            interpretation="数据不足，无法评估"
        )

    before_scores = [r.get('total_score', 0) for r in before_records]
    after_scores = [r.get('total_score', 0) for r in after_records]

    before_avg = np.mean(before_scores)
    before_median = np.median(before_scores)
    after_avg = np.mean(after_scores)
    after_median = np.median(after_scores)

    # Score change (negative = improvement in QMG context)
    score_change = after_avg - before_avg
    change_percent = (score_change / before_avg * 100) if before_avg > 0 else 0
    improved = score_change < 0  # Score decrease = improvement

    # Statistical significance
    p_value = None
    is_significant = False
    if len(before_scores) >= 3 and len(after_scores) >= 3:
        try:
            t_stat, p_value = stats.ttest_ind(before_scores, after_scores)
            is_significant = p_value < 0.05
        except Exception:
            pass

    # Generate interpretation
    direction = "改善" if improved else "恶化"
    magnitude = abs(change_percent)
    if magnitude < 10:
        effect_desc = "轻微"
    elif magnitude < 30:
        effect_desc = "中等"
    else:
        effect_desc = "显著"

    sig_text = f"(统计学显著，p={round(p_value,3)})" if is_significant else "(统计学不显著)"
    interpretation = f"用药后评分{direction}{abs(round(score_change,2))}分({effect_desc}，{round(abs(change_percent),1)}%)，{sig_text}"

    return EffectEvaluation(
        patient_id=patient_id,
        patient_name=patient_name,
        medication_name=medication_name,
        before_period={
            'start': min(r.get('assessment_date') for r in before_records),
            'end': max(r.get('assessment_date') for r in before_records),
            'avg_score': round(before_avg, 2),
            'median_score': round(before_median, 2),
            'count': len(before_records)
        },
        after_period={
            'start': min(r.get('assessment_date') for r in after_records),
            'end': max(r.get('assessment_date') for r in after_records),
            'avg_score': round(after_avg, 2),
            'median_score': round(after_median, 2),
            'count': len(after_records)
        },
        score_change=round(score_change, 2),
        change_percent=round(change_percent, 2),
        statistical_significance=round(p_value, 4) if p_value else None,
        trend_improved=improved,
        interpretation=interpretation
    )