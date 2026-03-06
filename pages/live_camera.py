"""Live camera analytics: video stream with visitor detection and tracking."""

import streamlit as st
import numpy as np

try:
    import cv2  # type: ignore
except ImportError:  # pragma: no cover - cloud environments may lack OpenCV
    cv2 = None  # type: ignore

from backend.video_processing import (
    load_yolo_model,
    load_deepsort_tracker,
    process_frame,
    get_sample_video_path,
)


def render() -> None:
    st.header("Live Camera Analytics")

    if cv2 is None:
        st.error(
            "OpenCV (`cv2`) is not available in this environment, "
            "so the live camera view cannot run on Streamlit Cloud.\n\n"
            "You can still deploy the app and use all analytics pages; "
            "run it locally with OpenCV installed to use Live Camera."
        )
        return

    sample_path = get_sample_video_path()
    use_webcam = st.checkbox("Use webcam (if no sample video)", value=not bool(sample_path))
    yolo_model = load_yolo_model()
    tracker = load_deepsort_tracker()
    if yolo_model is None:
        st.warning("YOLOv8 not available; using OpenCV HOG fallback.")
    if tracker is None:
        st.warning("DeepSORT not available; using simple ID assignment.")

    cap = None
    if use_webcam:
        cap = cv2.VideoCapture(0)
    elif sample_path:
        cap = cv2.VideoCapture(str(sample_path))
    else:
        st.info("No sample video found. Place sample_video.mp4 in project root or enable webcam.")
        placeholder = st.empty()
        if st.button("Run Demo (synthetic frames)"):
            for i in range(20):
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(
                    frame,
                    "Demo - No video source",
                    (80, 240),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 255, 255),
                    2,
                )
                placeholder.image(frame, channels="BGR")
                import time

                time.sleep(0.15)
        return

    if cap and not cap.isOpened():
        st.error("Could not open video source.")
        return

    frame_skip = st.slider("Process every N frames", 1, 5, 2)
    num_frames = st.slider("Frames to process", 10, 100, 30)
    if st.button("Start Processing"):
        st_placeholder = st.empty()
        count_placeholder = st.empty()
        frame_idx = 0
        processed = 0
        while cap.isOpened() and processed < num_frames:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            frame_idx += 1
            if frame_idx % frame_skip != 0:
                continue
            h, w = frame.shape[:2]
            annotated, visitors, _ = process_frame(frame, yolo_model, tracker, h, w)
            count_placeholder.metric("Visitors in frame", len(visitors))
            st_placeholder.image(annotated, channels="BGR", use_container_width=True)
            processed += 1
        cap.release()
        st.success("Processing complete.")
