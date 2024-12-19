from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import CheckConstraint

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)  # Ensure passwords are hashed before storage
    failed_attempts = db.Column(db.Integer, default=0)  # Tracks consecutive failed login attempts
    lockout_until = db.Column(db.DateTime, nullable=True)  # Locks account until this time if needed

    # Add a constraint for valid failed_attempts (non-negative)
    __table_args__ = (
        CheckConstraint(failed_attempts >= 0, name='check_failed_attempts_non_negative'),
    )

class Reference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)  # Ensure input is sanitized before storage
    url = db.Column(db.String(300), nullable=False)  # Validate URL format before saving
    public = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('references', lazy=True))

    # Add a constraint to enforce non-empty titles
    __table_args__ = (
        CheckConstraint('LENGTH(title) > 0', name='check_title_non_empty'),
    )
