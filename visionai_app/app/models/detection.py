from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import time
import random
from app import db


def _generate_id():
    """Generate unique ID using timestamp + random.
    Databricks IDENTITY columns don't return auto-generated IDs to SQLAlchemy,
    so we generate IDs in the application layer instead."""
    return int(time.time() * 1000) + random.randint(0, 999)


class Detection(db.Model):
    __tablename__ = 'detections'
    
    id = db.Column(db.BigInteger, primary_key=True, default=_generate_id)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    image_path = db.Column(db.String, nullable=False)
    detection_type = db.Column(db.String, nullable=False)  # 'camera', 'upload'
    objects_detected = db.Column(db.Text, nullable=False)  # JSON string
    confidence_scores = db.Column(db.Text)  # JSON string
    timestamp = db.Column(db.DateTime, default=datetime.now)
    processing_time = db.Column(db.Float)  # in seconds
    
    def set_objects_detected(self, objects):
        self.objects_detected = json.dumps(objects)
    
    def get_objects_detected(self):
        return json.loads(self.objects_detected) if self.objects_detected else []
    
    def set_confidence_scores(self, scores):
        self.confidence_scores = json.dumps(scores)
    
    def get_confidence_scores(self):
        return json.loads(self.confidence_scores) if self.confidence_scores else []
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'image_path': self.image_path,
            'detection_type': self.detection_type,
            'objects_detected': self.get_objects_detected(),
            'confidence_scores': self.get_confidence_scores(),
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'processing_time': self.processing_time
        }
