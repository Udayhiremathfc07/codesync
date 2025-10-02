# backend/models.py
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import datetime
import os

Base = declarative_base()

# sqlite placed next to repository root (codesync.db)
DATABASE_URL = "sqlite:///codesync.db"

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)

    messages = relationship("Message", back_populates="user")

class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    room_code = Column(String(50), unique=True, nullable=False)

    messages = relationship("Message", back_populates="room")
    snapshots = relationship("CodeSnapshot", back_populates="room", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)

    user = relationship("User", back_populates="messages")
    room = relationship("Room", back_populates="messages")

class CodeSnapshot(Base):
    __tablename__ = "code_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(Text, nullable=False)
    # allow either numeric room_id (FK) or a string room_key (socket room name / room_code)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    room_key = Column(String(100), nullable=True)

    room = relationship("Room", back_populates="snapshots")

def init_db():
    Base.metadata.create_all(bind=engine)