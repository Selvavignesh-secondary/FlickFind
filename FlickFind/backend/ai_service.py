from sentence_transformers import SentenceTransformer
from typing import List

class AIEngine:
    def __init__(self):
        # 🎯 SWAPPED: Upgraded from 384-dim MiniLM to Nomic's 768-dim high-performance local text embedder
        self.model_name = "nomic-ai/nomic-embed-text-v1"
        self.model = None

    def load_model(self):
        """
        Downloads and caches the model locally on the first boot.
        """
        print(f"🧠 [AI Engine] Loading {self.model_name} into system memory...")
        # trust_remote_code=True is strictly required by Nomic's custom architecture layer
        self.model = SentenceTransformer(self.model_name, trust_remote_code=True)
        print("✅ [AI Engine] 768-Dimensional Model loaded successfully and ready for inference!")

    def generate_vector(self, text: str) -> List[float]:
        """
        Converts a raw validated text string into a 768-dimensional float vector.
        The vector inherently captures the deep contextual nuances of the user's mood.
        """
        if not self.model:
            raise RuntimeError("AI Model has not been initialized. Call load_model() first.")
        
        # Nomic expects queries to be prefixed with this specific modifier string to achieve max accuracy
        search_query_prefix = f"search_query: {text}"
        
        # Calculate the mathematical semantic vector natively
        embedding = self.model.encode(search_query_prefix)
        return embedding.tolist()

ai_engine = AIEngine()