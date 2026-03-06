"""Computer vision processing: YOLOv8, DeepSORT, zone mapping, dwell time, heatmap."""

from pathlib import Path
from typing import Any, Optional

import numpy as np

# OpenCV is optional on some deploy targets (e.g. Streamlit Cloud).
try:
    import cv2  # type: ignore
except ImportError:  # pragma: no cover
    cv2 = None  # type: ignore

# Zone coordinates as (x1, y1, x2, y2) normalized 0-1 relative to frame
ZONE_COORDS = {
    "Entrance": (0.0, 0.0, 0.25, 0.3),
    "Kitchen Tiles": (0.25, 0.0, 0.5, 0.35),
    "Living Room Tiles": (0.5, 0.0, 0.75, 0.35),
    "Bathroom Tiles": (0.0, 0.35, 0.35, 0.7),
    "Wall Tiles": (0.35, 0.35, 0.65, 0.7),
    "Large Slabs": (0.65, 0.35, 1.0, 1.0),
}


def _get_center(bbox: tuple[float, float, float, float]) -> tuple[float, float]:
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def _point_in_zone(px: float, py: float, zone_bbox: tuple[float, float, float, float]) -> bool:
    x1, y1, x2, y2 = zone_bbox
    return x1 <= px <= x2 and y1 <= py <= y2


def get_zone_for_point(px: float, py: float) -> Optional[str]:
    """Return zone name if point (normalized 0-1) is inside a zone."""
    for name, bbox in ZONE_COORDS.items():
        if _point_in_zone(px, py, bbox):
            return name
    return None


def load_yolo_model():
    """Load YOLOv8 model; fallback to None if not available."""
    try:
        from ultralytics import YOLO

        return YOLO("yolov8n.pt")
    except Exception:
        return None


def load_deepsort_tracker():
    """Load DeepSORT tracker; fallback to None if not available."""
    try:
        from deep_sort_realtime.deepsort_tracker import DeepSort

        return DeepSort(max_age=30)
    except Exception:
        return None


def detect_people_opencv(frame: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Fallback: use OpenCV HOG for person detection. Returns list of (x,y,w,h)."""
    if cv2 is None:
        return []
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    boxes, _ = hog.detectMultiScale(gray, winStride=(8, 8), padding=(8, 8), scale=1.05)
    return [tuple(int(x) for x in b) for b in boxes]


def detect_people_yolo(frame: np.ndarray, model) -> list[tuple[int, int, int, int]]:
    """Use YOLOv8 for person detection. Returns list of (x1,y1,x2,y2)."""
    results = model(frame, verbose=False)[0]
    boxes = []
    for box in results.boxes:
        if int(box.cls) == 0:  # COCO class 0 = person
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            boxes.append((int(x1), int(y1), int(x2), int(y2)))
    return boxes


def process_frame(
    frame: np.ndarray,
    yolo_model=None,
    tracker=None,
    h: int = 0,
    w: int = 0,
) -> tuple[np.ndarray, list[dict[str, Any]], dict[str, float]]:
    """
    Process a frame: detect people, optionally track, assign zones, accumulate heatmap.
    Returns (annotated_frame, visitor_data, zone_counts).
    """
    if h == 0 or w == 0:
        h, w = frame.shape[:2]

    if yolo_model is not None:
        detections = detect_people_yolo(frame, yolo_model)
        # Convert to (x,y,w,h) for DeepSORT
        dets = [[x1, y1, x2 - x1, y2 - y1] for x1, y1, x2, y2 in detections]
    else:
        boxes = detect_people_opencv(frame)
        dets = [[x, y, w, h] for x, y, w, h in boxes]

    visitor_data = []
    zone_counts: dict[str, float] = {name: 0.0 for name in ZONE_COORDS}

    if cv2 is None:
        # No annotation possible without OpenCV; return safely.
        return frame, visitor_data, zone_counts

    if tracker is not None and dets:
        try:
            # DeepSORT expects ([left, top, width, height], confidence, class)
            dets_formatted = [((x, y, w, h), 0.9, "person") for x, y, w, h in dets]
            tracks = tracker.update_tracks(dets_formatted, frame=frame)
            for track in tracks:
                if not track.is_confirmed():
                    continue
                tid = track.track_id
                ltrb = track.to_ltrb()
                x1, y1, x2, y2 = int(ltrb[0]), int(ltrb[1]), int(ltrb[2]), int(ltrb[3])
                cx = (x1 + x2) / 2 / w
                cy = (y1 + y2) / 2 / h
                zone = get_zone_for_point(cx, cy)
                if zone:
                    zone_counts[zone] += 1.0
                visitor_data.append({"id": tid, "bbox": (x1, y1, x2, y2), "zone": zone})
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    str(tid),
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    1,
                )
        except Exception:
            pass
    else:
        for i, (x, y, w_box, h_box) in enumerate(dets):
            x1, y1, x2, y2 = x, y, x + w_box, y + h_box
            cx = (x1 + x2) / 2 / w
            cy = (y1 + y2) / 2 / h
            zone = get_zone_for_point(cx, cy)
            if zone:
                zone_counts[zone] += 1.0
            visitor_data.append({"id": i + 1, "bbox": (x1, y1, x2, y2), "zone": zone})
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame,
                str(i + 1),
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1,
            )

    return frame, visitor_data, zone_counts


def generate_heatmap_overlay(
    zone_counts: dict[str, float],
    frame_shape: tuple[int, int],
) -> np.ndarray:
    """Create heatmap overlay (red=hot, blue=cold) from zone counts."""
    h, w = frame_shape[:2]
    overlay = np.zeros((h, w, 3), dtype=np.uint8)
    max_count = max(zone_counts.values()) or 1
    for zone_name, count in zone_counts.items():
        bbox = ZONE_COORDS.get(zone_name)
        if not bbox:
            continue
        x1, y1, x2, y2 = [int(v * (w if i % 2 == 0 else h)) for i, v in enumerate(bbox)]
        intensity = count / max_count
        # BGR: blue (low) -> red (high)
        b = int(255 * (1 - intensity))
        r = int(255 * intensity)
        overlay[y1:y2, x1:x2] = (b, 128, r)

    # Blend using numpy to avoid requiring cv2
    return (overlay.astype(np.float32) * 0.3).astype(np.uint8)


def get_sample_video_path() -> Optional[Path]:
    """Return path to sample CCTV video if exists, else None."""
    candidates = [
        Path(__file__).parent.parent / "sample_video.mp4",
        Path(__file__).parent.parent / "assets" / "sample_video.mp4",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None
