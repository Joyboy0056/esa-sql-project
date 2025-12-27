def get_metadata_query(table: str, *, schema: str='public'):
    return f"""
        SELECT
            c.column_name,
            c.data_type,
            -- TRUE se PRIMARY KEY reale
            (pk.column_name IS NOT NULL) AS primary_key,
            -- Commento colonna
            pgd.description
        FROM information_schema.columns c
        -- PRIMARY KEY
        LEFT JOIN (
            SELECT
                kcu.table_schema,
                kcu.table_name,
                kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
        ) pk
        ON pk.table_schema = c.table_schema
        AND pk.table_name   = c.table_name
        AND pk.column_name  = c.column_name
        -- COLUMN COMMENTS
        LEFT JOIN pg_catalog.pg_statio_all_tables st
        ON st.schemaname = c.table_schema
        AND st.relname   = c.table_name
        LEFT JOIN pg_catalog.pg_description pgd
        ON pgd.objoid   = st.relid
        AND pgd.objsubid = c.ordinal_position
        WHERE c.table_schema = '{schema}'
        AND c.table_name   = '{table}'
        ORDER BY c.ordinal_position
        ;
    """