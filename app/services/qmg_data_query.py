"""
QMG Data Query Service
"""
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional, Dict, Any
import json


ITEM_KEYS = [
    'diplopia', 'ptosis', 'eyelidClosure',
    'swallowing', 'counting', 'vitalCapacity',
    'armRaiseRight', 'armRaiseLeft',
    'gripStrengthRight', 'gripStrengthLeft',
    'headLift', 'legRaiseRight', 'legRaiseLeft'
]

ITEM_NAMES = {
    'diplopia': '左右侧视复视',
    'ptosis': '上视眼睑下垂',
    'eyelidClosure': '眼睑闭合',
    'swallowing': '吞咽100mL水',
    'counting': '数数构音障碍',
    'vitalCapacity': '肺活量预计值',
    'armRaiseRight': '右上肢抬起',
    'armRaiseLeft': '左上肢抬起',
    'gripStrengthRight': '右手握力',
    'gripStrengthLeft': '左手握力',
    'headLift': '抬头',
    'legRaiseRight': '右下肢抬起',
    'legRaiseLeft': '左下肢抬起'
}


class QmgDataQuery:
    def __init__(self, db: Session):
        self.db = db

    def get_patient_records(
        self,
        patient_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Get patient questionnaire records"""
        sql = """
            SELECT
                qr.id, qr.patient_id, qr.assessment_date,
                qr.total_score, qr.selections, qr.item_scores,
                qr.category_scores, qr.doctor_id, qr.doctor_username,
                p.name as patient_name, p.gender as patient_gender
            FROM questionnaire_record qr
            JOIN patient p ON qr.patient_id = p.id
            WHERE qr.patient_id = :patient_id
        """
        params = {'patient_id': patient_id}

        if start_date:
            sql += " AND qr.assessment_date >= :start_date"
            params['start_date'] = start_date
        if end_date:
            sql += " AND qr.assessment_date <= :end_date"
            params['end_date'] = end_date

        sql += " ORDER BY qr.assessment_date ASC"

        if limit:
            sql += f" LIMIT {limit}"

        result = self.db.execute(text(sql), params)
        return [self._parse_row(row) for row in result.fetchall()]

    def get_severity_distribution(
        self,
        doctor_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """Get severity distribution statistics"""
        sql = """
            SELECT
                CASE
                    WHEN total_score <= 9 THEN 'mild'
                    WHEN total_score <= 18 THEN 'moderate'
                    ELSE 'severe'
                END as severity,
                COUNT(*) as count
            FROM questionnaire_record qr
            WHERE 1=1
        """
        params = {}

        if doctor_id:
            sql += " AND qr.patient_id IN (SELECT patient_id FROM patient_doctor WHERE doctor_id = :doctor_id)"
            params['doctor_id'] = doctor_id
        if start_date:
            sql += " AND qr.assessment_date >= :start_date"
            params['start_date'] = start_date
        if end_date:
            sql += " AND qr.assessment_date <= :end_date"
            params['end_date'] = end_date

        sql += " GROUP BY severity"

        result = self.db.execute(text(sql), params)
        rows = result.fetchall()

        distribution = {'mild': 0, 'moderate': 0, 'severe': 0}
        for row in rows:
            distribution[row[0]] = row[1]

        total = sum(distribution.values())
        if total > 0:
            return {
                'mild_count': distribution['mild'],
                'mild_percent': round(distribution['mild'] / total * 100, 2),
                'moderate_count': distribution['moderate'],
                'moderate_percent': round(distribution['moderate'] / total * 100, 2),
                'severe_count': distribution['severe'],
                'severe_percent': round(distribution['severe'] / total * 100, 2),
                'total_count': total
            }
        return distribution

    def get_all_records_for_training(self, min_records: int = 3) -> List[Dict]:
        """Get all records for model training"""
        sql = """
            SELECT qr.* FROM questionnaire_record qr
            WHERE qr.patient_id IN (
                SELECT patient_id FROM questionnaire_record
                GROUP BY patient_id HAVING COUNT(*) >= :min_count
            )
            ORDER BY patient_id, assessment_date
        """
        result = self.db.execute(text(sql), {'min_count': min_records})
        return [self._parse_row(row) for row in result.fetchall()]

    def get_doctor_patients(self, doctor_id: int) -> List[int]:
        """Get patient IDs for a doctor"""
        sql = "SELECT patient_id FROM patient_doctor WHERE doctor_id = :doctor_id"
        result = self.db.execute(text(sql), {'doctor_id': doctor_id})
        return [row[0] for row in result.fetchall()]

    def get_patient_by_id(self, patient_id: int) -> Optional[Dict]:
        """Get patient info"""
        sql = "SELECT id, name, gender, admission_number FROM patient WHERE id = :patient_id"
        result = self.db.execute(text(sql), {'patient_id': patient_id})
        row = result.fetchone()
        if row:
            return {'id': row[0], 'name': row[1], 'gender': row[2], 'admission_number': row[3]}
        return None

    def _parse_row(self, row) -> Dict:
        """Parse database row to dict"""
        data = dict(row._mapping) if hasattr(row, '_mapping') else dict(row)

        # Parse JSON fields
        if data.get('item_scores') and isinstance(data['item_scores'], str):
            try:
                data['item_scores'] = json.loads(data['item_scores'])
            except:
                data['item_scores'] = {}
        if data.get('category_scores') and isinstance(data['category_scores'], str):
            try:
                data['category_scores'] = json.loads(data['category_scores'])
            except:
                data['category_scores'] = {}
        if data.get('selections') and isinstance(data['selections'], str):
            try:
                data['selections'] = json.loads(data['selections'])
            except:
                data['selections'] = {}

        return data