from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db
import time
import random


def _generate_id():
    """Generate unique ID using timestamp + random.
    Databricks IDENTITY columns don't return auto-generated IDs to SQLAlchemy,
    so we generate IDs in the application layer instead."""
    return int(time.time() * 1000) + random.randint(0, 999)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.BigInteger, primary_key=True, default=_generate_id)
    email = db.Column(db.String, unique=True, nullable=False)
    username = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    role = db.Column(db.String, default='user')  # 'admin', 'user'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_login = db.Column(db.DateTime)
    birth_date = db.Column(db.Date)
    location = db.Column(db.String)
    
    # Relationship with detections
    detections = db.relationship('Detection', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
