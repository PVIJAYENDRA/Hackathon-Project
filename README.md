# VisionSense

AI retail analytics platform for tile showrooms. Converts CCTV footage into business intelligence: visitor detection, zone tracking, dwell time, sentiment analysis, and insights.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open the app in your browser. Log in with:

- **Admin:** admin@visionsense.com / admin123
- **Manager:** manager@visionsense.com / manager123

## Features

- **Login** – JWT auth, bcrypt password hashing
- **Dashboard** – Total visitors, current count, avg duration, top section, charts
- **Live Camera** – YOLOv8 + DeepSORT visitor detection (OpenCV HOG fallback)
- **Heatmap** – Zone engagement (red=hot, blue=cold)
- **Visitor Analytics** – Zone popularity, dwell time
- **Sentiment Analysis** – Emotion distribution by zone
- **Reports** – Export Excel analytics report

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy, SQLite
- **AI:** OpenCV, YOLOv8, DeepSORT, DeepFace
- **Frontend:** Streamlit, Plotly
- **Auth:** JWT, bcrypt

## Project Structure

```
├── app.py              # Streamlit entrypoint
├── backend/
│   ├── api.py          # FastAPI routes (optional deployment)
│   ├── auth.py         # JWT, bcrypt
│   ├── database.py     # SQLite, models
│   ├── models.py       # ORM
│   ├── seed.py         # Sample users + 100 visitors
│   ├── analytics.py    # Metrics, insights
│   └── video_processing.py  # CV pipeline
├── pages/              # Streamlit pages
└── requirements.txt
```

## Sample Video

Place `sample_video.mp4` in the project root for live camera processing. Otherwise use webcam or the demo mode.
