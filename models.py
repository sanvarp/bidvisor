from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ExtractionSession(db.Model):
    id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.String, nullable=False)
    assistant_id = db.Column(db.String, nullable=False)
    vector_store_id = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    files = db.relationship('UploadedFile', backref='session', lazy=True, cascade="all, delete-orphan")
    chat_messages = db.relationship('ChatMessage', backref='session', lazy=True, cascade="all, delete-orphan")
    extracted_info = db.relationship('ExtractedInfo', backref='session', lazy=True, cascade="all, delete-orphan")

class UploadedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String, db.ForeignKey('extraction_session.id'), nullable=False)
    filename = db.Column(db.String, nullable=False)
    filepath = db.Column(db.String, nullable=False)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String, db.ForeignKey('extraction_session.id'), nullable=False)
    role = db.Column(db.String, nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class ExtractedInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String, db.ForeignKey('extraction_session.id'), nullable=False)
    section = db.Column(db.String, nullable=False)
    field = db.Column(db.String, nullable=True)
    value = db.Column(db.Text, nullable=False)