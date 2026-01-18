# 🛰️ Galileo *for* Earth Observation (EO) Databases 🌍

#### `Galileo` is an AI-agent that performs *nl-2-sql* on ESA EO data.
> *Cfr.* [demo-videos](docs/demo_offline.md).
---

## Prerequisites
- A `PostgreSQL` and a `Qdrant` db in `docker`
- A `LLM API key` (OpenAI or Anthropic)

## Quickstart
After git cloning the repo and setup your virtual environment, create a `.env` file within the `build` module, with variables:
```bash
# !./build/.env
POSTGRES_DB="eo_catalog"
POSTGRES_USER=<your_user>
POSTGRES_PASSWORD=<your_password>

PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=admin

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

## Data Ingestion 
This `EO-Agent` certainly needs databases to run.

### PostgreSQL database
Start populate the *sql-database* by running this script (*e.g.*)
```python
python -m scripts.postgres_ingestion --bbox -180 -50 -109 25 --start 1997-07-14 --end 2025-12-26
```
> ***Note:*** choose the geographical coordinates of the bounding box as you prefer.

or this one, if you just want to update data up today
 ```python
 python -m scripts.postgres_ingestion --update
 ```


### RAG vector database
Start create the *vector store* by running 
```python
python -m scripts.qdrant_ingestion --create
```

 In order to extend the *sql knowledge* of the agent, you shall add new queries to the file `queries_example.sql` from the *sql module*, then run from the scripts module:

 ```python
python -m scripts.qdrant_ingestion --update
 ```

 You can also see the available collection with some stats by:
  ```python
python -m scripts.qdrant_ingestion --view
 ```

 ---

 ## Running the agent
 Chat with `Galileo` *locally*, either in a chainlit app or in cli by:
 ```bash
# chainlit ui
python -m chainlit run scripts/ui.py -w

# or cli
python -m scripts.cli
 ```