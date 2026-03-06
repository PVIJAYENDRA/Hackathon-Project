"""Visitor analytics: dwell time, zone popularity, movement."""

import streamlit as st
import pandas as pd
import plotly.express as px

from backend.database import SessionLocal
from backend.analytics import get_zone_popularity, get_dwell_time_by_zone, get_visitor_analytics_df


def render() -> None:
    st.header("Visitor Analytics")
    db = SessionLocal()
    try:
        pop = get_zone_popularity(db)
        dwell = get_dwell_time_by_zone(db)
        df_visitors = get_visitor_analytics_df(db)
    finally:
        db.close()

    st.subheader("Zone Popularity")
    if pop:
        df = pd.DataFrame(pop)
        fig = px.bar(df, x="zone", y="visits", title="Visit count by zone")
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Average Dwell Time by Zone")
    if dwell:
        df = pd.DataFrame(dwell)
        fig = px.bar(df, x="zone", y="avg_dwell_seconds", title="Avg dwell time (seconds)")
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Visitor Records")
    if not df_visitors.empty:
        st.dataframe(df_visitors.head(50), use_container_width=True)
