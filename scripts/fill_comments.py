# Usage: python -m scripts.fill_comments
from psycopg2 import connect
from src.ingestion.refiner import DBRefiner
from build.config import config

if __name__=="__main__":
    refiner = DBRefiner()
    try:
        conn = connect(**config.db_config)
        refiner.fill_comments(conn)
    finally:
        conn.close()