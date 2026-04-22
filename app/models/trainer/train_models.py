"""
Model Training Scripts
"""
import os
import pickle
from datetime import datetime
from typing import List, Dict
import numpy as np

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.linear_model import LogisticRegression
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

from app.services.qmg_data_query import ITEM_KEYS


MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'pretrained')


def train_anomaly_detector(records: List[Dict], contamination: float = 0.08):
    """Train anomaly detection model"""
    if not ML_AVAILABLE or len(records) < 50:
        return None

    features = []
    for r in records:
        item_scores = r.get('item_scores', {})
        if isinstance(item_scores, str):
            import json
            try:
                item_scores = json.loads(item_scores)
            except:
                item_scores = {}

        vec = [item_scores.get(k, 0) for k in ITEM_KEYS] + [r.get('total_score', 0)]
        features.append(vec)

    X = np.array(features)

    model = IsolationForest(
        contamination=contamination,
        n_estimators=100,
        random_state=42
    )
    model.fit(X)

    return model


def train_priority_model(features: List[Dict], labels: List[int]):
    """Train followup priority prediction model"""
    if not ML_AVAILABLE or len(features) < 30:
        return None

    vectors = []
    for f in features:
        vec = [
            f.get('age', 50),
            1 if f.get('gender') == 'male' else 0,
            f.get('days_since_last', 30) or 30,
            f.get('recent_episodes', 0) or 0,
            1 if f.get('medication_changed') else 0,
        ]
        vectors.append(vec)

    X = np.array(vectors)
    y = np.array(labels)

    model = LogisticRegression(max_iter=1000, class_weight='balanced')
    model.fit(X, y)

    return model


def save_model(model, filename: str):
    """Save model to file"""
    os.makedirs(MODEL_DIR, exist_ok=True)
    filepath = os.path.join(MODEL_DIR, filename)
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)

    # Save version info
    version_file = os.path.join(MODEL_DIR, 'version.txt')
    with open(version_file, 'w') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"{filename}\n")


def train_all_models(db=None):
    """Train all models (called by scheduler or API)"""
    print(f"[{datetime.now()}] Starting model training...")

    results = {'qmg_anomaly': False, 'followup_priority': False}

    # Train QMG anomaly detector
    if db:
        from app.services.qmg_data_query import QmgDataQuery
        qmg_query = QmgDataQuery(db)
        records = qmg_query.get_all_records_for_training(min_records=3)

        if len(records) >= 50:
            model = train_anomaly_detector(records)
            if model:
                save_model(model, 'anomaly_detector.pkl')
                results['qmg_anomaly'] = True
                print(f"  ✓ Anomaly detector trained with {len(records)} records")
        else:
            print(f"  ⚠ Only {len(records)} records, skipping anomaly training")

    print(f"[{datetime.now()}] Training complete: {results}")
    return results


if __name__ == '__main__':
    train_all_models()