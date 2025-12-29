from sentence_transformers import SentenceTransformer

class Embedder:
    """Embedder for SentenceTransformer by HuggingFace"""
    def __init__(self, model=SentenceTransformer("all-MiniLM-L6-v2")):
        self.model = model 

    def _embed(self, sentences: list[str]):
        embeddings = self.model.encode(sentences)
        # print(embeddings.shape)  [3, 384]
        return embeddings
    
    def _distance(self, embeddings):
        similarities = self.model.similarity(embeddings, embeddings)
        # print(similarities)
        return similarities