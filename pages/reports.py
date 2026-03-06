"""Reports and data export."""

import io
import streamlit as st
import pandas as pd

from backend.database import SessionLocal
from backend.analytics import (
    get_visitor_analytics_df,
    get_zone_analytics_df,
    get_sentiment_analytics_df,
    get_insights,
)


def render() -> None:
    st.header("Reports")
    db = SessionLocal()
    try:
        df_visitors = get_visitor_analytics_df(db)
        df_zones = get_zone_analytics_df(db)
        df_sentiment = get_sentiment_analytics_df(db)
        insights = get_insights(db)
    finally:
        db.close()

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_visitors.to_excel(writer, sheet_name="Visitor Analytics", index=False)
        df_zones.to_excel(writer, sheet_name="Zone Popularity", index=False)
        df_sentiment.to_excel(writer, sheet_name="Sentiment Scores", index=False)
        pd.DataFrame({"Insight": insights}).to_excel(writer, sheet_name="Insights", index=False)
    buffer.seek(0)

    st.download_button(
        "Export Analytics Report",
        data=buffer,
        file_name="visionsense_analytics_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    st.success("Click the button above to download the Excel report.")
