from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from qdrant_client.http.exceptions import UnexpectedResponse

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
        self.size = self.hf_embedder.embedding_dim

    def create_collection(
            self, 
            collection_name: str="nl_to_sql",
            force_rebuild: bool=False,
        ) -> Optional[object] | None:
        """Create a collection called `collection_name`"""

        v_cfg = VectorParams(size=self.size, distance=Distance.COSINE)

        if force_rebuild:
            logger.debug(f"Force rebuild activated for collection `{collection_name}`.")

            try:
                logger.debug(f"Attempt to delete collection: `{collection_name}`.")
                self.qclient.delete_collection(collection_name)
                logger.info(f"Collection `{collection_name}` deleted.")

            except UnexpectedResponse as e:
                logger.info(f"Collection `{collection_name}` didn't exist when trying to delete. Details: {e}")

            try:
                logger.debug(f"Creating collection `{collection_name}`...")
                self.qclient.create_collection(
                    collection_name=collection_name,
                    vectors_config=v_cfg
                )
                logger.info(f"Collection `{collection_name}` created (force rebuild)")

            except UnexpectedResponse as e:
                logger.error(f"Error while creating collection `{collection_name}`.")
                raise

            try:
                return self.qclient.get_collection(collection_name)

            except Exception:
                return None


        try:
            coll = self.qclient.get_collection(collection_name)
            logger.info(f"Collection `{collection_name}` already exists. No action.")
            return coll
        
        except UnexpectedResponse:
            logger.info(f"Collection `{collection_name}` not found. Go ahead with creating it...")
            
            try:
                self.qclient.create_collection(
                    collection_name=collection_name,
                    vectors_config=v_cfg
                )
                logger.info(f"Collection `{collection_name}` created.")

            except UnexpectedResponse as e:
                logger.error(f"Error while creating the collectionCollection `{collection_name}`: {e}")
                raise

            try:
                return self.qclient.get_collection(collection_name)
            
            except Exception:
                return None


    def embed(self, collection_name: str="nl_to_sql") -> None:
        """Create vectors and embed them in the qdrant collection"""
        
        try:
            self.qclient.collection_exists(collection_name)
        
        except Exception: # TODO: specialized exception
            logger.error("Collection must exist.")

        points = [
            PointStruct(
                id=item["id"],
                vector=self.hf_embedder.get_embeddings([item["nl_quest"],])[0],
                payload={
                    "nl_quest": item["nl_quest"],
                    "sql_answ": item["sql_answ"],
                    "step_by_step": "<placeholder>"
                }
            )
            for item in self.queries_kb
        ]

        logger.debug("Embedding points...")
        self.qclient.upsert(
            collection_name=collection_name,
            wait=True,
            points=points
        )
        logger.info(f" >> Embedded {len(points)} points in the collection `{collection_name}`.")

    
    def search(
            self,
            user_query: str,
            *,
            collection_name: str="nl_to_sql",
            top_k: int=5
    ) -> list[dict]:
        """Vector similarity search method"""

        try:
            self.qclient.collection_exists(collection_name)
        
        except Exception: # TODO: specialized exception
            logger.error("Collection must exist.")

        # User query embedding
        query = self.hf_embedder.get_embeddings([user_query,])[0]

        # Search step
        results = self.qclient.query_points(
            collection_name=collection_name,
            query=query,
            limit=top_k,
            with_payload=True
        )

        return [
            {
                "nl": point.payload.get("nl_quest"),
                "sql": point.payload.get("sql_answ"),
                "dsc": point.payload.get("step_by_step"),
                "score": point.score,
            }
            for point in results.points
        ]
    
    def update_collection(self, collection_name: str="nl_to_sql") -> None:
        """Update collection by inserting only new vectors"""

        try:
            points, _ = self.qclient.scroll(
                collection_name=collection_name,
                limit=10000
            )
            existing_ids = {p.id for p in points}

        except UnexpectedResponse as e:
            logger.error(f"Unexpected response from qdrant: {e}")
            return
        
        except (ValueError, RuntimeError) as e:
            logger.error(f"Error while retrieving points: {e}")
            return

        new_items = [i for i in self.queries_kb if i["id"] not in existing_ids]

        if not new_items:
            logger.info("No new vectors found: collection still updated.")
            return
        
        points = [
            
            PointStruct(
                id=item["id"],
                vector=self.hf_embedder.get_embeddings([item["nl_quest"],])[0],
                payload={
                    "nl_quest": item["nl_quest"],
                    "nl_quest": item["nl_quest"],
                    "step_by_step": "<placeholder>"
                }
            )
            for item in new_items
        ]

        try:
            self.qclient.upsert(collection_name=collection_name, wait=True, points=points)
            logger.info(f"Added {len(points)} new vectors to the collection `{collection_name}`.")

        except UnexpectedResponse as e:
            logger.error(f"Error while upserting vectors: {e}")


# Singleton
sql_retriever = SQLRetriever()