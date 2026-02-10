from ultralytics.models import YOLO
from pathlib import Path
import numpy as np
from typing import Optional, Dict, List


class YOLOModel:
    """Manager class for loading and managing multiple YOLO models."""

    _models: Dict[str, YOLO] = {}
    _available_models: List[str] = []
    _default_model: Optional[str] = None

    @classmethod
    def _discover_models(cls) -> List[str]:
        """Discover available YOLO models in both Docker and development paths."""
        available = []

        # Docker mode - models are in /app/ml_models/*.pt
        docker_models_dir = Path("/app/ml_models")
        if docker_models_dir.exists():
            print("Running in Docker mode")
            for model_file in docker_models_dir.glob("*.pt"):
                model_name = model_file.stem  # filename without .pt extension
                available.append(model_name)
                print(f"  Found model: {model_name}")
        else:
            # Development mode - models are in ml/runs/detect/*/weights/best.pt
            print("Running in Development mode")
            backend_dir = Path(__file__).parent.parent
            ml_runs = backend_dir.parent / "ml" / "runs" / "detect"

            if ml_runs.exists():
                for run_dir in ml_runs.iterdir():
                    if run_dir.is_dir():
                        model_file = run_dir / "weights" / "best.pt"
                        if model_file.exists():
                            model_name = run_dir.name
                            available.append(model_name)
                            print(f"  Found model: {model_name}")

        return available

    @classmethod
    def initialize(cls) -> None:
        """Initialize and discover available models."""
        if not cls._available_models:
            cls._available_models = cls._discover_models()

            if cls._available_models:
                # Set default to the most recent version (highest v number)
                cls._default_model = sorted(cls._available_models)[-1]
                print(f"Default model set to: {cls._default_model}")
            else:
                raise FileNotFoundError("No YOLO models found in expected locations")

    @classmethod
    def get_available_models(cls) -> List[str]:
        """Get list of available model names."""
        if not cls._available_models:
            cls.initialize()
        return cls._available_models.copy()

    @classmethod
    def get_default_model(cls) -> Optional[str]:
        """Get the default model name."""
        if not cls._default_model:
            cls.initialize()
        return cls._default_model

    @classmethod
    def _get_model_path(cls, model_name: str) -> Path:
        """Get the full path to a model file."""
        # Try Docker path first
        docker_path = Path(f"/app/ml_models/{model_name}.pt")
        if docker_path.exists():
            return docker_path

        # Try development path
        backend_dir = Path(__file__).parent.parent
        dev_path = (
            backend_dir.parent
            / "ml"
            / "runs"
            / "detect"
            / model_name
            / "weights"
            / "best.pt"
        )

        if dev_path.exists():
            return dev_path

        raise FileNotFoundError(f"Model '{model_name}' not found at expected locations")

    @classmethod
    def load_model(cls, model_name: Optional[str] = None) -> YOLO:
        """
        Load a YOLO model by name. If already loaded, return cached instance.

        Args:
            model_name: Name of the model to load. If None, uses default model.

        Returns:
            YOLO model instance
        """
        if not cls._available_models:
            cls.initialize()

        # Use default model if none specified
        if model_name is None:
            model_name = cls._default_model

        # Validate model name
        if model_name not in cls._available_models:
            raise ValueError(
                f"Model '{model_name}' not available. "
                f"Available models: {', '.join(cls._available_models)}"
            )

        # Return cached model if already loaded
        if model_name in cls._models:
            print(f"Using cached model: {model_name}")
            return cls._models[model_name]

        # Load new model
        model_path = cls._get_model_path(model_name)
        print(f"Loading YOLO model '{model_name}' from {model_path}")

        model = YOLO(str(model_path))
        cls._models[model_name] = model

        print(f"Model '{model_name}' loaded successfully")
        return model

    @classmethod
    def predict(
        cls,
        image: np.ndarray,
        conf_threshold: float = 0.5,
        model_name: Optional[str] = None,
    ):
        """
        Run inference on an image using specified model.

        Args:
            image: Image as numpy array (BGR format from OpenCV or RGB from PIL)
            conf_threshold: Confidence threshold for detections
            model_name: Name of model to use. If None, uses default model.

        Returns:
            YOLO prediction results
        """
        model = cls.load_model(model_name)
        results = model(image, conf=conf_threshold, verbose=False)
        return results[0]  # Return first result
