from pathlib import Path

def load_queries(sql_file: str="sql/queries_example.sql") -> list[dict]:
    """Load queries from a sql file.
    
    Args: 
        sql_file: The path to the sql file where read queries in format
                    --nl description
                    SELECT ...sql query
    Returns:
        List of dicts storing nl questions and sql answers with a unique id.
    """
    content = Path(sql_file).read_text(encoding="utf-8")

    entries = []
    current_nl = None
    current_sql_lines = []

    for line in content.splitlines():
        stripped = line.strip()

        # Nuova NL query
        if stripped.startswith("--"):
            # salva la precedente
            if current_nl and current_sql_lines:
                entries.append({
                    "nl_quest": current_nl,
                    "sql_answ": "\n".join(current_sql_lines).strip()
                })

            current_nl = stripped.lstrip("-").strip()
            current_sql_lines = []

        # Riga SQL
        elif stripped:
            current_sql_lines.append(line)

    # ultimo blocco
    if current_nl and current_sql_lines:
        entries.append({
            "nl_quest": current_nl,
            "sql_answ": "\n".join(current_sql_lines).strip()
        })

    for j, entry in enumerate(entries):
        entry["id"] = j+1

    return entries


def get_queries_dict(sql_file: str="sql/queries_example.sql"):
    return {item["nl_quest"]: item["sql_answ"] for item in load_queries(sql_file)}

# Singleton for `queries_dict`
queries_dict = get_queries_dict()