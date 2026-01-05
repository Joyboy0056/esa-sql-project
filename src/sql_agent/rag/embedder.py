from build.config import config

class Embedder:
    """Embedder for SentenceTransformer by HuggingFace"""
    def __init__(
            self, 
            model=config.EMBEDDING_MODEL, # all-MiniLM-L6-v2
            client=config.EMBEDDING_CLIENT,
            dimension=config.EMBEDDING_DIM
        ):
        self.embedding_model = model 
        self.embedding_client = client
        self.embedding_dim = dimension

    def get_embeddings(self, sentences: list[str]) -> list[float]:
        embeddings = self.embedding_model.encode(sentences)
        return embeddings.tolist()