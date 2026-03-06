"""Heatmap visualization overlay on showroom layout."""

import streamlit as st
import cv2
import numpy as np

from backend.database import SessionLocal
from backend.analytics import get_zone_popularity, get_dwell_time_by_zone
from backend.video_processing import ZONE_COORDS, get_sample_video_path


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
        color = (b, 128, r)
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
        cv2.putText(overlay, zone_name[:12], (x1 + 5, y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    blended = cv2.addWeighted(base.astype(np.uint8), 0.5, overlay, 0.5, 0)
    st.image(blended, use_container_width=True)
    st.caption("Red = hot (high engagement), Blue = cold (low engagement)")
