from typing import List, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd


# Step 1: Create a demo vector store
def create_vector_store_demo() -> pd.DataFrame:
    data = [
        {"category": "Legal Document", "feature": "summons notice"},
        {"category": "Financial Document", "feature": "loan agreement"},
        {"category": "Medical Record", "feature": "patient diagnosis"},
        {"category": "Technical Manual", "feature": "installation guide"},
    ]
    vector_store = pd.DataFrame(data)
    return vector_store


# Step 2: Encode the features using a pre-trained model
class VectorStoreAssistant:
    def __init__(self, vector_store: pd.DataFrame):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.vector_store = vector_store
        self.vector_store["embedding"] = self.vector_store["feature"].apply(
            self._encode
        )

    def _encode(self, text: str) -> np.ndarray:
        return self.model.encode(text)

    def classify_text(self, texts: List[str]) -> List[Tuple[str, str]]:
        results = []
        for text in texts:
            embedding = self._encode(text)
            similarities = [
                cosine_similarity([embedding], [stored_emb])[0][0]
                for stored_emb in self.vector_store["embedding"]
            ]
            best_match_idx = np.argmax(similarities)
            category = self.vector_store.iloc[best_match_idx]["category"]
            results.append((text, category))
        return results


# Step 3: Functions for processing multiple texts
def batch_classify_text(
    vector_store: pd.DataFrame, texts: List[str]
) -> List[Tuple[str, str]]:
    assistant = VectorStoreAssistant(vector_store)
    return assistant.classify_text(texts)


# Usage example
if __name__ == "__main__":
    # Create demo vector store
    vector_store = create_vector_store_demo()

    # Input texts for classification
    input_texts = [
        "This document contains a summons notice.",
        "Details about the loan agreement are outlined here.",
        "Patient diagnosis is included in this medical report.",
        "Refer to the installation guide for setup.",
    ]

    # Classify texts
    results = batch_classify_text(vector_store, input_texts)

    # Print results
    for text, category in results:
        print(f"Text: {text}\nCategory: {category}\n")
