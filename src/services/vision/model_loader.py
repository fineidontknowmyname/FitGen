from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

_HERE         = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parents[3]

_DEFAULT_BODY_COMP_PATH = _PROJECT_ROOT / "models" / "body_composition.keras"
_DEFAULT_POSE_LANDMARKER_PATH = _PROJECT_ROOT / "models" / "pose_landmarker.task"

_POSE_MIN_DETECTION_CONF = 0.5
_POSE_MIN_PRESENCE_CONF  = 0.5
_POSE_MIN_TRACKING_CONF  = 0.5


def _load_keras_model(path: Path):

    if not path.exists():
        log.warning(
            "Model file not found at %s — inference will use heuristic fallback. "
            "Place a trained .keras file at this path to enable MobileNetV2 inference.",
            path,
        )
        return None

    try:
        import tensorflow as tf  # noqa: F401

        model = tf.keras.saving.load_model(str(path), compile=False)
        log.info("Loaded Keras model from %s  (params: %s)", path, model.count_params())
        return model

    except ImportError:
        log.warning("tensorflow not installed — cannot load model from %s", path)
        return None

    except Exception as exc:
        log.error("Failed to load model from %s: %s", path, exc)
        return None


def create_pose_landmarker(path: Path):
    if not path.exists():
        log.warning(
            "Pose landmarker model not found at %s — pose-based metrics (SWR, V-taper, "
            "body-fat estimate) will be unavailable. Run 'curl -o %s "
            "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
            "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task' to fetch it.",
            path, path,
        )
        return None

    try:
        import mediapipe as mp

        base_options = mp.tasks.BaseOptions(model_asset_path=str(path))
        options = mp.tasks.vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=mp.tasks.vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=_POSE_MIN_DETECTION_CONF,
            min_pose_presence_confidence=_POSE_MIN_PRESENCE_CONF,
            min_tracking_confidence=_POSE_MIN_TRACKING_CONF,
        )
        return mp.tasks.vision.PoseLandmarker.create_from_options(options)

    except ImportError:
        log.warning("mediapipe not installed — cannot create pose landmarker from %s", path)
        return None

    except Exception as exc:
        log.error("Failed to create pose landmarker from %s: %s", path, exc)
        return None


class ModelRegistry:

    def __init__(self) -> None:
        self._paths: dict[str, Path] = {
            "body_composition": Path(
                os.environ.get("BODY_COMPOSITION_MODEL_PATH", str(_DEFAULT_BODY_COMP_PATH))
            ),
            "pose_landmarker": Path(
                os.environ.get("POSE_LANDMARKER_MODEL_PATH", str(_DEFAULT_POSE_LANDMARKER_PATH))
            ),
        }
        self._cache: dict[str, object] = {}

    def set_path(self, name: str, path: str | Path) -> None:
        if name in self._cache:
            raise RuntimeError(
                f"Cannot change path for '{name}' — it has already been loaded. "
                "Restart the process to apply a new path."
            )
        self._paths[name] = Path(path)

    @property
    def body_composition(self):
        return self._get("body_composition")

    def _get(self, name: str):
        """Load (if needed) and return the named model from cache."""
        if name not in self._cache:
            path = self._paths.get(name)
            if path is None:
                log.error("No path registered for model '%s'", name)
                self._cache[name] = None
            else:
                self._cache[name] = _load_keras_model(path)
        return self._cache[name]

    def create_pose_landmarker(self):
        path = self._paths.get("pose_landmarker")
        if path is None:
            log.error("No path registered for model 'pose_landmarker'")
            return None
        return create_pose_landmarker(path)

    def preload_all(self) -> None:

        _ = self._get("body_composition")
        log.info(
            "Pre-loaded model 'body_composition': %s",
            "OK" if self._cache.get("body_composition") else "UNAVAILABLE",
        )

        pose_path = self._paths.get("pose_landmarker")
        if pose_path is not None and pose_path.exists():
            log.info("Pre-check 'pose_landmarker': model file present at %s", pose_path)
        else:
            log.warning("Pre-check 'pose_landmarker': model file missing at %s", pose_path)

    def status(self) -> dict[str, str]:
        """Return a {name: "loaded" | "not_loaded" | "unavailable" | "available"} status map."""
        out: dict[str, str] = {}
        for name, path in self._paths.items():
            if name == "pose_landmarker":
                out[name] = "available" if path.exists() else "file_missing"
                continue
            if name in self._cache:
                out[name] = "loaded" if self._cache[name] is not None else "unavailable"
            else:
                out[name] = "not_loaded" if path.exists() else "file_missing"
        return out


model_registry = ModelRegistry()
