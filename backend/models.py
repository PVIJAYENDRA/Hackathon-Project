from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="manager")
    created_at = Column(DateTime, default=datetime.utcnow)


class Visitor(Base):
    __tablename__ = "visitors"

    visitor_id = Column(Integer, primary_key=True, index=True)
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime, nullable=True)
    visit_duration = Column(Float, nullable=True)  # seconds

    zone_visits = relationship("ZoneVisit", back_populates="visitor")


class Zone(Base):
    __tablename__ = "zones"

    zone_id = Column(Integer, primary_key=True, index=True)
    zone_name = Column(String, unique=True, nullable=False)

    zone_visits = relationship("ZoneVisit", back_populates="zone")


class ZoneVisit(Base):
    __tablename__ = "zone_visits"

    visit_id = Column(Integer, primary_key=True, index=True)
    visitor_id = Column(Integer, ForeignKey("visitors.visitor_id"), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.zone_id"), nullable=False)
    entry_timestamp = Column(DateTime, nullable=False)
    exit_timestamp = Column(DateTime, nullable=True)
    dwell_time_seconds = Column(Float, nullable=True)

    visitor = relationship("Visitor", back_populates="zone_visits")
    zone = relationship("Zone", back_populates="zone_visits")


class Sentiment(Base):
    __tablename__ = "sentiments"

    id = Column(Integer, primary_key=True, index=True)
    visitor_id = Column(Integer, ForeignKey("visitors.visitor_id"), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.zone_id"), nullable=False)
    emotion = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)

