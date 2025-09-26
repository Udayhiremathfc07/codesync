from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import datetime
import os

# Base class for models
Base = declarative_base()

# Always create DB inside backend/ folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'codesync.db')}"

# Engine & Session
engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# ---- MODELS ----
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)

    messages = relationship("Message", back_populates="user")

class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    room_code = Column(String(10), unique=True, nullable=False)

    messages = relationship("Message", back_populates="room")
    snapshots = relationship("CodeSnapshot", back_populates="room")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user_id = Column(Integer, ForeignKey("users.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))

    user = relationship("User", back_populates="messages")
    room = relationship("Room", back_populates="messages")

class CodeSnapshot(Base):
    __tablename__ = "code_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(Text, nullable=False)

    room_id = Column(Integer, ForeignKey("rooms.id"))
    room = relationship("Room", back_populates="snapshots")

# ---- INIT DB ----
def init_db():
    Base.metadata.create_all(bind=engine)
