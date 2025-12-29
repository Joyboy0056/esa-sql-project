from typing import Literal
from pydantic import BaseModel, Field
from agents import function_tool
from pandas import DataFrame, read_sql_query
from psycopg2.extensions import connection
from psycopg2 import connect

from build.config import config
from sql.utils.metadata_general_query import get_metadata_query
from sql.utils.load_nl_sql_pairs import queries_dict

# Tool `executeQuery`
class ExecQueryParams(BaseModel):
    query: str=Field(
        default=None,
        description="La query da eseguire"
    )
    mode: Literal['conn', 'cursor']=Field(
        default="cursor",
        description="Parametro per eseguire la query o via cursor o via connection in Pandas"
    )

@function_tool
def executeQuery(params: ExecQueryParams) -> DataFrame:
    """Tool function for directly execute a query on PostgresDB"""
    try:
        conn: connection = connect(**config.db_config)
        cursor = conn.cursor()
        if params.mode == "cursor":
            cursor.execute(params.query)
            data = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            df = DataFrame(data=data, columns=columns)
            return df.to_string()

        elif params.mode == "conn":
            df = read_sql_query(sql=params.query, con=conn)
            return df.to_string()
        else:
            return params.mode
    finally:
        cursor.close()
        conn.close()

executeQuery.name = ("executeQuery")
executeQuery.description = "Funzione per eseguire una query PostgreSQL su db"


# Tool `getMetadata`
def get_tables(*, schema: str='public') -> list[str]:
    """Aux function to get all the tables in the schema"""
    conn, cursor = None, None
    try:
        conn: connection = connect(**config.DB_CONFIG)
        cursor = conn.cursor()

        # query to get all the tables
        query = f"""
                SELECT tablename FROM pg_catalog.pg_tables
                WHERE schemaname = '{schema}'
                """
        cursor.execute(query)
        tables = cursor.fetchall() # on the form [('country',), ('city',), ...] here
        return [table[0] for table in tables]
    
    finally:
        if conn is not None and cursor is not None:
            conn.close()
            cursor.close()


# Tool getMetadata
class FillTablesMetadata(BaseModel):
    retrieved_tables: list[str]=Field(
        default=None,
        description=f"""
            Sei un retriever semantico specializzato in query NL-to-SQL

            KNOWLEDGE BASE
            {get_tables()}

            TASK: Identifica le chiavi più semanticamente simili alla richiesta dell'utente

            RULES:
            - Restituisci SOLO le chiavi esatte (nessun testo aggiuntivo)
            - Prioritizza intent match su keyword match

            OUTPUT FORMAT:
            key1
            key2
            ...
        """
    )

@function_tool
def getMetadata(params: FillTablesMetadata) -> DataFrame:
    metadata_res = ""
    try:
        conn: connection = connect(**config.db_config)
        cursor = conn.cursor()
        
        for table_name in params.retrieved_tables:
            metadata_res += f"\n--- Tabella: {table_name} ---\n"
            
            query = get_metadata_query(table_name)
            
            cursor.execute(query)
            data = cursor.fetchall()
            columns = [col[0] for col in cursor.description]

            df = DataFrame(data=data, columns=columns)
            metadata_res += df.to_string() + "\n"

        return metadata_res
            
    finally:
        cursor.close()
        conn.close()

getMetadata.name = "getMetadata"
getMetadata.description = "Funzione per estrarre i metadati (campi, tipi, commenti) di una lista di tabelle"


# Tool `retrieveQueries``
class SQLQueriesParam(BaseModel):
    retrieved_nl: list[str]=Field(
        default=None,
        description="""
            Sei un retriever semantico specializzato in query NL-to-SQL

            KNOWLEDGE BASE
            {keys_list}

            TASK: Identifica le chiavi più semanticamente simili alla richiesta dell'utente

            RULES:
            - Restituisci SOLO le chiavi esatte (nessun testo aggiuntivo)
            - Prioritizza intent match su keyword match
        """.format(keys_list=list(queries_dict.keys()))
    )
    score: list[float]=Field(
        default=None,
        description=f"""
            Sei un retriever semantico specializzato in query NL-to-SQL

            KNOWLEDGE BASE
            {retrieved_nl}

            TASK: Associa uno score di similarità compreso tra 0 e 1 tra le chiavi retrievate e la richiesta dell'utente

            RULES:
            - Restituisci SOLO le chiavi esatte (nessun testo aggiuntivo)
            - Prioritizza intent match su keyword match
        """
    )

@function_tool
def retrieveQueries(param: SQLQueriesParam):
    res = "\n".join(
        f"\nNL key: {rkey}\nSQL value: {queries_dict[rkey]}\nScore: {param.score[j]:.4f}" 
        for j, rkey in enumerate(param.retrieved_nl)
    )
    return res

retrieveQueries.name = "retrieveQueries"
retrieveQueries.description = "Funzione per retrievare delle query SQLite utili simili alla richiesta NL dell'utente"
