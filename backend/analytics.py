"""Analytics computations for dashboard and reports."""

from datetime import datetime, timedelta
from typing import Any

import pandas as pd
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .models import Sentiment, Visitor, Zone, ZoneVisit


def get_today_visitors(db: Session) -> int:
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return db.query(Visitor).filter(Visitor.entry_time >= today_start).count()


def get_current_visitors(db: Session) -> int:
    now = datetime.now()
    return (
        db.query(Visitor)
        .filter(
            Visitor.entry_time <= now,
            or_(Visitor.exit_time.is_(None), Visitor.exit_time >= now),
        )
        .count()
    )


def get_avg_visit_duration(db: Session) -> float:
    result = db.query(func.avg(Visitor.visit_duration)).scalar()
    return round(result or 0, 1)


def get_top_section(db: Session) -> str:
    row = (
        db.query(Zone.zone_name, func.sum(ZoneVisit.dwell_time_seconds).label("total"))
        .join(ZoneVisit, ZoneVisit.zone_id == Zone.zone_id)
        .group_by(Zone.zone_id)
        .order_by(func.sum(ZoneVisit.dwell_time_seconds).desc())
        .first()
    )
    return row[0] if row else "N/A"


def get_zone_popularity(db: Session) -> list[dict[str, Any]]:
    rows = (
        db.query(Zone.zone_name, func.count(ZoneVisit.visit_id).label("visits"))
        .join(ZoneVisit, ZoneVisit.zone_id == Zone.zone_id)
        .group_by(Zone.zone_id)
        .order_by(func.count(ZoneVisit.visit_id).desc())
        .all()
    )
    return [{"zone": r[0], "visits": r[1]} for r in rows]


def get_dwell_time_by_zone(db: Session) -> list[dict[str, Any]]:
    rows = (
        db.query(
            Zone.zone_name,
            func.avg(ZoneVisit.dwell_time_seconds).label("avg_dwell"),
        )
        .join(ZoneVisit, ZoneVisit.zone_id == Zone.zone_id)
        .group_by(Zone.zone_id)
        .order_by(func.avg(ZoneVisit.dwell_time_seconds).desc())
        .all()
    )
    return [{"zone": r[0], "avg_dwell_seconds": round(r[1] or 0, 1)} for r in rows]


def get_sentiment_by_zone(db: Session) -> list[dict[str, Any]]:
    rows = (
        db.query(
            Zone.zone_name,
            Sentiment.emotion,
            func.count(Sentiment.id).label("cnt"),
        )
        .join(Sentiment, Sentiment.zone_id == Zone.zone_id)
        .group_by(Zone.zone_id, Sentiment.emotion)
        .all()
    )
    zone_emotions: dict[str, dict[str, int]] = {}
    for zone, emotion, cnt in rows:
        if zone not in zone_emotions:
            zone_emotions[zone] = {}
        zone_emotions[zone][emotion] = cnt
    result = []
    for zone, emotions in zone_emotions.items():
        total = sum(emotions.values())
        result.append(
            {
                "zone": zone,
                "emotions": emotions,
                "total": total,
            }
        )
    return result


def get_insights(db: Session) -> list[str]:
    insights = []
    popularity = get_zone_popularity(db)
    dwell = get_dwell_time_by_zone(db)
    sentiment = get_sentiment_by_zone(db)

    if popularity:
        top = popularity[0]
        insights.append(f"{top['zone']} attracts the highest engagement.")
    if dwell:
        longest = dwell[0]
        insights.append(
            f"{longest['zone']} receives the longest dwell time ({int(longest['avg_dwell_seconds'])}s avg)."
        )
    if popularity and len(popularity) > 1:
        low = popularity[-1]
        insights.append(f"{low['zone']} has the lowest traffic.")
    return insights


def get_visitor_analytics_df(db: Session) -> pd.DataFrame:
    visitors = db.query(Visitor).all()
    data = [
        {
            "visitor_id": v.visitor_id,
            "entry_time": v.entry_time,
            "exit_time": v.exit_time,
            "visit_duration_seconds": v.visit_duration,
        }
        for v in visitors
    ]
    return pd.DataFrame(data)


def get_zone_analytics_df(db: Session) -> pd.DataFrame:
    popularity = get_zone_popularity(db)
    dwell = {d["zone"]: d["avg_dwell_seconds"] for d in get_dwell_time_by_zone(db)}
    return pd.DataFrame(
        [
            {
                "zone": p["zone"],
                "total_visits": p["visits"],
                "avg_dwell_seconds": dwell.get(p["zone"], 0),
            }
            for p in popularity
        ]
    )


def get_sentiment_analytics_df(db: Session) -> pd.DataFrame:
    rows = (
        db.query(Zone.zone_name, Sentiment.emotion, func.avg(Sentiment.confidence))
        .join(Sentiment, Sentiment.zone_id == Zone.zone_id)
        .group_by(Zone.zone_id, Sentiment.emotion)
        .all()
    )
    return pd.DataFrame(
        [{"zone": r[0], "emotion": r[1], "avg_confidence": round(r[2], 2)} for r in rows]
    )
