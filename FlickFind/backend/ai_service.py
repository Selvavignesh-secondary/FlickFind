from sentence_transformers import SentenceTransformer
from typing import List

class AIEngine:
    def __init__(self):
        self.model_name = "all-MiniLM-L6-v2"
        self.model = None

    def load_model(self):
        """
        Downloads and caches the model locally on the first boot.
        """
        print(f"🧠 [AI Engine] Loading {self.model_name} into system memory...")
        self.model = SentenceTransformer(self.model_name)
        print("✅ [AI Engine] Model loaded successfully and ready for inference!")

    def generate_vector(self, text: str) -> List[float]:
        """
        Converts a raw validated text string into a 384-dimensional float vector.
        The vector inherently captures the deep contextual nuances of the user's mood.
        """
        if not self.model:
            raise RuntimeError("AI Model has not been initialized. Call load_model() first.")
        
        # Calculate the mathematical semantic vector natively
        embedding = self.model.encode(text)
        return embedding.tolist()

ai_engine = AIEngine()