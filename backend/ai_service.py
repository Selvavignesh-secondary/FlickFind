import os
from typing import List
from dotenv import load_dotenv

# Ensure environment variables are loaded immediately
load_dotenv()

# --- Backward compatibility patch for transformers >= 4.45 / 5.x ---
# NomicBERT's custom modeling file requires get_extended_attention_mask,
# which was refactored out in modern transformers releases.
import torch
from transformers import PreTrainedModel

def _get_extended_attention_mask_compat(self, attention_mask, input_shape, device=None, dtype=None):
    if dtype is None:
        dtype = self.dtype if hasattr(self, "dtype") else torch.float32
    if attention_mask.dim() == 3:
        extended_attention_mask = attention_mask[:, None, :, :]
    elif attention_mask.dim() == 2:
        extended_attention_mask = attention_mask[:, None, None, :]
    else:
        raise ValueError(f"Unexpected attention_mask shape: {attention_mask.shape}")
    extended_attention_mask = extended_attention_mask.to(dtype=dtype)
    extended_attention_mask = (1.0 - extended_attention_mask) * torch.finfo(dtype).min
    return extended_attention_mask

if not hasattr(PreTrainedModel, "get_extended_attention_mask"):
    PreTrainedModel.get_extended_attention_mask = _get_extended_attention_mask_compat


class AIEngine:
    """Hybrid Embedding Engine for FlickFind.

    Default: nomic-ai/nomic-embed-text-v1.5 (768 dimensions).
    Matches the pre-computed embeddings for the 1M+ movie dataset in PostgreSQL.

    Fallback: Google Gemini Embedding API if local model cannot be loaded.
    """

    def __init__(self):
        self.model_name = "nomic-ai/nomic-embed-text-v1.5"
        self.local_model = None
        self.gemini_client = None
        self.use_gemini_fallback = os.getenv("USE_GEMINI_EMBEDDINGS", "false").lower() == "true"

    def load_model(self):
        if self.use_gemini_fallback:
            self._init_gemini()
            print("[AI Engine] Configured with Gemini Embedding API.")
            return

        try:
            print(f"[AI Engine] Loading local embedding model '{self.model_name}'...")
            from sentence_transformers import SentenceTransformer
            self.local_model = SentenceTransformer(self.model_name, trust_remote_code=True)
            print("[AI Engine] Local Nomic model loaded successfully (768-dim).")
        except Exception as e:
            print(f"[AI Engine] Warning: Failed to load local model: {e}")
            print("[AI Engine] Falling back to Gemini Embedding API...")
            self._init_gemini()
            self.use_gemini_fallback = True

    def _init_gemini(self):
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is missing.")
        self.gemini_client = genai.Client(api_key=api_key)

    def generate_vector(self, text: str) -> List[float]:
        """Encodes input text into a 768-dimensional normalized embedding vector."""
        if not self.use_gemini_fallback and self.local_model is not None:
            # Asymmetric search prompt recommended by Nomic for queries
            query_text = f"search_query: {text}" if not text.startswith("search_query:") else text
            embedding = self.local_model.encode(query_text)
            return [float(x) for x in embedding]

        # Gemini API fallback
        if self.gemini_client is None:
            self._init_gemini()

        from google.genai import types as gtypes
        result = self.gemini_client.models.embed_content(
            model="models/gemini-embedding-001",
            contents=text,
            config=gtypes.EmbedContentConfig(output_dimensionality=768),
        )
        return list(result.embeddings[0].values)


# Global singleton instance
ai_engine = AIEngine()