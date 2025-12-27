## Prerequisites
- A `PostgreSQL` db in `docker`
- A `LLM API key`

## Quickstart
After git cloning the repo and setup your virtual environment, create a `.env` file with variables:
```bash
POSTGRES_DB="eo_catalog"
POSTGRES_USER="<your_user>"
POSTGRES_PASSWORD=<your_password>

PGADMIN_EMAIL="admin@eo.local"
PGADMIN_PASSWORD="admin"

ANTHROPIC_API_KEY="your_anthropic_api_key"
# or
# OPENAI_API_KEY="your_openai_api_key"
```

Then, run the docker-compose instance
```bash
docker-compose up -d
```
and connect to the cointainerized `PostgresDB`.
> I reccomend the official `PostgreSQL` and `Docker` extensions by Microsoft.

### Finally:
#### If you still have to populate the database, run this script (*e.g.*)
```python
python -m scripts.create_postgres --bbox -180 -50 -109 25 --start 1997-07-14 --end 2025-12-26
```
 #### or this one ,if you just want to update data up today
 ```python
 python -m scripts.create_postgres --update
 ```

 ---

 ## PostgreSQL Agent
 Chat with the agent by:
 ```python
 python -m cli.py
 ```