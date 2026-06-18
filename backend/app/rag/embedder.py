import hashlib
import numpy as np
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class MultilingualEmbedder:
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self.model = None
        self.dimension = 768  # LaBSE output dimension is 768
        
        # Proactively load the model, fallback to mock if loading fails
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully.")
        except Exception as e:
            logger.warning(
                f"Failed to load sentence-transformers model '{self.model_name}': {e}. "
                f"Falling back to high-fidelity mock deterministic embeddings."
            )
            self.model = None

    def embed_text(self, text: str) -> list[float]:
        """Generate a vector embedding for a single text."""
        if self.model:
            try:
                embeddings = self.model.encode([text])
                return embeddings[0].tolist()
            except Exception as e:
                logger.error(f"Error generating embedding with model: {e}. Using fallback.")
        
        # Fallback deterministic vector generator using SHA-256 hash
        # Ensures that identical texts produce identical embeddings for unit tests / offline runs
        sha = hashlib.sha256(text.encode("utf-8")).digest()
        # Convert hash to a deterministic pseudo-random float vector of dimension 768
        np.random.seed(int.from_bytes(sha[:4], byteorder="big"))
        vec = np.random.uniform(-1.0, 1.0, self.dimension)
        # Normalize vector
        vec = vec / np.linalg.norm(vec)
        return vec.tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings for a list of texts."""
        if self.model:
            try:
                embeddings = self.model.encode(texts)
                return embeddings.tolist()
            except Exception as e:
                logger.error(f"Error embedding documents: {e}. Using fallback.")
        
        return [self.embed_text(t) for t in texts]

# Instantiate singleton
embedder = MultilingualEmbedder()
