# 🛰️ Galileo Earth Observation Database Capabilities 🌍

#### `Galileo` is an AI-agent that performs *nl-2-sql* on ESA EO data.

### Some fascinating queries you can explore:

> 1. **Satellite Coverage Analysis**
>   - Find scenes with minimal cloud cover
>   - Track snow coverage across regions
>   - Analyze sun elevation and viewing angles
>   - Compare different satellite platforms

>2. **Geospatial Queries**
 >  - Spatial intersections with city/region boundaries
  > - Calculate area covered by scenes
  > - Find scenes intersecting specific geographic regions
  > - Perform complex geometric operations

> 3. **Temporal Analysis**
  > - Track satellite acquisitions over time
  > - Find scenes within specific date ranges
  > - Compare seasonal changes
  > - Analyze orbit patterns

> 4. **Image Asset Management**
  > - Download thumbnails or full-resolution images
  > - Filter by spectral bands
  > - Find assets by resolution (GSD)
  > - Extract download links

> 5. **Advanced Filtering**
  > - Cloud cover percentage filters
   >- Snow cover analysis
  > - Platform and instrument selection
 >  - Processing level comparisons

## Example Queries

**Basic Spatial:**
1. Find scenes covering Rome
2. Show me the clearest images of Milan from the last 3 months

**Quality & Filtering:**

3. Find scenes with less than 5% cloud cover over Florence
4. Which month had the clearest skies over Rome in 2024?

**Advanced Spatial (PostGIS):**

5. Find scenes along the Tuscan coast with less than 5% clouds
6. All scenes within 50km of the Rome-Florence path
7. Show me the geodesic distance between Rome and Palermo

**Image Downloads:**

8. Give me the download link for the best RGB image of Vesuvius

**Analytics:**

9. Compare cloud cover between Rome and Milan in summer 2025
10. Show cloud cover trends over Rome month by month in 2025

---

## Prerequisites
- A `PostgreSQL` and a `Qdrant` db in `docker`
- A `LLM API key` (OpenAI or Anthropic)

## Quickstart
After git cloning the repo and setup your virtual environment, create a `.env` file with variables:
```bash
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
 Chat with `Galileo` by:
 ```python
 python -m scripts.cli
 ```
 or run the (forthcoming) *chainlit* app:
 ```bash
 python ...
 ```