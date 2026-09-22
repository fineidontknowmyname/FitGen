import math

import cv2
import mediapipe as mp
import numpy as np
from typing import NamedTuple, List, Optional, Tuple

from schemas.vision import SWRCategory
from services.vision.model_loader import model_registry


class Landmark(NamedTuple):
    x: float
    y: float
    z: float
    visibility: float


class LandmarkDetector:

    def detect(self, frame: np.ndarray) -> Optional[List[Landmark]]:

        landmarker = model_registry.create_pose_landmarker()
        if landmarker is None:
            return None

        try:
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(img_rgb))
            result = landmarker.detect(mp_image)
        except Exception:
            return None
        finally:
            landmarker.close()

        if not result.pose_landmarks:
            return None

        return [
            Landmark(
                x=lm.x, y=lm.y, z=lm.z,
                visibility=lm.visibility if lm.visibility is not None else 1.0,
            )
            for lm in result.pose_landmarks[0]
        ]

    def detect_from_bytes(self, image_bytes: bytes) -> Optional[List[Landmark]]:
        nparr   = np.frombuffer(image_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            return None
        return self.detect(img_bgr)

    def draw_landmarks(self, frame: np.ndarray, landmarks_list) -> np.ndarray:
        return frame


def calculate_shoulder_waist_ratio(
    landmarks: List[Landmark],
    image_width: int,
    image_height: int,
) -> Tuple[float, float, float, SWRCategory]:

    l_sh = landmarks[11]
    r_sh = landmarks[12]
    l_hp = landmarks[23]
    r_hp = landmarks[24]

    shoulder_width_px = math.hypot(
        (l_sh.x - r_sh.x) * image_width,
        (l_sh.y - r_sh.y) * image_height,
    )
    waist_width_px = math.hypot(
        (l_hp.x - r_hp.x) * image_width,
        (l_hp.y - r_hp.y) * image_height,
    )

    if waist_width_px < 1e-6:
        return (shoulder_width_px, 0.0, 1.1, SWRCategory.BALANCED)

    swr = shoulder_width_px / waist_width_px

    if swr < 1.0:
        category = SWRCategory.OVERFAT
    elif swr > 1.2:
        category = SWRCategory.ATHLETIC
    else:
        category = SWRCategory.BALANCED

    return (round(shoulder_width_px, 2), round(waist_width_px, 2),
            round(swr, 3), category)


landmark_detector = LandmarkDetector()
