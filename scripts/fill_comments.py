from psycopg2 import connect
from src.ingestion.refiner import DBRefiner

# Usage: python -m scripts.fill_comments
if __name__=="__main__":
    refiner = DBRefiner()
    try:
        conn = connect()
        refiner.fill_comments(conn)
    finally:
        conn.close()