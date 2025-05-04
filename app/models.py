from app import db
from flask_login import UserMixin
from app import login_manager
from datetime import datetime
import json

# Lägger till en användare i sessionen
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Skapar en User-klass som representerar en tabell i databasen
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    hashed_password = db.Column(db.String(100), nullable=False)
    chats = db.relationship('Chat', backref='owner', lazy=True)
    company = db.relationship('Company', backref='owner', uselist=False)

# Skapar en Chat-klass som representerar en tabell i databasen
class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    config = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    messages = db.relationship('Message', backref='chat', lazy=True, cascade='all, delete-orphan')

    def set_config(self, config):
        self.config = config

    def get_config(self):
        return self.config or {}

# Skapar en Company-klass som representerar en tabell i databasen
class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_name = db.Column(db.String(100), nullable=True)
    industry = db.Column(db.String(100), nullable=True)
    background = db.Column(db.Text, nullable=True)
    target_audience = db.Column(db.Text, nullable=True)
    brand_voice = db.Column(db.String(100), nullable=True)
    key_values = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Skapar en Message-klass som representerar en tabell i databasen
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_bot = db.Column(db.Boolean, default=False)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)