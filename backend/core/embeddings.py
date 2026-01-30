import clip
import torch
import numpy as np
from PIL import Image
from pathlib import Path
from typing import List, Optional, Union, Tuple
import logging
import warnings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress unnecessary warnings
warnings.filterwarnings('ignore', category=UserWarning)


class MultimodalEmbedder:

    def __init__(self, model_name: str = "ViT-B/32"):
        try:
            logger.info(f"Loading CLIP model {model_name}...")

            # Detect device
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {self._device}")

            # Load model and preprocessing
            self.model, self.preprocess = clip.load(model_name, device=self._device)

            # Set to evaluation mode
            self.model.eval()

            self._model_name = model_name
            logger.info(f"✅ Model loaded successfully on {self._device}")

        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            raise RuntimeError(f"Could not initialize MultimodalEmbedder: {e}")

    @property
    def device(self) -> str:
        return self._device

    def embed_text(self, text: str) -> np.ndarray:
        if not text or not isinstance(text, str):
            raise ValueError("Text must be a non-empty string")

        if not text.strip():
            raise ValueError("Text cannot be empty or whitespace only")

        try:
            with torch.no_grad():
                text_tokens = clip.tokenize([text], truncate=True).to(self._device)

                if len(text.split()) > 50:
                    logger.warning(
                        "Text exceeds ~50 words and may be truncated "
                        "(CLIP max 77 tokens)."
                    )

                text_features = self.model.encode_text(text_tokens)
                embedding = text_features.cpu().numpy().astype(np.float32).squeeze()
                embedding = embedding / np.linalg.norm(embedding)
                return embedding

        except Exception as e:
            logger.error(f"Failed to embed text: {e}")
            raise RuntimeError(f"Text encoding failed: {e}")

    def embed_image(self, image_path: Union[str, Path]) -> np.ndarray:
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            image = Image.open(image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')

            with torch.no_grad():
                image_input = self.preprocess(image).unsqueeze(0).to(self._device)
                image_features = self.model.encode_image(image_input)
                embedding = image_features.cpu().numpy().astype(np.float32).squeeze()
                embedding = embedding / np.linalg.norm(embedding)
                return embedding

        except Exception as e:
            logger.error(f"Failed to embed image: {e}")
            raise RuntimeError(f"Image encoding failed: {e}")

    def embed_multimodal(
        self,
        text: str,
        image_path: Union[str, Path],
        text_weight: float = 0.7
    ) -> np.ndarray:
        if not 0 <= text_weight <= 1:
            raise ValueError(f"text_weight must be in [0, 1], got {text_weight}")

        image_weight = 1 - text_weight
        text_embedding = self.embed_text(text)
        image_embedding = self.embed_image(image_path)

        combined = text_weight * text_embedding + image_weight * image_embedding
        combined = combined / np.linalg.norm(combined)
        return combined

    def embed_batch_text(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> np.ndarray:
        if not texts:
            raise ValueError("Text list cannot be empty")

        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("No valid texts to embed")

        try:
            all_embeddings = []
            iterator = range(0, len(valid_texts), batch_size)

            if show_progress:
                try:
                    from tqdm import tqdm
                    iterator = tqdm(iterator, desc="Embedding batches")
                except ImportError:
                    logger.warning("tqdm not installed")

            with torch.no_grad():
                for i in iterator:
                    batch = valid_texts[i:i + batch_size]
                    tokens = clip.tokenize(batch, truncate=True).to(self._device)
                    features = self.model.encode_text(tokens)
                    all_embeddings.append(features.cpu().numpy().astype(np.float32))

            embeddings = np.vstack(all_embeddings)
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            return embeddings

        except Exception as e:
            logger.error(f"Failed to embed batch: {e}")
            raise RuntimeError(f"Batch encoding failed: {e}")

    @staticmethod
    def get_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        if vec1.shape != (512,) or vec2.shape != (512,):
            raise ValueError("Vectors must have shape (512,)")

        similarity = np.dot(vec1, vec2)
        return float(np.clip(similarity, -1.0, 1.0))

    @classmethod
    def from_pretrained(cls, model_name: str = "ViT-B/32"):
        return cls(model_name=model_name)

    def __repr__(self) -> str:
        return f"MultimodalEmbedder(model={self._model_name}, device={self._device})"


def create_embedder(model_name: str = "ViT-B/32") -> MultimodalEmbedder:
    return MultimodalEmbedder(model_name=model_name)

# Global instance
clip_embedder = create_embedder()
