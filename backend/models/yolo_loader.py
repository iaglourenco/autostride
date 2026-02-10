from ultralytics.models import YOLO
from pathlib import Path
import numpy as np
from typing import Optional


class YOLOModel:
    """Singleton class for loading and managing the YOLO model."""

    _instance: Optional["YOLOModel"] = None
    _model: Optional[YOLO] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._model is None:
            self._load_model()

    def _load_model(self) -> None:
        """Load the YOLO model from the specified path."""
        # Path to the trained model
        # backend/../ml/runs/detect/yolo11m-pose_manual/weights/best.pt
        backend_dir = Path(__file__).parent.parent
        model_path = (
            backend_dir.parent
            / "ml"
            / "runs"
            / "detect"
            / "yolo11m-pose_manual_v2_v1"
            / "weights"
            / "best.pt"
        )

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found at {model_path}")

        print(f"Loading YOLO model from {model_path}")
        self._model = YOLO(str(model_path))
        print("YOLO model loaded successfully")

    def predict(self, image: np.ndarray, conf_threshold: float = 0.5):
        """
        Run inference on an image.

        Args:
            image: Image as numpy array (BGR format from OpenCV or RGB from PIL)
            conf_threshold: Confidence threshold for detections

        Returns:
            YOLO prediction results
        """
        if self._model is None:
            raise RuntimeError("Model not loaded")

        results = self._model(image, conf=conf_threshold, verbose=False)
        return results[0]  # Return first result

    @property
    def model(self) -> YOLO | None:
        """Get the underlying YOLO model."""
        return self._model
