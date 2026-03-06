"""Sentiment analysis by zone."""

import streamlit as st
import pandas as pd
import plotly.express as px

from backend.database import SessionLocal
from backend.analytics import get_sentiment_by_zone, get_sentiment_analytics_df


def render() -> None:
    st.header("Sentiment Analysis")
    db = SessionLocal()
    try:
        sentiment_by_zone = get_sentiment_by_zone(db)
        df = get_sentiment_analytics_df(db)
    finally:
        db.close()

    st.subheader("Emotion distribution by zone")
    if sentiment_by_zone:
        rows = []
        for s in sentiment_by_zone:
            for emotion, cnt in s["emotions"].items():
                rows.append({"zone": s["zone"], "emotion": emotion, "count": cnt})
        df_em = pd.DataFrame(rows)
        if not df_em.empty:
            fig = px.bar(df_em, x="zone", y="count", color="emotion", barmode="stack", title="Emotions per zone")
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Sentiment scores (avg confidence)")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
