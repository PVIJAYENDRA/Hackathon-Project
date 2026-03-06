"""Dashboard page: analytics summary cards and charts."""

import streamlit as st
import pandas as pd
import plotly.express as px

from backend.database import SessionLocal
from backend.analytics import (
    get_today_visitors,
    get_current_visitors,
    get_avg_visit_duration,
    get_top_section,
    get_zone_popularity,
    get_dwell_time_by_zone,
    get_insights,
)


def render() -> None:
    st.header("Dashboard")
    db = SessionLocal()
    try:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Visitors Today", get_today_visitors(db))
        with col2:
            st.metric("Currently in Showroom", get_current_visitors(db))
        with col3:
            st.metric("Avg Visit Duration (sec)", get_avg_visit_duration(db))
        with col4:
            st.metric("Top Section", get_top_section(db))

        st.divider()

        pop = get_zone_popularity(db)
        dwell = get_dwell_time_by_zone(db)
        if pop:
            c1, c2 = st.columns(2)
            with c1:
                df_pop = pd.DataFrame(pop)
                fig1 = px.bar(df_pop, x="zone", y="visits", title="Zone Popularity (Visit Count)")
                fig1.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig1, use_container_width=True)
            with c2:
                df_dwell = pd.DataFrame(dwell)
                fig2 = px.bar(df_dwell, x="zone", y="avg_dwell_seconds", title="Avg Dwell Time by Zone (sec)")
                fig2.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig2, use_container_width=True)

        insights = get_insights(db)
        if insights:
            st.subheader("Smart Insights")
            for i in insights:
                st.info(i)
    finally:
        db.close()
