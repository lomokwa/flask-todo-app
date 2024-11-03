from datetime import datetime, timezone

from flask import Flask
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, String, DateTime, Integer, Boolean
from sqlalchemy.orm import mapped_column, relationship

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///book.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = mapped_column(Integer, primary_key=True)
    username = mapped_column(String(30), unique=True, nullable=False)
    password_hash = mapped_column(String(255), nullable=False) 

    tasks = relationship("Task", backref="user", lazy=True)

    def __init__(self, username, password_hash):
        self.username = username
        self.password_hash = password_hash

class Task(db.Model):
    __tablename__ = "task"

    id = mapped_column(Integer, primary_key = True)
    name = mapped_column(String(100), nullable=False)
    is_done = mapped_column(Boolean, default=False)
    due_date = mapped_column(DateTime)
    created_at = mapped_column(DateTime, default=datetime.now(timezone.utc))
    user_id = mapped_column(ForeignKey("user.id"))

    def __init__(self, name, due_date, user_id):
        self.name = name
        self.due_date = due_date
        self.user_id = user_id
