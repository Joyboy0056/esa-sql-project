from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from build.config import config
from src.sql_agent.rag.embedder import Embedder
from sql.utils.load_nl_sql_pairs import load_queries
from src.logger import logger



class SQLRetriever:
    def __init__(self, qclient: QdrantClient=config.QCLIENT):
        """Initialize class for SQL retrieving with param a singleton qdrant client"""
        self.hf_embedder = Embedder()
        self.qclient = qclient
        self.queries_kb = load_queries()

    def create_collection(self, collection_name: str="nl_examples"):
        """Create a collection called `collection_name`"""
        if self.qclient.get_collection(collection_name).status != "green": 
            self.qclient.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
        else: 
            logger.error("Collection status is not green.")

    def embed(self, collection_name: str="nl_examples"):
        """Create vectors and embed them in the qdrant collection"""
        if not self.qclient.get_collection(collection_name):
            logger.error("Collection must exist, please create it.")
            return

        # construct points from queries
        embeddings: list[list[float]] = self.hf_embedder._embed(
            [
                item["nl_quest"] 
                for item in self.queries_kb
            ]
        ).tolist()
        
        points = []
        for item in self.queries_kb:
            points.append(
                PointStruct(
                    id=item["id"], 
                    vector=self.hf_embedder._embed([item["nl_quest"]]).tolist(),
                    payload={
                        "sql": item["sql_answ"],
                        "step_by_step": "<placeholder per step-by-step reasoning>"
                    }
                )
            )
     
        self.qclient.upsert(
            collection_name=collection_name,
            wait=True,
            points=[
                PointStruct
            ]
        )

