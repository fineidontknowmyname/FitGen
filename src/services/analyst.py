import cv2
import asyncio
from typing import AsyncGenerator, Dict, Any
from services.vision.landmarks import landmark_detector
from services.fitness.engine import fitness_engine

class VideoAnalyst:
    async def process_video_stream(self, video_source: str = 0, exercise_type: str = "squat") -> AsyncGenerator[Dict[str, Any], None]:
        """
        generators that yields analysis results frame-by-frame.
        video_source can be an integer (webcam index) or file path.
        """
        cap = cv2.VideoCapture(video_source)

        if not cap.isOpened():
            yield {"error": "Could not open video source"}
            return

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break

            landmarks = landmark_detector.detect(frame)

            if landmarks:
                analysis = fitness_engine.analyze_form(exercise_type, landmarks)

                yield {
                    "frame_shape": frame.shape,
                    "has_landmarks": True,
                    "analysis": analysis
                }
            else:
                yield {
                     "frame_shape": frame.shape,
                     "has_landmarks": False,
                     "analysis": None
                }

            await asyncio.sleep(0.01)

        cap.release()

video_analyst = VideoAnalyst()
