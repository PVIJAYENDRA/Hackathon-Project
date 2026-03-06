"""FastAPI application wiring backend modules."""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from .auth import decode_token, verify_password
from .database import SessionLocal, get_db, init_db
from .models import User
from .analytics import (
    get_today_visitors,
    get_current_visitors,
    get_avg_visit_duration,
    get_top_section,
    get_zone_popularity,
    get_dwell_time_by_zone,
    get_sentiment_by_zone,
    get_insights,
    get_visitor_analytics_df,
    get_zone_analytics_df,
    get_sentiment_analytics_df,
)

security = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


def create_app():
    from fastapi import FastAPI
    app = FastAPI(title="VisionSense API", version="1.0.0")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/analytics/summary")
    def analytics_summary(db=Depends(get_db), _=Depends(get_current_user)):
        return {
            "total_visitors_today": get_today_visitors(db),
            "current_visitors": get_current_visitors(db),
            "avg_visit_duration": get_avg_visit_duration(db),
            "top_section": get_top_section(db),
        }

    @app.get("/analytics/zones")
    def analytics_zones(db=Depends(get_db), _=Depends(get_current_user)):
        return {
            "popularity": get_zone_popularity(db),
            "dwell_time": get_dwell_time_by_zone(db),
        }

    @app.get("/analytics/sentiment")
    def analytics_sentiment(db=Depends(get_db), _=Depends(get_current_user)):
        return get_sentiment_by_zone(db)

    @app.get("/analytics/insights")
    def analytics_insights(db=Depends(get_db), _=Depends(get_current_user)):
        return {"insights": get_insights(db)}

    return app


app = create_app()
