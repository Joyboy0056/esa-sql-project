"""
STAC Loader - Fetch and load ESA Sentinel data into PostgresDB
"""
import requests
import psycopg2
from psycopg2.extras import execute_values
from psycopg2.extensions import connection
from shapely.geometry import shape
from typing import List, Dict, Tuple
from datetime import datetime, timedelta, timezone

from build.config import config
from src.logger import logger


class STACLoader():
    """Load Sentinel data from ESA STAC API into PostgreSQL"""
    
    STAC_API = "https://catalogue.dataspace.copernicus.eu/stac/search"
    
    def __init__(self, db_config: Dict[str, str] = None):
        """
        Initialize loader with database configuration
        
        Args:
            db_config: Dict with keys: host, port, database, user, password
                      If None, reads from environment variables
        """
        if db_config is None:
            self.db_config = config.DB_CONFIG
        else:
            self.db_config = db_config
    
    def fetch_stac_data(
        self, 
        bbox: List[float], 
        datetime_range: str, 
        collection: str = "sentinel-2-l2a",
        limit: int = 500
    ) -> List[Dict]:
        """
        Fetch data from STAC API; main call to API ESA.
        
        Args:
            bbox: [min_lon, min_lat, max_lon, max_lat]
            datetime_range: "2024-01-01/2024-12-31"
            collection: STAC collection name
            limit: Max results per request
            
        Returns:
            List of STAC feature dicts
        """
        logger.info(f"Fetching from STAC API...")
        logger.info(f"  Collection: {collection}")
        logger.info(f"  BBox: {bbox}")
        logger.info(f"  Date range: {datetime_range}")
        
        response = requests.post(
            self.STAC_API,
            json={
                "collections": [collection],
                "bbox": bbox,
                "datetime": datetime_range,
                "limit": limit
            },
            timeout=300
        )
        
        response.raise_for_status()
        data = response.json()
        features = data.get('features', [])
        
        logger.info(f"✓ Fetched {len(features)} scenes")
        return features
    
    def parse_feature(self, feature: Dict) -> Tuple:
        """
        Parse STAC feature into database row tuple; converts json into tuple db.
        
        Args:
            feature: STAC feature dict
            
        Returns:
            Tuple of values matching sentinel_scenes table schema
        """
        props = feature['properties']
        geom = shape(feature['geometry'])
        bbox = feature['bbox']
        
        return (
            # Identificatori
            feature['id'],
            
            # Temporale
            props.get('datetime'),
            props.get('start_datetime'),
            props.get('end_datetime'),
            
            # Piattaforma
            props.get('platform'),
            props.get('constellation'),
            props.get('instruments'),
            
            # Qualità
            props.get('eo:cloud_cover'),
            props.get('eo:snow_cover'),
            
            # Geometria solare
            props.get('view:sun_azimuth'),
            props.get('view:sun_elevation'),
            props.get('view:azimuth'),
            props.get('view:incidence_angle'),
            
            # Orbita
            props.get('sat:absolute_orbit'),
            props.get('sat:relative_orbit'),
            props.get('sat:orbit_state'),
            
            # Prodotto
            props.get('product:type'),
            props.get('processing:level'),
            props.get('processing:version'),
            props.get('product:timeliness'),
            
            # Spaziale
            props.get('grid:code'),
            f'SRID=4326;{geom.wkt}',  # PostGIS geometry
            bbox[0], bbox[1], bbox[2], bbox[3],
            
            # Metadata
            props.get('gsd'),
            props.get('created'),
            props.get('updated')
        )
    
    def insert_scenes(self, features: List[Dict]) -> int:
        """
        Insert features into PostgreSQL; bulk insert PostgreSQL.
        
        Args:
            features: List of STAC feature dicts
            
        Returns:
            Number of rows inserted
        """
        if not features:
            logger.warning("⚠ No features to insert")
            return 0
        
        logger.info(f"Inserting {len(features)} scenes into database...")
        
        conn: connection = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        try:
            # Parse all features
            data = [self.parse_feature(f) for f in features]
            
            # Bulk insert with conflict handling
            execute_values(
                cursor,
                """
                INSERT INTO sentinel_scenes (
                    scene_id, datetime, start_datetime, end_datetime,
                    platform, constellation, instruments,
                    cloud_cover, snow_cover,
                    sun_azimuth, sun_elevation, view_azimuth, incidence_angle,
                    absolute_orbit, relative_orbit, orbit_state,
                    product_type, processing_level, processing_version, timeliness,
                    grid_code, footprint,
                    bbox_minx, bbox_miny, bbox_maxx, bbox_maxy,
                    gsd, created, updated
                ) VALUES %s
                ON CONFLICT (scene_id) DO NOTHING
                """,
                data,
                page_size=100
            )
            
            inserted = cursor.rowcount
            conn.commit()
            logger.info(f"✓ Inserted {inserted} scenes ({len(features) - inserted} duplicates skipped)")
            
            return inserted
            
        except Exception as e:
            conn.rollback()
            logger.error(f"✗ Error inserting data: {e}")
            raise
            
        finally:
            cursor.close()
            conn.close()

    def insert_assets(self, features: List[Dict]) -> int:
        """Insert scene assets (image links) into database"""
        
        conn: connection = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        data = []
        for feature in features:
            scene_id = feature['id']
            assets = feature.get('assets', {})
            
            for asset_key, asset_data in assets.items():
                data.append((
                    scene_id,
                    asset_key,
                    asset_data.get('type'),
                    asset_data.get('href'),
                    asset_data.get('roles'),
                    asset_data.get('eo:bands'),
                    asset_data.get('gsd'),
                    asset_data.get('file:size'),
                    asset_data.get('proj:shape'),
                    asset_data.get('title'),
                    asset_data.get('description')
                ))
        
        execute_values(cursor, """
            INSERT INTO scene_assets (
                scene_id, asset_key, asset_type, href, roles,
                eo_bands, gsd, file_size, proj_shape, title, description
            ) VALUES %s
            ON CONFLICT (scene_id, asset_key) DO NOTHING
        """, data, page_size=500)
        
        inserted = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✓ Inserted {inserted} assets")
        return inserted
    
    def load_region(
        self,
        bbox: List[float],
        datetime_range: str,
        collection: str = "sentinel-2-l2a",
        limit: int = 500
    ) -> int:
        """
        Complete pipeline: fetch from STAC + insert to DB
        
        Args:
            bbox: [min_lon, min_lat, max_lon, max_lat]
            datetime_range: "2024-01-01/2024-12-31"
            collection: STAC collection name
            limit: Max results
            
        Returns:
            Number of scenes inserted
        """
        print("\n" + "="*60)
        print("STAC INGESTION PIPELINE")
        print("="*60 + "\n")
        
        # Fetch
        features = self.fetch_stac_data(bbox, datetime_range, collection, limit)
        
        # Insert
        inserted_scenes = self.insert_scenes(features)
        inserted_assets = self.insert_assets(features)
        
        print("\n" + "="*60)
        print(f"COMPLETED: {inserted_scenes} scenes, {inserted_assets} assets loaded")
        print("="*60 + "\n")
        
        return inserted_scenes, inserted_assets
    
    def print_stats(self):
        """Gets and prints database statistics
        
        Returns:
            Dict with collection stats"""
        try:
            conn: connection = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_scenes,
                    MIN(datetime) as earliest,
                    MAX(datetime) as latest,
                    AVG(cloud_cover) as avg_cloud_cover,
                    COUNT(DISTINCT grid_code) as unique_tiles,
                    COUNT(DISTINCT platform) as platforms
                FROM sentinel_scenes
            """)
            
            row = cursor.fetchone()
            stats = {
                'total_scenes': row[0],
                'earliest': row[1],
                'latest': row[2],
                'avg_cloud_cover': row[3],
                'unique_tiles': row[4],
                'platforms': row[5]
            }

            cursor.execute("""
                SELECT COUNT(asset_id)
                  FROM scene_assets             
            """)
            row = cursor.fetchone()
            stats['total_assets'] = row[0]
            
            print("\n" + "="*60)
            print("DATABASE STATISTICS")
            print("="*60)
            logger.info(f"Total scenes:      {stats['total_scenes']:,}")
            logger.info(f"Total assets:      {stats['total_assets']:,}")
            logger.info(f"Date range:        {stats['earliest']} to {stats['latest']}")
            logger.info(f"Avg cloud cover:   {stats['avg_cloud_cover']:.1f}%" if stats['avg_cloud_cover'] else "N/A")
            logger.info(f"Unique tiles:      {stats['unique_tiles']}")
            logger.info(f"Platforms:         {stats['platforms']}")
            print("="*60 + "\n")

            return stats
        
        finally:
            cursor.close()
            conn.close()

    def update_data(
        self,
        bbox: List[float],
        days_back: int=360,
        collection: str = "sentinel-2-l2a"
    ):
        """Compute last date and load new up to today data"""
        try:
            conn: connection = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT max(datetime) last_date --date_trunc('day', max(datetime))
            FROM public.sentinel_scenes
            """)
            row = cursor.fetchone()
            last_date = row[0]

            if last_date is None:
                # empty table -> fallback: fetch last year data
                start = datetime.now(timezone.utc) - timedelta(days=days_back)
            else:
                # To stay sure: start from +1 second
                start = last_date + timedelta(seconds=1)

            end = datetime.now(timezone.utc)

            datetime_range = f"{start.isoformat()}/{end.isoformat()}"

            return self.load_region(
                bbox=bbox,
                datetime_range=datetime_range,
                collection=collection
            )

        finally:
            cursor.close()
            conn.close()