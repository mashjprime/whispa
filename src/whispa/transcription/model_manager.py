"""Model management for faster-whisper."""

import logging
import threading
from pathlib import Path
from typing import Optional, Callable, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Information about a Whisper model."""

    name: str
    size_mb: int
    description: str


# Available models with their approximate sizes
AVAILABLE_MODELS = {
    "tiny": ModelInfo("tiny", 75, "Fastest, lowest accuracy"),
    "tiny.en": ModelInfo("tiny.en", 75, "Fastest, English only"),
    "base": ModelInfo("base", 145, "Fast, low accuracy"),
    "base.en": ModelInfo("base.en", 145, "Fast, English only"),
    "small": ModelInfo("small", 488, "Balanced speed/accuracy"),
    "small.en": ModelInfo("small.en", 488, "Balanced, English only"),
    "medium": ModelInfo("medium", 1500, "Good accuracy, slower"),
    "medium.en": ModelInfo("medium.en", 1500, "Good accuracy, English only"),
    "large-v2": ModelInfo("large-v2", 3100, "Best accuracy, slowest"),
    "large-v3": ModelInfo("large-v3", 3100, "Latest large model"),
    "large-v3-turbo": ModelInfo("large-v3-turbo", 1600, "Best speed/accuracy tradeoff"),
}


class ModelManager:
    """Manages Whisper model download and caching."""

    def __init__(self, models_dir: Path):
        """Initialize model manager.

        Args:
            models_dir: Directory to store models
        """
        self.models_dir = models_dir
        self._lock = threading.Lock()

    def get_available_models(self) -> List[ModelInfo]:
        """Get list of available models.

        Returns:
            List of ModelInfo objects
        """
        return list(AVAILABLE_MODELS.values())

    def is_model_downloaded(self, model_size: str) -> bool:
        """Check if model is already downloaded.

        Args:
            model_size: Model size name

        Returns:
            True if model exists locally
        """
        # faster-whisper downloads to huggingface cache by default
        # Check if the model directory exists in our models dir
        model_path = self.models_dir / model_size
        return model_path.exists()

    def get_model_path(self, model_size: str) -> str:
        """Get path or identifier for a model.

        Args:
            model_size: Model size name

        Returns:
            Model path or name (faster-whisper will download if needed)
        """
        # faster-whisper uses the model name directly and handles downloading
        return model_size

    def download_model(
        self,
        model_size: str,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> bool:
        """Download a model (triggers faster-whisper download).

        Args:
            model_size: Model size name
            progress_callback: Callback for progress updates (progress 0-1, message)

        Returns:
            True if download successful
        """
        if model_size not in AVAILABLE_MODELS:
            logger.error("Unknown model: %s", model_size)
            return False

        try:
            if progress_callback:
                progress_callback(0.0, f"Downloading {model_size} model...")

            # Import faster_whisper to trigger download
            from faster_whisper import WhisperModel

            # This will download the model if not cached
            logger.info("Downloading model %s (this may take a while)...", model_size)

            # Create model with download_root to our models dir
            _ = WhisperModel(
                model_size,
                device="cpu",  # Use CPU for download only
                compute_type="int8",
                download_root=str(self.models_dir),
            )

            if progress_callback:
                progress_callback(1.0, "Download complete")

            logger.info("Model %s downloaded successfully", model_size)
            return True

        except Exception as e:
            logger.error("Failed to download model %s: %s", model_size, e)
            if progress_callback:
                progress_callback(0.0, f"Download failed: {e}")
            return False

    def delete_model(self, model_size: str) -> bool:
        """Delete a downloaded model.

        Args:
            model_size: Model size name

        Returns:
            True if deleted successfully
        """
        import shutil

        model_path = self.models_dir / model_size
        if model_path.exists():
            try:
                shutil.rmtree(model_path)
                logger.info("Deleted model %s", model_size)
                return True
            except Exception as e:
                logger.error("Failed to delete model %s: %s", model_size, e)
                return False
        return True

    def get_model_size_mb(self, model_size: str) -> int:
        """Get model size in MB.

        Args:
            model_size: Model size name

        Returns:
            Size in MB or 0 if unknown
        """
        info = AVAILABLE_MODELS.get(model_size)
        return info.size_mb if info else 0


def detect_gpu() -> tuple[bool, str]:
    """Detect if CUDA GPU is available.

    Returns:
        Tuple of (cuda_available, device_name)
    """
    try:
        import torch

        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
            logger.info("CUDA available: %s (%.1f GB VRAM)", device_name, vram_gb)
            return True, f"{device_name} ({vram_gb:.1f} GB)"
        else:
            logger.info("CUDA not available, using CPU")
            return False, "CPU"
    except Exception as e:
        logger.warning("Failed to detect GPU: %s", e)
        return False, "CPU"
