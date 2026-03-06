"""Seed database with sample users and realistic showroom activity data."""

import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .auth import hash_password
from .database import SessionLocal, init_db
from .models import Sentiment, User, Visitor, Zone, ZoneVisit

ZONE_NAMES = [
    "Entrance",
    "Kitchen Tiles",
    "Living Room Tiles",
    "Bathroom Tiles",
    "Wall Tiles",
    "Large Slabs",
]

EMOTIONS = ["Happy", "Interested", "Neutral", "Confused", "Dissatisfied"]


def seed_users(db: Session) -> None:
    if db.query(User).first():
        return
    users = [
        User(
            name="Admin",
            email="admin@visionsense.com",
            password_hash=hash_password("admin123"),
            role="admin",
        ),
        User(
            name="Manager",
            email="manager@visionsense.com",
            password_hash=hash_password("manager123"),
            role="manager",
        ),
    ]
    for u in users:
        db.add(u)
    db.commit()


def seed_zones(db: Session) -> None:
    if db.query(Zone).first():
        return
    for i, name in enumerate(ZONE_NAMES, start=1):
        db.add(Zone(zone_id=i, zone_name=name))
    db.commit()


def seed_visitors_and_activity(db: Session, count: int = 100) -> None:
    if db.query(Visitor).first():
        return
    zones = db.query(Zone).all()
    zone_ids = [z.zone_id for z in zones]
    now = datetime.now()
    base_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
    base_time = base_time - timedelta(days=7)

    for vid in range(1, count + 1):
        # Mix: ~30% from today, rest from past week
        if random.random() < 0.3:
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            max_offset = max(60, int((now - day_start).total_seconds()) - 60)
            entry_offset = random.randint(0, max_offset)
            entry_time = day_start + timedelta(seconds=entry_offset)
        else:
            entry_offset = random.randint(0, 6 * 24 * 3600)
            entry_time = base_time + timedelta(seconds=entry_offset)
        visit_dur = random.uniform(180, 1200)
        if entry_time.date() == now.date():
            max_dur = (now - entry_time).total_seconds() - 1
            visit_dur = min(visit_dur, max(60, max_dur))
            # ~10% of today's visitors still "in showroom" (exit_time in future)
            if random.random() < 0.1 and visit_dur > 120:
                exit_time = now + timedelta(minutes=30)
            else:
                exit_time = entry_time + timedelta(seconds=visit_dur)
        else:
            exit_time = entry_time + timedelta(seconds=visit_dur)

        visitor = Visitor(
            visitor_id=vid,
            entry_time=entry_time,
            exit_time=exit_time,
            visit_duration=visit_dur,
        )
        db.add(visitor)
        db.flush()

        num_zones = random.randint(2, min(5, len(zones)))
        chosen = random.sample(zone_ids, num_zones)
        elapsed = 0.0
        for zid in chosen:
            dwell = random.uniform(30, min(200, visit_dur - elapsed - 10))
            elapsed += dwell
            entry_ts = entry_time + timedelta(seconds=elapsed - dwell)
            exit_ts = entry_time + timedelta(seconds=elapsed)
            db.add(
                ZoneVisit(
                    visitor_id=vid,
                    zone_id=zid,
                    entry_timestamp=entry_ts,
                    exit_timestamp=exit_ts,
                    dwell_time_seconds=dwell,
                )
            )
            emotion = random.choices(
                EMOTIONS,
                weights=[0.15, 0.35, 0.30, 0.12, 0.08],
            )[0]
            db.add(
                Sentiment(
                    visitor_id=vid,
                    zone_id=zid,
                    emotion=emotion,
                    confidence=round(random.uniform(0.6, 0.98), 2),
                )
            )

    db.commit()


def run_seed() -> None:
    init_db()
    db = SessionLocal()
    try:
        seed_users(db)
        seed_zones(db)
        seed_visitors_and_activity(db)
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
