import os
from dataclasses import dataclass

from agents import OpenAIChatCompletionsModel, AsyncOpenAI
from agents.extensions.models.litellm_model import LitellmModel
from qdrant_client import QdrantClient
from dotenv import load_dotenv
load_dotenv("build/.env")

from src.logger import logger

@dataclass
class Config:
    """Dataclass for singleton configurations"""

    DB_CONFIG = {
        'host': 'localhost',
        'port': 5433,
        'database': os.getenv('POSTGRES_DB'),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD')
    }
    home_bbox = [11.798012, 42.514816, 12.401342, 42.741971]
    italy_bbox = [6.6, 36.6, 18.5, 47.1]
    DEFAULT_BOX = italy_bbox

    QCLIENT = QdrantClient(url="localhost:6333")

    # llms config
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    LLM_CLIENT = None
    MODEL = None

    if OPENAI_API_KEY:
        LLM_CLIENT = AsyncOpenAI(api_key=OPENAI_API_KEY)
        MODEL = OpenAIChatCompletionsModel(
            model="gpt-4o-mini",
            openai_client=LLM_CLIENT
        )
        logger.info(f"OpenAI client initialized and model {MODEL.model} set up.")

    elif ANTHROPIC_API_KEY:
        MODEL = LitellmModel(
            model="claude-3-5-haiku-20241022", 
            api_key=ANTHROPIC_API_KEY
            )
        logger.info(f"Anthropic client initialized and model {MODEL.model} set up.")
        
            
# Singleton
config = Config()