"""Heatmap visualization overlay on showroom layout."""

import streamlit as st
import numpy as np

from backend.database import SessionLocal
from backend.analytics import get_zone_popularity, get_dwell_time_by_zone
from backend.video_processing import ZONE_COORDS


def render() -> None:
    st.header("Heatmap")
    db = SessionLocal()
    try:
        popularity = get_zone_popularity(db)
        dwell = get_dwell_time_by_zone(db)
    finally:
        db.close()

    dwell_map = {d["zone"]: d["avg_dwell_seconds"] for d in dwell}
    pop_map = {p["zone"]: p["visits"] for p in popularity}
    max_dwell = max(dwell_map.values()) or 1
    max_pop = max(pop_map.values()) or 1

    metric = st.radio("Heatmap metric", ["Dwell time", "Visit count"], horizontal=True)
    h, w = 400, 600
    overlay = np.zeros((h, w, 3), dtype=np.uint8)
    base = np.ones((h, w, 3), dtype=np.uint8) * 240

    for zone_name, bbox in ZONE_COORDS.items():
        x1, y1, x2, y2 = [int(v * (w if i % 2 == 0 else h)) for i, v in enumerate(bbox)]
        if metric == "Dwell time":
            val = dwell_map.get(zone_name, 0) / max_dwell
        else:
            val = pop_map.get(zone_name, 0) / max_pop
        r = int(255 * val)
        b = int(255 * (1 - val))
        overlay[y1:y2, x1:x2] = (b, 128, r)

    blended = (base.astype(np.float32) * 0.5 + overlay.astype(np.float32) * 0.5).astype(np.uint8)
    st.image(blended, use_container_width=True)
    st.caption("Red = hot (high engagement), Blue = cold (low engagement)")
