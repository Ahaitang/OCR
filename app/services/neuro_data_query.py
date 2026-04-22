"""
Neuroimmune Data Query Service
"""
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import List, Optional, Dict, Tuple
import json


class NeuroDataQuery:
    def __init__(self, db: Session):
        self.db = db

    def get_pending_followups(self, doctor_id: Optional[int] = None) -> List[Dict]:
        """Get pending followup patients"""
        sql = """
            SELECT
                f.id as followup_id,
                f.patient_id,
                p.name as patient_name,
                p.gender as patient_gender,
                f.date as scheduled_date,
                f.status,
                f.doctor_id,
                f.project,
                f.type
            FROM follow_up f
            JOIN patient p ON f.patient_id = p.id
            WHERE f.status = 'pending'
        """
        params = {}

        if doctor_id:
            sql += " AND f.doctor_id = :doctor_id"
            params['doctor_id'] = doctor_id

        sql += " ORDER BY f.date ASC"

        result = self.db.execute(text(sql), params)
        return [self._row_to_dict(row) for row in result.fetchall()]

    def get_overdue_followups(self, doctor_id: Optional[int] = None) -> List[Dict]:
        """Get overdue followups"""
        sql = """
            SELECT
                f.id, f.patient_id, p.name as patient_name,
                f.date as scheduled_date,
                DATEDIFF(CURDATE(), f.date) as days_overdue,
                f.status
            FROM follow_up f
            JOIN patient p ON f.patient_id = p.id
            WHERE f.status = 'pending'
            AND f.date < CURDATE()
        """
        params = {}

        if doctor_id:
            sql += " AND f.doctor_id = :doctor_id"
            params['doctor_id'] = doctor_id

        sql += " ORDER BY days_overdue DESC"

        result = self.db.execute(text(sql), params)
        return [self._row_to_dict(row) for row in result.fetchall()]

    def get_patient_history(self, patient_id: int) -> Dict:
        """Get patient comprehensive history"""
        history = {'patient_id': patient_id}

        # Recent episodes (90 days)
        episodes_sql = """
            SELECT COUNT(*) as episode_count
            FROM disease_episode
            WHERE patient_id = :patient_id
            AND onset_date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
        """
        result = self.db.execute(text(episodes_sql), {'patient_id': patient_id})
        row = result.fetchone()
        history['recent_episodes'] = row[0] if row else 0

        # Recent medication changes (30 days)
        med_sql = """
            SELECT COUNT(*) as change_count
            FROM medication
            WHERE patient_id = :patient_id
            AND create_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """
        result = self.db.execute(text(med_sql), {'patient_id': patient_id})
        row = result.fetchone()
        history['medication_changed_recently'] = (row[0] if row else 0) > 0

        # Last followup date
        last_sql = """
            SELECT MAX(date) as last_date
            FROM follow_up
            WHERE patient_id = :patient_id
            AND status = 'completed'
        """
        result = self.db.execute(text(last_sql), {'patient_id': patient_id})
        row = result.fetchone()
        history['last_followup_date'] = row[0] if row else None

        # Patient info
        patient_sql = """
            SELECT name, gender, age FROM patient WHERE id = :patient_id
        """
        result = self.db.execute(text(patient_sql), {'patient_id': patient_id})
        row = result.fetchone()
        if row:
            history['name'] = row[0]
            history['gender'] = row[1]
            history['age'] = row[2]

        return history

    def get_patient_followup_records(self, patient_id: int) -> List[Dict]:
        """Get patient followup history for trend analysis"""
        sql = """
            SELECT id, date, status, content, type, project
            FROM follow_up
            WHERE patient_id = :patient_id
            ORDER BY date DESC
            LIMIT 20
        """
        result = self.db.execute(text(sql), {'patient_id': patient_id})
        return [self._row_to_dict(row) for row in result.fetchall()]

    def get_patient_by_id(self, patient_id: int) -> Optional[Dict]:
        """Get patient info"""
        sql = "SELECT id, name, gender, age FROM patient WHERE id = :patient_id"
        result = self.db.execute(text(sql), {'patient_id': patient_id})
        row = result.fetchone()
        if row:
            return {'id': row[0], 'name': row[1], 'gender': row[2], 'age': row[3]}
        return None

    def _row_to_dict(self, row) -> Dict:
        if hasattr(row, '_mapping'):
            return dict(row._mapping)
        return dict(row)